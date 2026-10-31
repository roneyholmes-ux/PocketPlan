import base64
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class ImportTests(unittest.TestCase):
    def test_currency_and_csv(self):
        self.assertEqual(app.money('R$ 1.234,56'), 123456)
        self.assertEqual(app.money('-20,00'), -2000)
        with self.assertRaises(ValueError):
            app.money('NaN')
        rows = app.parse_file('f.csv', b'Data;Descricao;Valor\n01/10/2026;Cinema;48,00\n')
        self.assertEqual(rows[0]['date'], '2026-10-01')
        self.assertEqual(app.classify(rows)[0]['category'], 'Lazer')

    def test_invalid_row_is_not_silently_discarded(self):
        with self.assertRaisesRegex(ValueError, 'Linha 3'):
            app.parse_file('f.csv', b'Data;Descricao;Valor\n01/10/2026;Cinema;48,00\nxxx;Mercado;10,00')

    def test_pdf_extraction_and_encryption(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer = PdfWriter()
        page = writer.add_blank_page(width=600, height=800)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        content = DecodedStreamObject()
        content.set_data(b'BT /F1 12 Tf 50 700 Td (01/10/2026 Supermercado 245,90) Tj 0 -20 Td (02/10/2026 Cinema 48,00) Tj ET')
        page[NameObject('/Contents')] = writer._add_object(content)
        out = io.BytesIO(); writer.write(out)
        rows = app.parse_file('f.pdf', out.getvalue())
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r['cents'] for r in rows), 29390)
        writer.encrypt('senha'); out = io.BytesIO(); writer.write(out)
        with self.assertRaisesRegex(ValueError, 'protegido'):
            app.parse_file('f.pdf', out.getvalue())
        with self.assertRaisesRegex(ValueError, 'incorreta'):
            app.parse_file('f.pdf', out.getvalue(), 'errada')
        self.assertEqual(len(app.parse_file('f.pdf', out.getvalue(), 'senha')), 2)

    def test_inter_current_expenses_reconcile_and_exclude_payments(self):
        # Synthetic data only. Never commit a real statement or its password.
        text = '''bancointer.com.br
Total da sua fatura
R$ 120,00
Despesas da fatura
CARTÃO 1234****5678
30 de dez. 2025 LOJA TESTE (Parcela 02 de 03) - R$ 100,00
02 de jan. 2026 PAGAMENTO ON LINE - + R$ 900,00
03 de jan. 2026 ESTORNO TESTE - + R$ 10,00
Total CARTÃO 1234****5678 R$ 90,00
CARTÃO 1234****9999
04 de jan. 2026 MERCADO TESTE - R$ 30,00
Total CARTÃO 1234****9999 R$ 30,00
Próxima fatura
LOJA TESTE (Parcela 03 de 03) R$ 100,00'''
        rows = app.parse_inter_text(text)
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum(r['cents'] for r in rows), 12000)
        self.assertEqual(rows[0]['date'], '2025-12-30')
        self.assertEqual(rows[1]['cents'], -1000)
        with self.assertRaisesRegex(ValueError, 'totais dos cartões'):
            app.parse_inter_text(text.replace('R$ 100,00\n02', 'R$ 99,00\n02'))
        with self.assertRaisesRegex(ValueError, 'difere do total'):
            app.parse_inter_text(text.replace('R$ 120,00', 'R$ 121,00'))
        with self.assertRaisesRegex(ValueError, 'não foi reconhecida'):
            app.parse_inter_text(text.replace('R$ 30,00\nTotal', 'USD 30,00\nTotal'))

    def test_xlsx(self):
        from openpyxl import Workbook
        book = Workbook(); sheet = book.active
        sheet.append(['Data', 'Descrição', 'Valor']); sheet.append(['01/10/2026', 'Mercado', 12.34])
        out = io.BytesIO(); book.save(out)
        self.assertEqual(app.parse_file('f.xlsx', out.getvalue())[0]['cents'], 1234)

    def test_ai_response_is_validated(self):
        result = {'output': [{'content': [{'type': 'output_text', 'text': '{"categories":["Mercado"]}'}]}]}
        with patch.dict(app.os.environ, {'OPENAI_API_KEY': 'test'}), patch('app.urllib.request.urlopen', return_value=io.BytesIO(json.dumps(result).encode())):
            rows = app.classify([{'description': 'Loja'}], True)
            self.assertEqual(rows[0]['category'], 'Mercado')
            self.assertEqual(rows[0]['source'], 'IA')

class ApiTests(unittest.TestCase):
    def test_preview_confirm_duplicate_bulk_and_persistence(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, 'DB', Path(tmp)/'db.sqlite3'):
            server = app.HTTPServer(('127.0.0.1', 0), app.Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            base = f'http://127.0.0.1:{server.server_port}/api/'
            def call(route, data=None):
                req = Request(base+route, data=json.dumps(data).encode() if data else None, headers={'Content-Type': 'application/json'})
                with urlopen(req) as response:
                    return json.load(response)
            try:
                raw = b'Data;Descricao;Valor\n01/10/2026;Cinema;48,00\n02/10/2026;Mercado;20,00'
                preview = call('preview', {'name': 'f.csv', 'content': base64.b64encode(raw).decode()})
                self.assertEqual(call('expenses')['rows'], [])
                call('import', preview)
                rows = call('expenses')['rows']; self.assertEqual(len(rows), 2)
                call('category', {'ids': [r['id'] for r in rows], 'category': 'Casa'})
                self.assertTrue(all(r['category']=='Casa' and r['source']=='Manual' for r in call('expenses')['rows']))
                with self.assertRaises(HTTPError) as error:
                    call('import', preview)
                self.assertEqual(error.exception.code, 409)
                error.exception.close()
                self.assertEqual(len(call('expenses')['rows']), 2)
            finally:
                server.shutdown(); server.server_close(); thread.join()

if __name__ == '__main__':
    unittest.main()
