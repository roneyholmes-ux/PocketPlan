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

    def test_statement_month_detection(self):
        self.assertEqual(app.detect_statement_month('Fatura: 10/2026'), '2026-10')
        self.assertEqual(app.detect_statement_month('Referência: outubro de 2026'), '2026-10')
        self.assertEqual(app.detect_statement_month('Data de Vencimento\n07/10/2026'), '2026-10')
        self.assertIsNone(app.detect_statement_month('01/10/2026 Supermercado 50,00'))
        self.assertIsNone(app.detect_statement_month('Fatura: 10/2026 Fatura: 11/2026'))
        self.assertIsNone(app.valid_month('', allow_empty=True))
        self.assertEqual(app.valid_month('10/2026'), '2026-10')
        with self.assertRaises(ValueError): app.valid_month('13/2026')
        meta = {}
        app.parse_file('f.csv', b'Fatura;10/2026\nData;Descricao;Valor\n01/09/2026;Mercado;50,00', metadata=meta)
        self.assertEqual(meta['statement_month'], '2026-10')

    def test_image_rows_and_partial_dates(self):
        rows = app.parse_image_text('01/10/2026 Mercado R$ 100,00\n02/10/2026 Estorno - + R$ 10,00\n03/10/2026 PAGAMENTO ON LINE - + R$ 500,00\n04/10 Cinema R$ 50,00')
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1]['cents'], -1000)
        self.assertEqual(rows[2]['date'], '')

    def test_image_ocr_end_to_end(self):
        from PIL import Image, ImageDraw, ImageFont
        font_path = Path('C:/Windows/Fonts/arial.ttf')
        if not font_path.exists():
            self.skipTest('Fonte de teste disponível no Windows')
        image = Image.new('RGB', (1400, 400), 'white')
        draw = ImageDraw.Draw(image); font = ImageFont.truetype(str(font_path), 36)
        for i, text in enumerate(['Fatura: 10/2026', '01/10/2026 Mercado Teste R$ 123,45', '02/10/2026 Cinema R$ 50,00']):
            draw.text((40, 40+i*100), text, fill='black', font=font)
        raw = io.BytesIO(); image.save(raw, format='PNG')
        metadata = {}
        rows = app.parse_file('teste.png', raw.getvalue(), metadata=metadata)
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r['cents'] for r in rows), 17345)
        self.assertEqual(metadata['statement_month'], '2026-10')
        self.assertIn('Imagem', metadata['warning'])

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
    def test_old_database_migration(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(app, 'DB', Path(tmp)/'old.sqlite3'):
            con = app.sqlite3.connect(app.DB)
            con.execute('CREATE TABLE imports (hash TEXT PRIMARY KEY)')
            con.execute('INSERT INTO imports VALUES (?)', ('a'*64,))
            con.commit(); con.close()
            with app.connect() as con:
                self.assertIsNone(con.execute('SELECT statement_month FROM imports').fetchone()[0])
            with app.connect() as con:
                self.assertEqual(con.execute('SELECT COUNT(*) FROM imports').fetchone()[0], 1)

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
                preview['statement_month'] = None
                call('import', preview)
                rows = call('expenses')['rows']; self.assertEqual(len(rows), 2)
                self.assertTrue(all(r['statement_month'] is None and r['date'].startswith('2026-10') for r in rows))
                call('statement-month', {'hashes': [preview['hash']], 'statement_month': '2026-12'})
                self.assertTrue(all(r['statement_month']=='2026-12' for r in call('expenses')['rows']))
                call('statement-month', {'hashes': [preview['hash']], 'statement_month': ''})
                self.assertTrue(all(r['statement_month'] is None for r in call('expenses')['rows']))
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
