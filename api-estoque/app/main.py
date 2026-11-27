"""Configuração do FastAPI e definição dos endpoints."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, FastAPI, Path as PathParam, Query, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app import __version__, services
from app.models import (
    PADRAO_CODIGO,
    ErroResposta,
    ErroValidacao,
    ListaCategorias,
    ListaProdutos,
    Produto,
    Saude,
)
from app.repository import CAMINHO_PADRAO, ErroArmazenamento, ProdutoRepository

DESCRICAO = """
API simulada para consulta e cadastro de produtos em atividades educacionais.

Os dados são **fictícios**, não há autenticação e a persistência é um arquivo JSON local.
A API apenas fornece os dados: a classificação do estoque (normal, baixo, esgotado) e as
recomendações são responsabilidade do agente desenvolvido pelos estudantes.

**Erros de negócio** (404, 409, 503 e 500) usam o formato `{"erro": "...", "mensagem": "..."}`.
**Erros de validação** (422) mantêm o campo padrão `detail` do FastAPI e acrescentam `erro` e `mensagem`.

| HTTP | `erro` | Quando ocorre |
|---|---|---|
| 200 | — | Consulta realizada com sucesso |
| 201 | — | Produto cadastrado |
| 404 | `produto_nao_encontrado` | Código válido, mas inexistente |
| 409 | `produto_duplicado` | Cadastro com código já existente |
| 422 | `codigo_invalido` | Código fora do padrão `PRD-XXX` na URL |
| 422 | `dados_invalidos` | Corpo do cadastro inválido (inclui o código reservado `PRD-503`) |
| 503 | `servico_indisponivel` | Simulação determinística: `GET /produtos/PRD-503` |
"""

TAGS = [
    {"name": "Sistema", "description": "Verificação de disponibilidade da API."},
    {"name": "Produtos", "description": "Consulta e cadastro de produtos do estoque."},
    {"name": "Categorias", "description": "Categorias presentes no estoque."},
]


def _resposta_erro(exemplo: dict[str, str], descricao: str, modelo: type = ErroResposta) -> dict[str, Any]:
    return {
        "model": modelo,
        "description": descricao,
        "content": {"application/json": {"example": exemplo}},
    }


EXEMPLO_PRODUTO_PRD001 = {
    "codigo": "PRD-001",
    "nome": "Mouse sem fio",
    "categoria": "Periféricos",
    "quantidade_atual": 5,
    "estoque_minimo": 10,
    "unidade": "un",
}

EXEMPLO_422_CODIGO = {
    "erro": "codigo_invalido",
    "mensagem": "Código de produto inválido. Use o formato PRD-XXX, em que XXX são três dígitos (exemplo: PRD-001).",
    "detail": [
        {
            "type": "string_pattern_mismatch",
            "loc": ["path", "codigo"],
            "msg": "String should match pattern '^PRD-[0-9]{3}$'",
            "input": "ABC-1",
            "ctx": {"pattern": "^PRD-[0-9]{3}$"},
        }
    ],
}

EXEMPLO_422_DADOS = {
    "erro": "dados_invalidos",
    "mensagem": "Dados inválidos nos campos: quantidade_atual. Consulte 'detail' para mais informações.",
    "detail": [
        {
            "type": "greater_than_equal",
            "loc": ["body", "quantidade_atual"],
            "msg": "Input should be greater than or equal to 0",
            "input": -3,
            "ctx": {"ge": 0},
        }
    ],
}

RESP_404 = _resposta_erro(
    {"erro": "produto_nao_encontrado", "mensagem": "Produto não encontrado."},
    "Produto inexistente.",
)
RESP_409 = _resposta_erro(
    {"erro": "produto_duplicado", "mensagem": "Já existe um produto cadastrado com o código PRD-001."},
    "Já existe um produto com este código.",
)
MENSAGEM_ERRO_ARMAZENAMENTO = (
    "Falha ao acessar o arquivo de dados. Verifique se data/produtos.json existe, "
    "é um JSON válido e tem permissão de leitura/gravação."
)

RESP_500 = _resposta_erro(
    {"erro": "erro_armazenamento", "mensagem": MENSAGEM_ERRO_ARMAZENAMENTO},
    "Falha ao ler ou gravar o arquivo de dados JSON.",
)
RESP_503 = _resposta_erro(
    {
        "erro": "servico_indisponivel",
        "mensagem": "Serviço temporariamente indisponível. Tente novamente mais tarde.",
    },
    "Indisponibilidade simulada (somente para o código reservado `PRD-503`).",
)


def get_repositorio(request: Request) -> ProdutoRepository:
    return request.app.state.repositorio


Repositorio = Annotated[ProdutoRepository, Depends(get_repositorio)]

router = APIRouter()


@router.get(
    "/health",
    tags=["Sistema"],
    summary="Verificar disponibilidade da API",
    response_model=Saude,
    responses={200: {"description": "Serviço disponível."}},
)
def health() -> Saude:
    """Retorna HTTP 200 quando o serviço está disponível."""
    return Saude(status="ok", service="api-estoque", version=__version__)


@router.get(
    "/produtos",
    tags=["Produtos"],
    summary="Listar produtos",
    response_model=ListaProdutos,
    responses={
        200: {"description": "Lista de produtos ordenada pelo código."},
        500: RESP_500,
    },
)
def listar_produtos(
    repo: Repositorio,
    categoria: Annotated[
        str | None,
        Query(
            description="Filtra pela categoria (ignora maiúsculas/minúsculas; acentos devem coincidir). "
            "Uma categoria inexistente retorna lista vazia com HTTP 200.",
            examples=["Periféricos"],
        ),
    ] = None,
) -> ListaProdutos:
    """Retorna todos os produtos cadastrados, inclusive os criados via `POST /produtos`.

    A ordem é determinística (pelo código). O filtro `categoria` é opcional.
    """
    produtos = services.listar_produtos(repo, categoria)
    return ListaProdutos(total=len(produtos), produtos=produtos)


@router.get(
    "/produtos/{codigo}",
    tags=["Produtos"],
    summary="Consultar um produto pelo código",
    response_model=Produto,
    responses={
        200: {
            "description": "Produto encontrado.",
            "content": {"application/json": {"example": EXEMPLO_PRODUTO_PRD001}},
        },
        404: RESP_404,
        422: _resposta_erro(EXEMPLO_422_CODIGO, "Código fora do padrão `PRD-XXX`.", ErroValidacao),
        500: RESP_500,
        503: RESP_503,
    },
)
def obter_produto(
    repo: Repositorio,
    codigo: Annotated[
        str,
        PathParam(
            pattern=PADRAO_CODIGO,
            description="Código do produto no formato `PRD-XXX` (três dígitos). "
            "`PRD-503` simula indisponibilidade (HTTP 503).",
            examples=["PRD-001"],
        ),
    ],
) -> Produto:
    """Consulta um produto específico.

    - **200**: produto encontrado.
    - **404**: código válido, mas inexistente.
    - **422**: código com formato inválido.
    - **503**: indisponibilidade simulada, sempre que o código for `PRD-503`.
    """
    return services.obter_produto(repo, codigo)


@router.post(
    "/produtos",
    tags=["Produtos"],
    summary="Cadastrar um novo produto",
    status_code=status.HTTP_201_CREATED,
    response_model=Produto,
    responses={
        201: {
            "description": "Produto cadastrado e persistido em `data/produtos.json`.",
            "content": {
                "application/json": {
                    "example": {
                        "codigo": "PRD-020",
                        "nome": "Teclado mecânico",
                        "categoria": "Periféricos",
                        "quantidade_atual": 15,
                        "estoque_minimo": 5,
                        "unidade": "un",
                    }
                }
            },
        },
        409: RESP_409,
        422: _resposta_erro(
            EXEMPLO_422_DADOS,
            "Dados inválidos, campo obrigatório ausente ou código reservado (`PRD-503`).",
            ErroValidacao,
        ),
        500: RESP_500,
    },
)
def cadastrar_produto(
    repo: Repositorio,
    produto: Annotated[
        Produto,
        Body(
            openapi_examples={
                "valido": {
                    "summary": "Cadastro válido (201)",
                    "value": {
                        "codigo": "PRD-020",
                        "nome": "Teclado mecânico",
                        "categoria": "Periféricos",
                        "quantidade_atual": 15,
                        "estoque_minimo": 5,
                        "unidade": "un",
                    },
                },
                "duplicado": {
                    "summary": "Código já existente (409)",
                    "value": EXEMPLO_PRODUTO_PRD001,
                },
                "quantidade_negativa": {
                    "summary": "Quantidade negativa (422)",
                    "value": {
                        "codigo": "PRD-021",
                        "nome": "Headset USB",
                        "categoria": "Periféricos",
                        "quantidade_atual": -3,
                        "estoque_minimo": 5,
                        "unidade": "un",
                    },
                },
            }
        ),
    ],
) -> Produto:
    """Cadastra um novo produto e o grava em `data/produtos.json`.

    **Esta operação modifica os dados.** Regras de validação:

    - `codigo` no formato `PRD-XXX`, único e diferente de `PRD-503` (reservado).
    - `nome`, `categoria` e `unidade` não vazios (espaços nas extremidades são removidos).
    - `quantidade_atual` e `estoque_minimo` inteiros maiores ou iguais a zero
      (sem conversão implícita: `"15"` ou `15.5` são rejeitados).
    - Campos desconhecidos são rejeitados.

    Persistência em JSON local, sem controle de concorrência entre múltiplos processos.
    """
    return services.cadastrar_produto(repo, produto)


@router.get(
    "/categorias",
    tags=["Categorias"],
    summary="Listar categorias",
    response_model=ListaCategorias,
    responses={200: {"description": "Categorias distintas em ordem alfabética."}, 500: RESP_500},
)
def listar_categorias(repo: Repositorio) -> ListaCategorias:
    """Retorna as categorias existentes, incluindo as de produtos cadastrados via POST."""
    categorias = services.listar_categorias(repo)
    return ListaCategorias(total=len(categorias), categorias=categorias)


# --------------------------------------------------------------------------- tratamento de erros


async def _tratar_erro_negocio(request: Request, exc: services.ErroNegocio) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"erro": exc.erro, "mensagem": exc.mensagem})


async def _tratar_erro_armazenamento(request: Request, exc: ErroArmazenamento) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"erro": "erro_armazenamento", "mensagem": MENSAGEM_ERRO_ARMAZENAMENTO},
    )


def _detalhes_serializaveis(erros: list[Any]) -> list[Any]:
    """Torna `exc.errors()` serializável (o Pydantic pode incluir exceções em `ctx`)."""
    limpos = []
    for erro in erros:
        erro = dict(erro)
        if "ctx" in erro:
            erro["ctx"] = {k: (str(v) if isinstance(v, Exception) else v) for k, v in erro["ctx"].items()}
        limpos.append(erro)
    return jsonable_encoder(limpos)


async def _tratar_validacao(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Mantém o `detail` padrão do FastAPI e acrescenta `erro` e `mensagem`."""
    erros = exc.errors()
    if any(e["loc"] and e["loc"][0] == "path" for e in erros):
        identificador = "codigo_invalido"
        mensagem = "Código de produto inválido. Use o formato PRD-XXX, em que XXX são três dígitos (exemplo: PRD-001)."
    else:
        identificador = "dados_invalidos"
        campos = list(
            dict.fromkeys(
                e["loc"][1]
                for e in erros
                if len(e["loc"]) > 1 and e["loc"][0] == "body" and isinstance(e["loc"][1], str)
            )
        )
        if campos:
            mensagem = f"Dados inválidos nos campos: {', '.join(campos)}. Consulte 'detail' para mais informações."
        else:
            mensagem = "Corpo da requisição ausente ou inválido. Consulte 'detail' para mais informações."
    return JSONResponse(
        status_code=422,
        content={"erro": identificador, "mensagem": mensagem, "detail": _detalhes_serializaveis(erros)},
    )


def create_app(caminho_dados: Path | None = None) -> FastAPI:
    """Cria a aplicação. `caminho_dados` permite usar outro JSON (usado nos testes)."""
    app = FastAPI(
        title="API de Estoque — Projeto Avaliativo de Agentes de IA",
        version=__version__,
        description=DESCRICAO,
        openapi_tags=TAGS,
    )
    app.state.repositorio = ProdutoRepository(caminho_dados or CAMINHO_PADRAO)
    app.include_router(router)
    app.add_exception_handler(services.ErroNegocio, _tratar_erro_negocio)
    app.add_exception_handler(ErroArmazenamento, _tratar_erro_armazenamento)
    app.add_exception_handler(RequestValidationError, _tratar_validacao)
    return app


app = create_app()
