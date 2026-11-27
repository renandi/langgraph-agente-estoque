# API de Estoque — Projeto Avaliativo de Agentes de IA

API REST **simulada** de controle de estoque, desenvolvida com **FastAPI** para ser a fonte de dados do projeto avaliativo **Analisador Inteligente de Estoque**.

## Sumário

1. [Apresentação](#1-apresentação)
2. [Requisitos](#2-requisitos)
3. [Instalação e configuração](#3-instalação-e-configuração)
4. [Execução](#4-execução)
5. [Swagger (documentação interativa)](#5-swagger-documentação-interativa)
6. [Endpoints](#6-endpoints)
7. [Dados disponíveis](#7-dados-disponíveis)
8. [Cadastro de produtos](#8-cadastro-de-produtos)
9. [Exemplos de utilização](#9-exemplos-de-utilização)
10. [Integração com Python e agentes de IA](#10-integração-com-python-e-agentes-de-ia)
11. [Integração com n8n](#11-integração-com-n8n)
12. [Testes da API](#12-testes-da-api)
13. [Restauração dos dados](#13-restauração-dos-dados)
14. [Resolução de problemas](#14-resolução-de-problemas)
15. [Segurança e limitações](#15-segurança-e-limitações)
16. [Organização do projeto](#16-organização-do-projeto)
17. [Orientações finais aos estudantes](#17-orientações-finais-aos-estudantes)

---

## 1. Apresentação

Esta API permite **consultar** produtos de uma loja fictícia, **verificar as quantidades disponíveis** e **cadastrar novos produtos**. Ela é a base de dados sobre a qual você construirá, no projeto avaliativo, um agente de IA capaz de interpretar pedidos sobre o estoque, consultar a API por meio de ferramentas e apresentar análises fundamentadas nos dados obtidos.

Pontos importantes:

- **O agente de IA não faz parte deste repositório.** Não há LangGraph, prompts, ferramentas (*tools*) de agente nem workflows do n8n aqui. Tudo isso é a atividade avaliativa que **você** (ou seu grupo) deverá desenvolver.
- A API **não classifica** o estoque e **não recomenda reposição**. Ela entrega apenas os dados brutos (quantidade atual e estoque mínimo). Decidir o que é estoque normal, baixo ou esgotado é parte do trabalho do agente.
- Os dados são fictícios e iguais para todos os estudantes, o que torna os resultados reproduzíveis.
- A API funciona 100% em ambiente local, sem internet e sem serviços externos.

## 2. Requisitos

| Item | Detalhe |
|---|---|
| Python | **3.11 ou superior** |
| Dependências | `fastapi`, `uvicorn`, `pydantic`, `pytest`, `httpx` (listadas em `requirements.txt`) |
| Ferramentas | `git`, `pip` e o módulo `venv` do Python; `curl` (opcional, para os exemplos de linha de comando) |
| Porta | **8000** (endereço padrão: `http://127.0.0.1:8000`) |

Para verificar sua versão do Python:

```bash
python --version      # em alguns sistemas Linux/macOS: python3 --version
```

## 3. Instalação e configuração

**1. Clone o repositório** e **2. acesse o diretório**:

```bash
git clone https://github.com/wangsouza/api-estoque.git
cd api-estoque
```

**3. Crie um ambiente virtual Python:**

```bash
python -m venv .venv
```

**4. Ative o ambiente virtual no Linux/macOS:**

```bash
source .venv/bin/activate
```

**5. Ative o ambiente virtual no Windows:**

```powershell
# PowerShell
.venv\Scripts\Activate.ps1

# Prompt de Comando (cmd)
.venv\Scripts\activate.bat
```

> No PowerShell, se aparecer erro de política de execução, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Com o ambiente ativo, o terminal exibe `(.venv)` no início da linha.

**6. Instale as dependências:**

```bash
pip install -r requirements.txt
```

## 4. Execução

Na raiz do projeto, com o ambiente virtual ativo:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- `app.main:app` indica o módulo `app/main.py` e o objeto `app` do FastAPI.
- `--reload` reinicia o servidor automaticamente quando o código Python muda (útil no desenvolvimento).
- `--host 127.0.0.1` aceita conexões apenas do seu próprio computador.

**Como verificar se o servidor está funcionando.** Em outro terminal:

```bash
curl http://127.0.0.1:8000/health
```

Resposta esperada:

```json
{"status":"ok","service":"api-estoque","version":"1.0.0"}
```

Você também pode abrir http://127.0.0.1:8000/health no navegador. Para parar o servidor, pressione `Ctrl+C` no terminal em que ele está rodando.

> **Acesso por rede ou Docker.** Quando outro equipamento ou um contêiner Docker precisar acessar a API, o servidor pode escutar em todas as interfaces com `--host 0.0.0.0`. Faça isso **apenas em um ambiente de desenvolvimento controlado** (a API não tem autenticação — veja a [seção 15](#15-segurança-e-limitações)):
>
> ```bash
> python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
> ```

## 5. Swagger (documentação interativa)

Com o servidor em execução, a API publica automaticamente:

| Recurso | Endereço |
|---|---|
| Swagger UI (testar pelo navegador) | http://127.0.0.1:8000/docs |
| ReDoc (documentação para leitura) | http://127.0.0.1:8000/redoc |
| Especificação OpenAPI (JSON) | http://127.0.0.1:8000/openapi.json |

### Como testar um endpoint no Swagger

1. Abra http://127.0.0.1:8000/docs.
2. Clique no endpoint desejado (por exemplo, `GET /produtos/{codigo}`) para expandi-lo.
3. Clique em **Try it out**.
4. Preencha os parâmetros (por exemplo, `codigo` = `PRD-001`).
5. Clique em **Execute**.
6. Veja o código HTTP, o corpo da resposta e o comando `curl` equivalente logo abaixo.

### Tutorial: cadastrar um produto pelo Swagger

1. Abra http://127.0.0.1:8000/docs.
2. Selecione **`POST /produtos`**.
3. Clique em **Try it out**.
4. Informe os dados em JSON no corpo da requisição (o Swagger já traz um exemplo; há também um menu com exemplos de cadastro duplicado e de quantidade negativa):

   ```json
   {
     "codigo": "PRD-020",
     "nome": "Teclado mecânico",
     "categoria": "Periféricos",
     "quantidade_atual": 15,
     "estoque_minimo": 5,
     "unidade": "un"
   }
   ```

5. Clique em **Execute**.
6. Verifique a resposta **HTTP 201** (*Created*) com os dados do produto.
7. Consulte o novo produto em **`GET /produtos/{codigo}`**, informando `PRD-020`. Deve retornar **HTTP 200**.

> Se você clicar em **Execute** uma segunda vez, receberá **HTTP 409**: o código `PRD-020` já existe. Isso é esperado.

### Códigos HTTP utilizados

| Código | Nome | Significado nesta API |
|---|---|---|
| **200** | OK | A consulta foi feita com sucesso e a resposta traz os dados. |
| **201** | Created | O produto foi cadastrado e gravado em `data/produtos.json`. |
| **404** | Not Found | O código tem formato válido, mas **não existe** produto com ele. |
| **409** | Conflict | O cadastro foi recusado porque **já existe** produto com aquele código. |
| **422** | Unprocessable Content | Os dados enviados são **inválidos**: código fora do padrão `PRD-XXX`, campo ausente, valor negativo, tipo errado, código reservado etc. |
| **503** | Service Unavailable | **Indisponibilidade simulada** (somente `GET /produtos/PRD-503`). Em uma integração real, significa "tente novamente mais tarde". |
| 500 | Internal Server Error | Falha ao ler/gravar o arquivo de dados (veja a [seção 14](#14-resolução-de-problemas)). Não faz parte dos cenários de teste. |

## 6. Endpoints

| Método | Caminho | Finalidade | Respostas possíveis |
|---|---|---|---|
| `GET` | `/health` | Verificar se a API está disponível | 200 |
| `GET` | `/produtos` | Listar produtos (filtro opcional `?categoria=`) | 200 |
| `GET` | `/produtos/{codigo}` | Consultar um produto pelo código | 200, 404, 422, 503 |
| `POST` | `/produtos` | Cadastrar um novo produto (**modifica os dados**) | 201, 409, 422 |
| `GET` | `/categorias` | Listar as categorias existentes | 200 |

Não existem endpoints para editar ou excluir produtos.

### Formato dos erros

Os erros de negócio (404, 409, 503) usam sempre o mesmo formato, com um identificador estável em `erro` (ideal para o seu código tratar) e uma `mensagem` legível:

```json
{
  "erro": "produto_nao_encontrado",
  "mensagem": "Produto não encontrado."
}
```

| HTTP | Valor de `erro` | Situação |
|---|---|---|
| 404 | `produto_nao_encontrado` | Produto inexistente |
| 409 | `produto_duplicado` | Código já cadastrado |
| 422 | `codigo_invalido` | Código com formato inválido na URL |
| 422 | `dados_invalidos` | Corpo do cadastro inválido |
| 503 | `servico_indisponivel` | Indisponibilidade simulada |
| 500 | `erro_armazenamento` | Falha no arquivo de dados |

Nos erros **422**, o campo `detail` padrão do FastAPI/Pydantic é mantido (lista com `type`, `loc`, `msg` e `input`), e os campos `erro` e `mensagem` são acrescentados.

### `GET /health`

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"ok","service":"api-estoque","version":"1.0.0"}
```

### `GET /produtos`

Retorna `total` e a lista `produtos`, **sempre ordenada pelo código**. Inclui os produtos cadastrados via `POST`.

```bash
curl http://127.0.0.1:8000/produtos
```

Filtro opcional por categoria (ignora maiúsculas/minúsculas, mas os acentos precisam coincidir; categoria inexistente devolve lista vazia com HTTP 200):

```bash
curl "http://127.0.0.1:8000/produtos?categoria=Papelaria"
```

> Dica: o `curl` não codifica espaços/acentos na URL; para categorias como "Cabos e Adaptadores", use `curl -G --data-urlencode "categoria=Cabos e Adaptadores" http://127.0.0.1:8000/produtos`.

### `GET /produtos/{codigo}`

```bash
curl http://127.0.0.1:8000/produtos/PRD-001
```

O código deve seguir o padrão `PRD-XXX` (três dígitos, `PRD` em maiúsculas).

### `POST /produtos`

```bash
curl -X POST http://127.0.0.1:8000/produtos \
  -H "Content-Type: application/json" \
  -d '{"codigo":"PRD-020","nome":"Teclado mecânico","categoria":"Periféricos","quantidade_atual":15,"estoque_minimo":5,"unidade":"un"}'
```

Detalhes na [seção 8](#8-cadastro-de-produtos).

### `GET /categorias`

```bash
curl http://127.0.0.1:8000/categorias
```

```json
{"total":8,"categorias":["Armazenamento","Cabos e Adaptadores","Computadores","Limpeza","Monitores","Papelaria","Periféricos","Suprimentos de Impressão"]}
```

Produtos cadastrados com `POST` que tragam categorias novas também passam a aparecer aqui.

## 7. Dados disponíveis

### Campos de um produto

| Campo | Tipo | Significado |
|---|---|---|
| `codigo` | texto | Identificador único, no formato `PRD-XXX` (três dígitos). |
| `nome` | texto | Nome do produto. |
| `categoria` | texto | Categoria à qual o produto pertence. |
| `quantidade_atual` | inteiro ≥ 0 | Quantidade disponível em estoque neste momento. |
| `estoque_minimo` | inteiro ≥ 0 | Nível mínimo recomendado de estoque para o produto. |
| `unidade` | texto | Unidade de medida (`un`, `pct`, `m`, `L`...). |

### Produtos iniciais (base de referência, igual para todos)

| Código | Nome | Categoria | Qtd. atual | Estoque mínimo | Unidade |
|---|---|---|---:|---:|---|
| PRD-001 | Mouse sem fio | Periféricos | 5 | 10 | un |
| PRD-002 | Teclado USB | Periféricos | 40 | 15 | un |
| PRD-003 | Monitor 24 polegadas | Monitores | 12 | 5 | un |
| PRD-004 | Cabo HDMI 2 m | Cabos e Adaptadores | 0 | 20 | un |
| PRD-005 | Papel sulfite A4 | Papelaria | 30 | 30 | pct |
| PRD-006 | Caneta esferográfica azul | Papelaria | 200 | 50 | un |
| PRD-007 | Cartucho de tinta preta | Suprimentos de Impressão | 3 | 8 | un |
| PRD-008 | Webcam Full HD | Periféricos | 0 | 5 | un |
| PRD-009 | Notebook 14 polegadas | Computadores | 8 | 8 | un |
| PRD-010 | Pen drive 64 GB | Armazenamento | 25 | 10 | un |
| PRD-011 | Álcool isopropílico | Limpeza | 4 | 10 | L |
| PRD-012 | Cabo de rede Cat6 | Cabos e Adaptadores | 150 | 100 | m |

A base inclui produtos em diferentes situações de estoque (acima do mínimo, abaixo do mínimo, exatamente no mínimo e zerados). **Descobrir quais são quais é parte da análise do seu agente.**

O código `PRD-503` é **reservado** para a simulação de indisponibilidade: não é um produto real, não aparece na listagem e não pode ser cadastrado.

### Como identificar a situação de um produto

A API **não devolve** nenhum campo como "situação" ou "status". Você deve comparar os dois campos numéricos de cada produto:

| Comparação entre `quantidade_atual` e `estoque_minimo` | Leitura usual |
|---|---|
| `quantidade_atual` **maior** que `estoque_minimo` | Estoque acima do mínimo (normal) |
| `quantidade_atual` **igual** a `estoque_minimo` | Exatamente no limite mínimo |
| `quantidade_atual` **maior que zero e menor ou igual** a `estoque_minimo` | Estoque baixo (inclui o caso do limite) |
| `quantidade_atual` **igual a zero** | Estoque esgotado |

Os critérios que valem para a sua avaliação são os definidos no enunciado do projeto; a tabela acima descreve apenas a leitura dos campos. Quem implementa a regra — e decide como tratar casos de borda — é o seu agente.

## 8. Cadastro de produtos

`POST /produtos` cria um novo produto, grava-o em `data/produtos.json` e o torna imediatamente disponível para as consultas `GET`.

> ⚠️ **Esta operação modifica a base de dados local.** Para voltar ao estado inicial, use o [script de restauração](#13-restauração-dos-dados).

### Corpo da requisição (JSON)

```json
{
  "codigo": "PRD-020",
  "nome": "Teclado mecânico",
  "categoria": "Periféricos",
  "quantidade_atual": 15,
  "estoque_minimo": 5,
  "unidade": "un"
}
```

Envie o cabeçalho `Content-Type: application/json`.

### Campos obrigatórios e restrições

Todos os seis campos são **obrigatórios**:

| Campo | Regra |
|---|---|
| `codigo` | Padrão `PRD-XXX` (três dígitos); **único**; não pode ser `PRD-503` (reservado). |
| `nome` | Texto não vazio. |
| `categoria` | Texto não vazio. |
| `quantidade_atual` | Número **inteiro** ≥ 0. |
| `estoque_minimo` | Número **inteiro** ≥ 0. |
| `unidade` | Texto não vazio. |

Outras regras:

- Os tipos são validados **sem conversão implícita**: `"15"` (texto), `15.5` (decimal) e `true` são rejeitados nos campos inteiros.
- Espaços nas extremidades dos textos são removidos (`"  Teclado  "` vira `"Teclado"`). Um texto só com espaços é considerado vazio.
- **Campos desconhecidos são rejeitados**, o que ajuda a detectar erros de digitação (por exemplo, `quantidade` em vez de `quantidade_atual`).

### Resposta de sucesso — HTTP 201

```json
{
  "codigo": "PRD-020",
  "nome": "Teclado mecânico",
  "categoria": "Periféricos",
  "quantidade_atual": 15,
  "estoque_minimo": 5,
  "unidade": "un"
}
```

### Código duplicado — HTTP 409

```json
{
  "erro": "produto_duplicado",
  "mensagem": "Já existe um produto cadastrado com o código PRD-020."
}
```

Um produto já cadastrado **não pode ser criado de novo** com o mesmo código, e a API não oferece edição nem exclusão. Para cadastrar outro produto, use outro código.

### Dados inválidos — HTTP 422

Campos ausentes, valores negativos, tipos incorretos, textos vazios, código fora do padrão ou o código reservado `PRD-503` resultam em HTTP 422, com `erro` igual a `dados_invalidos` e o detalhe de cada problema em `detail`. Nada é gravado. Veja exemplos na [seção 9](#9-exemplos-de-utilização).

### Persistência

- O produto é gravado em `data/produtos.json` **antes** de a resposta 201 ser enviada.
- A gravação usa um arquivo temporário que substitui o original ao final, evitando um JSON corrompido caso algo falhe no meio da escrita.
- Os produtos **permanecem após reiniciar** a API.
- A persistência é pensada para **uma única instância local de desenvolvimento**, sem a garantia de concorrência de um banco de dados transacional.

### Consultar o produto recém-criado

```bash
curl http://127.0.0.1:8000/produtos/PRD-020
```

Ele também aparece em `GET /produtos` (na posição determinada pela ordenação por código) e sua categoria passa a constar em `GET /categorias`.

### Exemplo completo com curl

```bash
curl -X POST \
  http://127.0.0.1:8000/produtos \
  -H "Content-Type: application/json" \
  -d '{
    "codigo": "PRD-020",
    "nome": "Teclado mecânico",
    "categoria": "Periféricos",
    "quantidade_atual": 15,
    "estoque_minimo": 5,
    "unidade": "un"
  }'
```

> No Windows PowerShell, aspas simples dentro de `-d` costumam falhar. Use o `curl.exe` com o JSON escapado, ou prefira o Swagger (`/docs`).

## 9. Exemplos de utilização

As respostas abaixo foram geradas pela própria API (campos longos foram abreviados com `...`).

### Listagem de produtos

```bash
curl http://127.0.0.1:8000/produtos
```

```json
{
  "total": 12,
  "produtos": [
    {
      "codigo": "PRD-001",
      "nome": "Mouse sem fio",
      "categoria": "Periféricos",
      "quantidade_atual": 5,
      "estoque_minimo": 10,
      "unidade": "un"
    },
    ...
  ]
}
```

Com filtro de categoria (`?categoria=Papelaria`), o resultado é:

```json
{
  "total": 2,
  "produtos": [
    {"codigo": "PRD-005", "nome": "Papel sulfite A4", "categoria": "Papelaria", "quantidade_atual": 30, "estoque_minimo": 30, "unidade": "pct"},
    {"codigo": "PRD-006", "nome": "Caneta esferográfica azul", "categoria": "Papelaria", "quantidade_atual": 200, "estoque_minimo": 50, "unidade": "un"}
  ]
}
```

### Consulta individual — HTTP 200

```bash
curl -i http://127.0.0.1:8000/produtos/PRD-001
```

```json
{
  "codigo": "PRD-001",
  "nome": "Mouse sem fio",
  "categoria": "Periféricos",
  "quantidade_atual": 5,
  "estoque_minimo": 10,
  "unidade": "un"
}
```

### Produto inexistente — HTTP 404

```bash
curl -i http://127.0.0.1:8000/produtos/PRD-999
```

```json
{
  "erro": "produto_nao_encontrado",
  "mensagem": "Produto não encontrado."
}
```

### Código inválido — HTTP 422

```bash
curl -i http://127.0.0.1:8000/produtos/ABC-1
```

```json
{
  "erro": "codigo_invalido",
  "mensagem": "Código de produto inválido. Use o formato PRD-XXX, em que XXX são três dígitos (exemplo: PRD-001).",
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["path", "codigo"],
      "msg": "String should match pattern '^PRD-[0-9]{3}$'",
      "input": "ABC-1",
      "ctx": {"pattern": "^PRD-[0-9]{3}$"}
    }
  ]
}
```

### Serviço indisponível — HTTP 503

O código `PRD-503` **sempre** responde 503 (comportamento determinístico, útil para testar o tratamento de falhas do seu agente):

```bash
curl -i http://127.0.0.1:8000/produtos/PRD-503
```

```json
{
  "erro": "servico_indisponivel",
  "mensagem": "Serviço temporariamente indisponível. Tente novamente mais tarde."
}
```

### Cadastro bem-sucedido — HTTP 201

```bash
curl -i -X POST http://127.0.0.1:8000/produtos \
  -H "Content-Type: application/json" \
  -d '{"codigo":"PRD-020","nome":"Teclado mecânico","categoria":"Periféricos","quantidade_atual":15,"estoque_minimo":5,"unidade":"un"}'
```

```json
{
  "codigo": "PRD-020",
  "nome": "Teclado mecânico",
  "categoria": "Periféricos",
  "quantidade_atual": 15,
  "estoque_minimo": 5,
  "unidade": "un"
}
```

### Cadastro duplicado — HTTP 409

Repetindo o mesmo comando acima:

```json
{
  "erro": "produto_duplicado",
  "mensagem": "Já existe um produto cadastrado com o código PRD-020."
}
```

### Cadastro com dados inválidos — HTTP 422

Quantidade negativa:

```bash
curl -i -X POST http://127.0.0.1:8000/produtos \
  -H "Content-Type: application/json" \
  -d '{"codigo":"PRD-021","nome":"Headset USB","categoria":"Periféricos","quantidade_atual":-3,"estoque_minimo":5,"unidade":"un"}'
```

```json
{
  "erro": "dados_invalidos",
  "mensagem": "Dados inválidos nos campos: quantidade_atual. Consulte 'detail' para mais informações.",
  "detail": [
    {
      "type": "greater_than_equal",
      "loc": ["body", "quantidade_atual"],
      "msg": "Input should be greater than or equal to 0",
      "input": -3,
      "ctx": {"ge": 0}
    }
  ]
}
```

Campos obrigatórios ausentes (`-d '{"codigo":"PRD-021","nome":"Headset"}'`) retornam um item em `detail` para cada campo faltante (`categoria`, `quantidade_atual`, `estoque_minimo` e `unidade`), todos com `"type": "missing"`.

O código reservado (`"codigo": "PRD-503"`) também retorna 422, com `loc` igual a `["body", "codigo"]` e uma mensagem explicando que ele é reservado.

## 10. Integração com Python e agentes de IA

Qualquer aplicação Python pode consumir esta API por meio de **requisições HTTP**: o programa envia uma requisição para uma URL (por exemplo, `http://127.0.0.1:8000/produtos/PRD-001`), recebe um código de status e um corpo JSON e transforma esse JSON em estruturas Python (dicionários e listas). Bibliotecas como `requests` ou `httpx` fazem esse trabalho. Ao integrar, planeje:

- **Verificar o código de status** antes de usar o corpo da resposta (200 não significa o mesmo que 404 ou 503).
- **Definir um tempo limite (*timeout*)** e tratar erros de conexão, como API desligada.
- **Ler o campo `erro`** das respostas de falha, em vez de depender do texto da `mensagem`.

No projeto avaliativo, você deverá **implementar ferramentas (*tools*) em Python que consultem os endpoints** e disponibilizá-las ao agente construído com **LangGraph**. O modelo de linguagem decide *quando* chamar cada ferramenta; as ferramentas fazem a chamada HTTP e devolvem os dados; e o agente fundamenta sua resposta nesses dados.

**Leitura × criação:**

| Tipo | Métodos/endpoints | Efeito |
|---|---|---|
| Leitura | `GET /produtos`, `GET /produtos/{codigo}`, `GET /categorias`, `GET /health` | Não alteram nada; podem ser repetidos à vontade. |
| Criação | `POST /produtos` | **Altera a base de dados.** Repetir a chamada com o mesmo código gera 409. |

O agente de análise de estoque **pode trabalhar apenas com consultas (`GET`)**. Usar o `POST` pelo agente é **opcional**. Se você decidir permitir que o agente cadastre produtos, a operação **deve exigir confirmação humana antes de modificar os dados**.

> Este repositório **não** contém código de agente, ferramentas prontas, fluxos LangGraph nem soluções da avaliação.

## 11. Integração com n8n

Para conectar o n8n a esta API, você só precisa do nó **HTTP Request**:

- **Método `GET`** para consultas (`/health`, `/produtos`, `/produtos/PRD-001`, `/categorias`).
- **Método `POST`** para cadastro: no nó, habilite o envio de corpo (*Send Body*), escolha o formato **JSON** e informe os campos do produto. O cabeçalho `Content-Type: application/json` é definido pelo nó.
- **Endereço da API:** depende de onde o n8n está rodando (veja abaixo).

| Onde o n8n roda | URL base a usar |
|---|---|
| Direto no seu computador (por exemplo, `npx n8n`) | `http://127.0.0.1:8000` |
| Em um contêiner Docker | `http://host.docker.internal:8000` |
| n8n Cloud | A API local **não é acessível** (veja abaixo) |

### `localhost` no computador × `localhost` no contêiner

Dentro de um contêiner Docker, `localhost` e `127.0.0.1` referem-se **ao próprio contêiner**, não ao seu computador. Por isso, um n8n em Docker que chame `http://localhost:8000` **não encontra** a API que está rodando no seu computador.

Use `host.docker.internal`, um nome que aponta para o computador hospedeiro:

- No **Docker Desktop (Windows/macOS)** ele já funciona.
- No **Linux**, é preciso mapeá-lo ao iniciar o contêiner, com `--add-host=host.docker.internal:host-gateway` (ou, no Docker Compose, `extra_hosts: ["host.docker.internal:host-gateway"]`).
- Nesse cenário, a API precisa **escutar em `0.0.0.0`** (`--host 0.0.0.0`), pois com `127.0.0.1` ela só aceita conexões de dentro do próprio computador. Faça isso apenas em rede de desenvolvimento controlada.

### n8n Cloud

O n8n Cloud roda na internet e **não consegue acessar** uma API que está em `localhost` no seu computador. Para essa atividade, prefira o n8n executado localmente. Expor a API à internet (por exemplo, com túneis) **não é recomendado**: ela não tem autenticação, e qualquer pessoa com o endereço poderia cadastrar produtos. Se precisar dessa opção, converse antes com o professor.

> ⚠️ Requisições `POST` **modificam os dados**. Use-as com cuidado nas automações (um fluxo executado repetidamente gera erros 409 ou novos cadastros indesejados) e lembre-se de que o [script de restauração](#13-restauração-dos-dados) devolve a base ao estado inicial.

Este repositório **não** inclui workflows prontos: a automação é uma atividade avaliativa.

## 12. Testes da API

Com o ambiente virtual ativo, na raiz do projeto:

```bash
python -m pytest -v
```

Os testes automatizados do arquivo `tests/test_api.py` verificam se **a API entrega o contrato prometido**: disponibilidade, listagem, consulta, erros 404/422/503, tipos dos campos, cadastro, duplicidade, validações, persistência, restauração e isolamento dos dados. Eles servem para garantir que a API continue correta se alguém modificá-la.

Eles **não** substituem os testes que você deve escrever para o **seu agente** (por exemplo, se ele escolhe a ferramenta certa, se interpreta corretamente as respostas de erro, se não inventa dados e se pede confirmação antes de cadastrar). Essa parte é responsabilidade sua.

**Isolamento:** os testes trabalham sobre uma **cópia temporária** da base original, criada para cada teste. Os cadastros feitos durante os testes **não alteram** `data/produtos.json` nem `data/produtos_original.json` — você pode rodá-los sem receio de perder ou poluir os dados da sua execução. Eles não precisam de internet nem de o servidor estar ligado.

> Ao rodar os testes, o `pytest` pode exibir um aviso de depreciação (`StarletteDeprecationWarning`) sobre o `httpx`. Ele não afeta os resultados.

## 13. Restauração dos dados

> ⚠️ **ATENÇÃO:** a restauração **apaga todos os produtos cadastrados depois da instalação** (via `POST /produtos`). Esses cadastros serão **perdidos** e não há como desfazê-los.

Com o ambiente virtual ativo, na raiz do projeto:

```bash
python scripts/reset_data.py
```

Saída esperada (o caminho varia conforme o seu computador):

```text
Base restaurada: 12 produtos gravados em /caminho/do/projeto/data/produtos.json
```

A restauração:

- **Remove** os produtos cadastrados posteriormente;
- **Recupera os 12 produtos iniciais**, copiando `data/produtos_original.json` para `data/produtos.json`;
- Permite **repetir os exercícios com os mesmos dados**;
- **Não modifica o código-fonte** da API nem o arquivo `data/produtos_original.json`.

O script pode ser executado com a API ligada: como a API relê o arquivo a cada requisição, a base restaurada é refletida imediatamente, sem reiniciar o servidor.

> **Sobre o Git:** como `data/produtos.json` é versionado, após cadastrar produtos o `git status` o mostrará como modificado. Rodar o script de restauração resolve isso. Evite fazer *commit* de uma base alterada.

## 14. Resolução de problemas

| Problema | Causa provável e solução |
|---|---|
| **Porta 8000 ocupada** (`address already in use`) | Outro programa (ou uma instância anterior da API) usa a porta. Encerre-o ou use outra porta: `python -m uvicorn app.main:app --reload --port 8001` (e ajuste as URLs). Para descobrir quem usa a porta: `ss -ltnp \| grep 8000` (Linux), `lsof -i :8000` (macOS) ou `netstat -ano \| findstr :8000` (Windows). |
| **`ModuleNotFoundError: No module named 'app'`** | Você não está na raiz do projeto. Use `cd api-estoque` e rode o comando de lá. Execute os testes com `python -m pytest`. |
| **`ModuleNotFoundError` (`fastapi`, `uvicorn`, `pydantic`...)** ou **`No module named uvicorn`** | Dependências ausentes ou ambiente virtual não ativado. Ative o ambiente (seção 3) e rode `pip install -r requirements.txt`. |
| **Ambiente virtual não ativado** | O prompt não mostra `(.venv)` e comandos como `pip`/`python` apontam para a instalação global. Ative o ambiente e confirme com `which python` (Linux/macOS) ou `where python` (Windows). |
| **Erro de conexão** (`Connection refused`, `Failed to connect`) | O servidor não está rodando, está em outra porta ou o endereço está errado. Confirme com `curl http://127.0.0.1:8000/health`. |
| **HTTP 404** | O código tem formato válido, mas não existe produto com ele. Consulte `GET /produtos` para ver os códigos existentes. Um 404 também ocorre se o caminho estiver errado (por exemplo, `/produto` em vez de `/produtos`). |
| **HTTP 409** | Você tentou cadastrar um código que já existe. Use outro código ou, se quiser recomeçar, restaure a base ([seção 13](#13-restauração-dos-dados)). |
| **HTTP 422** | Dados ou código inválidos. Leia `mensagem` e o campo `detail` da resposta: `loc` indica qual campo falhou e `msg` explica o motivo. Causas comuns: `prd-001` em minúsculas, número em texto (`"15"`), valor negativo, campo faltando, campo extra. |
| **HTTP 503** | É a simulação de indisponibilidade, esperada para `PRD-503`. Se ocorrer com outro código, consulte o log do servidor. |
| **Produto não encontrado após o cadastro** | Verifique se o cadastro retornou **201** (um 409 ou 422 não grava nada); se o código consultado é exatamente o cadastrado; se a restauração (`reset_data.py`) não foi executada depois; e se você está consultando a API que gravou em `data/produtos.json` deste projeto (e não outra instância ou diretório). |
| **Falha de permissão ao gravar o JSON** (HTTP 500 com `erro_armazenamento`) | O usuário que executa a API não pode escrever em `data/`. Ajuste as permissões da pasta e do arquivo (por exemplo, `chmod u+rw data data/produtos.json` no Linux/macOS). Se o JSON foi editado à mão e ficou inválido, restaure a base com `python scripts/reset_data.py`. |
| **n8n em Docker não acessa a API local** | Dentro do contêiner, `localhost` é o próprio contêiner. Use `http://host.docker.internal:8000`; no Linux, adicione `--add-host=host.docker.internal:host-gateway` ao contêiner; inicie a API com `--host 0.0.0.0`; e verifique o firewall do computador. Teste primeiro com o comando `curl` dentro do contêiner. |

## 15. Segurança e limitações

- A API usa **dados fictícios**.
- **Não possui autenticação** nem autorização.
- **Não foi desenvolvida para uso em produção.**
- **Não deve ser exposta publicamente** sem controles apropriados (autenticação, HTTPS, limites de uso etc.).
- Permite **consultar e cadastrar** produtos. **Não permite editar nem excluir.**
- Os novos produtos são **persistidos localmente em um arquivo JSON**.
- **Não há controle transacional** nem suporte a concorrência entre várias instâncias ou processos escrevendo no mesmo arquivo. Rode **uma única instância** da API por vez sobre o mesmo `data/produtos.json`.
- O cadastro é uma **operação que modifica dados**.
- Se você permitir que o agente cadastre produtos, **adote confirmação humana** antes de executar a operação.

## 16. Organização do projeto

```text
api-estoque/
├── app/
│   ├── __init__.py        # versão da API
│   ├── main.py            # configuração do FastAPI, endpoints e tratamento de erros
│   ├── models.py          # modelos Pydantic (validação de entrada e formato de saída)
│   ├── repository.py      # leitura e gravação atômica do JSON; restauração da base
│   └── services.py        # operações de consulta e cadastro (sem lógica de análise de estoque)
├── data/
│   ├── produtos.json          # dados usados pela API (alterado pelos cadastros)
│   └── produtos_original.json # cópia dos 12 produtos iniciais (nunca alterada pela API)
├── scripts/
│   └── reset_data.py      # restaura produtos.json a partir da base original
├── tests/
│   └── test_api.py        # testes automatizados (usam dados temporários)
├── .gitignore
├── LICENSE
├── pytest.ini             # configuração do pytest
├── README.md
└── requirements.txt       # dependências Python
```

## 17. Orientações finais aos estudantes

Esta API é **apenas a base disponibilizada pelo professor**. O trabalho avaliado está em **desenvolver o seu agente**: a interpretação das solicitações, as ferramentas Python, o fluxo em LangGraph, a análise do estoque, o tratamento de falhas e a automação complementar no n8n.

Você deverá **documentar sua implementação** e disponibilizá-la em **seu repositório individual ou do grupo** (até três integrantes), conforme as orientações do projeto avaliativo. Não copie a API para dentro do seu repositório como se fosse sua autoria e não altere o contrato dos endpoints.

Este repositório não traz respostas prontas para os cenários da avaliação. Explore a API pelo Swagger, teste os casos de erro e só então projete o seu agente.

Bom trabalho!

---

Licença: [MIT](LICENSE).
