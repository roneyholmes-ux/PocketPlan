# PocketPlan

Um app simples para acompanhar as despesas da casa. Importe sua fatura, confira os lançamentos e ajuste as categorias com um clique ou em lote.

## Começar no Windows

O endereço `http://127.0.0.1:8000` é local: ele só funciona neste computador enquanto o PocketPlan está em execução. A página do GitHub guarda o código e não inicia o aplicativo.

Para abrir com dois cliques, instale Python 3.11 ou superior, baixe e extraia o projeto em uma pasta e abra **Iniciar PocketPlan.cmd**. No primeiro uso é preciso conexão com a internet para instalar as bibliotecas. O navegador abrirá automaticamente. Mantenha a janela do PocketPlan aberta enquanto usar; para encerrar, pressione Ctrl+C nessa janela. Nas próximas vezes, abra o mesmo arquivo novamente.

Se preferir iniciar pelo terminal:

Instale Python 3.11 ou superior. Na pasta do projeto, abra o terminal e execute:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Abra **http://127.0.0.1:8000** no navegador. Para encerrar, pressione Ctrl+C no terminal. Nas próximas vezes basta executar o último comando. Nenhuma conta é necessária.

## Como usar

1. Clique em **Importar fatura** e escolha PDF, CSV, Excel ou uma imagem PNG/JPG/WebP.
2. Se o PDF for protegido, informe a senha no campo indicado. Ela é usada somente para leitura, não é salva e não é enviada à IA. Clique em **Ler e categorizar**. Confira a quantidade, o total e as compras encontradas com sua fatura original.
3. Confira as datas, descrições, valores e categorias. É possível corrigir os campos, remover linhas ou adicionar lançamentos antes de confirmar. O mês é buscado no conteúdo do arquivo; se não estiver explícito ou houver conflito, ficará como **Sem mês definido**, sem impedir o salvamento. Você pode preencher ou corrigir no formato **10/2026**.
4. Clique na categoria de uma despesa para alterá-la. Para várias despesas, marque as caixas, escolha a categoria na barra que aparece e clique em **Aplicar à seleção**.
5. Escolha a fatura na lista lateral, por exemplo **10/2026**. A lista é única, em ordem da mais recente para a mais antiga, sem agrupamentos por ano. Combine busca, categoria, data inicial/final e valor mínimo/máximo. Os limites são inclusivos. Ordene por data, valor ou estabelecimento. O botão **Limpar filtros** restaura os filtros da fatura selecionada. Gráfico, resumos, seleção em lote e exportação CSV usam somente os resultados filtrados.
6. Confira o gráfico de pizza e os resumos à direita da tabela. O gráfico mostra as compras positivas por categoria, com valores e percentuais; estornos ficam separados e são descontados dos totais. Todos acompanham os filtros e as alterações de categoria.

Categorias: **Lazer, Mercado, Despesa Médica e Casa**. **A revisar** é uma indicação de dúvida, para não forçar uma classificação incorreta. Créditos e estornos aparecem negativos e reduzem o total. O mesmo arquivo não pode ser importado novamente; arquivos diferentes que contenham as mesmas compras exigem conferência para evitar duplicação.

## Mês da fatura

O mês não é deduzido pelas datas das compras, pelo nome do arquivo nem pela data atual. O leitor busca referências explícitas como `Fatura: 10/2026`, `Referência: outubro de 2026` ou uma data de vencimento. CSV/Excel podem ter uma linha de referência antes do cabeçalho da tabela. Sem indicação clara, o app mantém **Sem mês definido**.

Para alterar depois da importação, abra **Editar mês de uma fatura**, escolha o arquivo, digite **10/2026** e clique em **Salvar mês**. A alteração vale apenas para a fatura escolhida. Deixe o campo vazio para remover o mês. As datas originais das compras e as categorias são preservadas.

## IA opcional

Sem configuração, o app usa palavras-chave locais. Isso não é IA. Para usar a categorização com IA, configure uma chave da API OpenAI no terminal antes de iniciar:

```powershell
$env:OPENAI_API_KEY = "sua-chave"
$env:OPENAI_MODEL = "gpt-4.1-mini"
.venv\Scripts\python app.py
```

