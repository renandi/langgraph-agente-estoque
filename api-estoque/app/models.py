"""Modelos Pydantic de entrada e saída da API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

PADRAO_CODIGO = r"^PRD-[0-9]{3}$"
CODIGO_RESERVADO = "PRD-503"  # Reservado para a simulação de indisponibilidade (HTTP 503).


class Produto(BaseModel):
    """Produto do estoque. Usado no cadastro (entrada) e nas consultas (saída)."""

    model_config = ConfigDict(
        strict=True,  # sem conversões implícitas: "15" (texto) não é aceito como inteiro
        extra="forbid",  # campos desconhecidos são rejeitados (evita erros de digitação)
        str_strip_whitespace=True,  # remove espaços nas extremidades dos textos
        json_schema_extra={
            "examples": [
                {
                    "codigo": "PRD-020",
                    "nome": "Teclado mecânico",
                    "categoria": "Periféricos",
                    "quantidade_atual": 15,
                    "estoque_minimo": 5,
                    "unidade": "un",
                }
            ]
        },
    )

    codigo: str = Field(
        pattern=PADRAO_CODIGO,
        description="Identificador único do produto no formato `PRD-XXX` (três dígitos).",
        examples=["PRD-020"],
    )
    nome: str = Field(min_length=1, description="Nome do produto.", examples=["Teclado mecânico"])
    categoria: str = Field(min_length=1, description="Categoria do produto.", examples=["Periféricos"])
    quantidade_atual: int = Field(
        ge=0, description="Quantidade disponível em estoque (inteiro >= 0).", examples=[15]
    )
    estoque_minimo: int = Field(
        ge=0, description="Nível mínimo recomendado de estoque (inteiro >= 0).", examples=[5]
    )
    unidade: str = Field(
        min_length=1, description="Unidade de medida (ex.: `un`, `pct`, `m`, `L`).", examples=["un"]
    )

    @field_validator("codigo")
    @classmethod
    def _rejeitar_codigo_reservado(cls, valor: str) -> str:
        if valor == CODIGO_RESERVADO:
            raise ValueError(
                f"O código {CODIGO_RESERVADO} é reservado para a simulação de indisponibilidade "
                "e não pode ser cadastrado."
            )
        return valor


class ListaProdutos(BaseModel):
    """Resposta de `GET /produtos`."""

    total: int = Field(description="Quantidade de produtos retornados.", examples=[12])
    produtos: list[Produto] = Field(description="Produtos ordenados pelo código.")


class ListaCategorias(BaseModel):
    """Resposta de `GET /categorias`."""

    total: int = Field(description="Quantidade de categorias.", examples=[8])
    categorias: list[str] = Field(description="Categorias em ordem alfabética.")


class Saude(BaseModel):
    """Resposta de `GET /health`."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["api-estoque"])
    version: str = Field(examples=["1.0.0"])


class ErroResposta(BaseModel):
    """Formato padronizado dos erros de negócio (404, 409, 503 e 500)."""

    erro: str = Field(description="Identificador estável do erro (para uso em código).")
    mensagem: str = Field(description="Mensagem em português, legível por pessoas.")


class DetalheValidacao(BaseModel):
    """Um item do campo `detail` — formato padrão de erros de validação do FastAPI/Pydantic."""

    type: str = Field(examples=["greater_than_equal"])
    loc: list[str | int] = Field(examples=[["body", "quantidade_atual"]])
    msg: str = Field(examples=["Input should be greater than or equal to 0"])
    input: Any = Field(default=None, examples=[-3])
    ctx: dict[str, Any] | None = None


class ErroValidacao(ErroResposta):
    """Erro 422: campos `erro` e `mensagem` + `detail` (contrato padrão do FastAPI, preservado)."""

    detail: list[DetalheValidacao]
