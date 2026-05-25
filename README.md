# Relatório de Exploração da Fonte — Etapa 1
## Diário Oficial Inteligente de Avaré

---

## 1. Identificação do Grupo

| Campo | Informação |
|---|---|
| Integrante 1 | *Lucas Nakamura Rodrigues* |
| Integrante 2 | *Gabriel Santana dps Santos* |
| Repositório GitHub | *https://github.com/santanafeap/RN-e-IA/* |

---

## 2. Fonte de Dados

**Portal:** Imprensa Oficial Municipal  
**URL base:** `https://imprensaoficialmunicipal.com.br`  
**URL da listagem:** `https://imprensaoficialmunicipal.com.br/listaatos.php?c=Avaré&s=Decretos`

O portal **Imprensa Oficial Municipal** centraliza publicações de dezenas de municípios paulistas. Para Avaré, disponibiliza principalmente Decretos, mas também há Portarias, Editais e Atas acessíveis via parâmetros na URL (`&s=`).

---

## 3. Exploração Manual da Estrutura do Site

### 3.1 Página de Listagem

A URL de listagem retorna uma página HTML com uma lista (`<ul>`) de edições. Cada item possui a estrutura:

```html
<li class="lista">
  <h3>Decreto nº 9.146, de 15 de maio de 2026</h3>
  <a href="exibe_do.php?i=NTM2NjQz">Visualizar</a>
</li>
```

**Campos extraíveis da listagem:**

| Campo | Localização no HTML | XPath / CSS |
|---|---|---|
| Título | `<h3>` dentro do `<li class="lista">` | `li.lista h3` |
| Link da edição | atributo `href` do `<a>` com `exibe_do.php?i=` | `a[href*="exibe_do.php"]` |

### 3.2 Página de Cada Edição

O link `exibe_do.php?i=<id>` pode retornar:

- **Documento HTML** com o conteúdo textual da publicação; ou  
- **PDF inline** (`Content-Type: application/pdf`), especialmente para edições mais recentes.

**Identificação do formato:**  
Verificamos o cabeçalho HTTP `Content-Type` da resposta antes de processar o conteúdo.

### 3.3 Paginação

A página de listagem não utiliza paginação explícita via parâmetros na URL — todos os registros são carregados em uma única requisição HTML. O controle de quantidade é feito no próprio script (variável `MAX_REGISTROS`).

---

## 4. Comparação de Ferramentas

| Critério | `requests` + `BeautifulSoup` | `Scrapy` | `Selenium` / `Playwright` |
|---|---|---|---|
| **Complexidade de configuração** | Baixa | Média | Alta |
| **Suporte a JavaScript** | Não | Não (nativo) | Sim |
| **Velocidade** | Alta | Alta (assíncrono) | Baixa |
| **Tratamento de PDFs** | Manual (PyMuPDF) | Manual (PyMuPDF) | Inviável |
| **Ideal para** | Scripts simples, ensino | Projetos de scraping em escala | Sites com JS pesado |
| **Escolha para esta etapa** | ✅ **Sim** | (Semanas seguintes) | Não necessário |

**Justificativa da escolha:**  
O portal não renderiza conteúdo via JavaScript; a listagem e os documentos são servidos como HTML ou PDF estático. Portanto, `requests` + `BeautifulSoup` é suficiente, mais simples de depurar e mais adequado pedagogicamente para a Semana 1.

---

## 5. Desafios Encontrados

### 5.1 Bloqueio por User-Agent
O servidor retorna HTTP 403 para requisições com `User-Agent` padrão do Python (`python-requests/...`). 

**Solução:** Usar um `User-Agent` de navegador real e uma `Session` que visite a home antes da listagem, acumulando cookies.

```python
sessao = requests.Session()
sessao.headers.update({"User-Agent": "Mozilla/5.0 ..."})
sessao.get("https://imprensaoficialmunicipal.com.br/")  # coleta cookies
```

### 5.2 Conteúdo em PDF
Parte das edições é servida como PDF binário, não como HTML.

**Solução:** Detectar via `Content-Type` e usar **PyMuPDF** (`fitz`) para extrair o texto:

```python
if "pdf" in content_type:
    doc = fitz.open(stream=response.content, filetype="pdf")
    texto = "\n".join(p.get_text() for p in doc)
```

### 5.3 Extração de Data
As datas aparecem no corpo do documento em formatos variados (`DD/MM/AAAA` ou `DD de mês de AAAA`).

**Solução:** Regex com duas alternativas:

```python
re.search(
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})\b"
    r"|\b(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})\b",
    texto, re.IGNORECASE
)
```

---

## 6. Campos Coletados no CSV

| Coluna | Descrição | Exemplo |
|---|---|---|
| `titulo` | Título da edição (extraído do `<h3>`) | `Decreto nº 9.146, de 15 de maio de 2026` |
| `data` | Data encontrada no conteúdo | `15/05/2026` |
| `link` | URL completa da edição | `https://imprensaoficialmunicipal...` |
| `trecho` | Primeiros 400 caracteres do conteúdo | `Regulamenta o uso de veículos...` |
| `status` | Resultado da requisição | `ok` / `erro: ...` |

---

## 7. Resultados

- **Total de publicações coletadas:** 20
- **Período coberto:** 08/04/2026 a 15/05/2026
- **Tipos de documento:** Decretos municipais (listagem padrão)
- **Arquivo gerado:** `diario_avare.csv`

---

## 8. Repositório TCU — Comparação com Referência

O repositório de referência (Acórdãos TCU) aplica scraping em um portal federal com estrutura de paginação explícita e documentos exclusivamente em PDF. As principais diferenças em relação ao Diário de Avaré são:

| Aspecto | Acórdãos TCU | Diário Oficial de Avaré |
|---|---|---|
| Formato dos documentos | Apenas PDF | HTML ou PDF |
| Paginação | Parâmetros na URL | Lista única |
| Volume de registros | Milhares | Dezenas por mês |
| Autenticação | Não requer | Não requer |
| Complexidade do HTML | Moderada | Simples |

A lógica de detecção de `Content-Type` e extração com PyMuPDF foi adaptada diretamente da abordagem do repositório de referência.

---

## 9. Próximos Passos (Semanas 2–4)

- **Semana 2:** Pré-processamento NLP — tokenização, remoção de stopwords, normalização do texto extraído
- **Semana 3:** Classificação automática das publicações por categoria (licitação, decreto, nomeação…) com modelos de ML
- **Semana 4:** Interface web para consulta e visualização dos dados classificados

---

*Relatório elaborado para a disciplina de NLP e Redes Neurais — Semana 1.*