Depois marque **Categorizar com IA** na importação. A API exige chave com acesso ao modelo e créditos próprios. Somente as descrições das compras são enviadas à OpenAI, em lotes de até 60, com `store: false`. O PDF, a imagem, os valores e as datas não são enviados. O reconhecimento do texto das imagens acontece localmente. A chave fica no servidor e não é entregue ao navegador. Não a salve no repositório. Se a API falhar, o app informa o problema e permite tentar novamente com regras locais. A integração segue a [documentação oficial de saídas estruturadas](https://developers.openai.com/api/docs/guides/structured-outputs).

## Formatos e limitações da primeira versão

- **PDF:** texto selecionável, com ou sem senha, até 80 páginas. O layout Inter com datas por extenso é suportado: reúne os cartões da fatura, mantém a descrição da parcela, exclui pagamentos e não importa a seção de parcelas futuras. Créditos são negativos. O leitor confere os subtotais de cada cartão e o total da fatura, interrompendo a importação se houver divergência. Faturas com antecipações, saldo anterior ou encargos que impeçam essa conferência ainda precisam de adaptação. As datas exibidas são as datas originais das compras. A navegação mensal usa o mês da fatura (mês do vencimento), preservando as parcelas antigas na fatura a que pertencem. O PDF Inter preenche esse mês automaticamente; confirme-o antes de salvar. Para arquivos sem mês explícito, a informação é opcional e pode ser alterada depois, individualmente em **Editar mês de uma fatura**. Para outros bancos, o leitor genérico reconhece linhas com `dd/mm/aaaa descrição 1.234,56` ou `dd/mm/aa descrição 1.234,56`. PDFs de bancos com datas sem ano, descrições quebradas entre linhas ou outras disposições precisam de adaptação. PDFs digitalizados ainda não são lidos diretamente: envie as páginas como imagens. Confira sempre o total, pois linhas não reconhecidas podem faltar. A [documentação do pypdf](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) explica essas limitações de extração.
- **Imagens (PNG/JPG/WebP):** leitura local com RapidOCR, até 25 megapixels e 10 MB. Use uma imagem por importação, nítida, de frente e com as linhas completas. O leitor reconhece datas numéricas ou por extenso, descrição e valor em reais na mesma linha. Datas sem ano ficam vazias para preenchimento manual na conferência, sem inventar o ano. Fotos inclinadas, baixa resolução ou tabelas complexas podem exigir correções; confira linhas faltando e o total. A imagem não é enviada a um serviço de OCR. O leitor segue a [documentação do RapidOCR](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/usage/).
- **CSV:** cabeçalhos Data, Descrição e Valor; vírgula, ponto e vírgula ou tabulação como separador. UTF-8 e Windows-1252. Veja `exemplo.csv`.
- **Excel (.xlsx):** primeira aba, os mesmos cabeçalhos.
- Até 10 MB e 2.000 lançamentos por arquivo. Valores em reais; compras parceladas são importadas como aparecem no arquivo.
- O app é local e individual. Ainda não há contas, sincronização nem exclusão dos lançamentos já salvos pela interface. Datas, descrições e valores podem ser corrigidos durante a conferência, antes de salvar. Não exponha este servidor diretamente na internet.

## Dados e desenvolvimento

Os lançamentos ficam em `data/orcamento.sqlite3`. Para backup, encerre o app e copie a pasta `data`. Os arquivos originais são processados em memória e não são guardados pelo app. `data`, PDFs, planilhas, chaves e ambientes locais estão ignorados pelo Git. Os exemplos são fictícios.

Servidor Python com biblioteca padrão, SQLite, interface HTML/CSS/JavaScript e pypdf/openpyxl/RapidOCR para leitura. Não há etapa de compilação.

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
node --test tests/filters.test.js
```

Os testes cobrem valores brasileiros, estornos, PDF sintético, PDF com senha correta/incorreta, layout Inter sintético com vários cartões e conferência dos totais, Excel, validação de classificação, conferência antes de salvar, persistência, duplicação e mudança de categoria em lote. Também há testes de OCR com imagem fictícia, detecção de mês explícito, salvamento sem mês, alteração posterior por fatura e filtros combinados por data/valor com ordenação. Os testes JavaScript precisam de Node.js; o uso do aplicativo não precisa. A chamada real à IA requer credenciais e não faz parte dos testes automatizados.
