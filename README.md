# PocketPlan

Um app simples para acompanhar as despesas da casa. Importe sua fatura, confira os lançamentos e ajuste as categorias com um clique ou em lote.

## Começar no Windows

Instale Python 3.11 ou superior. Na pasta do projeto, abra o terminal e execute:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Abra **http://127.0.0.1:8000** no navegador. Para encerrar, pressione Ctrl+C no terminal. Nas próximas vezes basta executar o último comando. Nenhuma conta é necessária.

## Como usar

1. Clique em **Importar fatura** e escolha seu PDF.
2. Se o PDF for protegido, informe a senha no campo indicado. Ela é usada somente para leitura, não é salva e não é enviada à IA. Clique em **Ler e categorizar**. Confira a quantidade, o total e as compras encontradas com sua fatura original.
3. Ajuste as categorias e confirme a importação.
4. Clique na categoria de uma despesa para alterá-la. Para várias despesas, marque as caixas, escolha a categoria na barra que aparece e clique em **Aplicar à seleção**.
5. Use a busca, os filtros de mês/categoria e a exportação CSV quando precisar.

Categorias: **Lazer, Mercado, Despesa Médica e Casa**. **A revisar** é uma indicação de dúvida, para não forçar uma classificação incorreta. Créditos e estornos aparecem negativos e reduzem o total. O mesmo arquivo não pode ser importado novamente; arquivos diferentes que contenham as mesmas compras exigem conferência para evitar duplicação.

## IA opcional

Sem configuração, o app usa palavras-chave locais. Isso não é IA. Para usar a categorização com IA, configure uma chave da API OpenAI no terminal antes de iniciar:

```powershell
$env:OPENAI_API_KEY = "sua-chave"
$env:OPENAI_MODEL = "gpt-4.1-mini"
.venv\Scripts\python app.py
```

Depois marque **Categorizar com IA** na importação. A API exige chave com acesso ao modelo e créditos próprios. Somente as descrições das compras são enviadas à OpenAI, em lotes de até 60, com `store: false`. O PDF, valores e datas não são enviados. A chave fica no servidor e não é entregue ao navegador. Não a salve no repositório. Se a API falhar, o app informa o problema e permite tentar novamente com regras locais. A integração segue a [documentação oficial de saídas estruturadas](https://developers.openai.com/api/docs/guides/structured-outputs).

## Formatos e limitações da primeira versão

- **PDF:** texto selecionável, com ou sem senha, até 80 páginas. O layout Inter com datas por extenso é suportado: reúne os cartões da fatura, mantém a descrição da parcela, exclui pagamentos e não importa a seção de parcelas futuras. Créditos são negativos. O leitor confere os subtotais de cada cartão e o total da fatura, interrompendo a importação se houver divergência. Faturas com antecipações, saldo anterior ou encargos que impeçam essa conferência ainda precisam de adaptação. As datas exibidas são as datas originais das compras; o filtro de mês também usa essas datas, inclusive para parcelas. Para outros bancos, o leitor genérico reconhece linhas com `dd/mm/aaaa descrição 1.234,56` ou `dd/mm/aa descrição 1.234,56`. PDFs de bancos com datas sem ano, descrições quebradas entre linhas ou outras disposições precisam de adaptação. Não há OCR. Confira sempre o total, pois linhas não reconhecidas podem faltar. A [documentação do pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) explica essas limitações de extração.
- **CSV:** cabeçalhos Data, Descrição e Valor; vírgula, ponto e vírgula ou tabulação como separador. UTF-8 e Windows-1252. Veja `exemplo.csv`.
- **Excel (.xlsx):** primeira aba, os mesmos cabeçalhos.
- Até 10 MB e 2.000 lançamentos por arquivo. Valores em reais; compras parceladas são importadas como aparecem no arquivo.
- O app é local e individual. Ainda não há contas, sincronização, edição de datas/valores nem exclusão pela interface. Não exponha este servidor diretamente na internet.

## Dados e desenvolvimento

Os lançamentos ficam em `data/orcamento.sqlite3`. Para backup, encerre o app e copie a pasta `data`. Os arquivos originais são processados em memória e não são guardados pelo app. `data`, PDFs, planilhas, chaves e ambientes locais estão ignorados pelo Git. Os exemplos são fictícios.

Servidor Python com biblioteca padrão, SQLite, interface HTML/CSS/JavaScript e pypdf/openpyxl para leitura. Não há etapa de compilação.

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Os testes cobrem valores brasileiros, estornos, PDF sintético, PDF com senha correta/incorreta, layout Inter sintético com vários cartões e conferência dos totais, Excel, validação de classificação, conferência antes de salvar, persistência, duplicação e mudança de categoria em lote. A chamada real à IA requer credenciais e não faz parte dos testes automatizados.
