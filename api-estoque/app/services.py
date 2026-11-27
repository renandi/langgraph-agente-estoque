"""Operações de consulta e cadastro de produtos.

Esta camada NÃO classifica o estoque nem recomenda reposição: isso é responsabilidade
do agente desenvolvido pelos estudantes.
"""

from app.models import CODIGO_RESERVADO, Produto
from app.repository import ProdutoRepository


class ErroNegocio(Exception):
    """Erro de negócio com status HTTP e identificador estável."""

    status_code: int = 400
    erro: str = "erro_negocio"
    mensagem: str = "Erro de negócio."

    def __init__(self, mensagem: str | None = None) -> None:
        super().__init__(mensagem or self.mensagem)
        self.mensagem = mensagem or self.mensagem


class ProdutoNaoEncontrado(ErroNegocio):
    status_code = 404
    erro = "produto_nao_encontrado"
    mensagem = "Produto não encontrado."


class ProdutoDuplicado(ErroNegocio):
    status_code = 409
    erro = "produto_duplicado"
    mensagem = "Já existe um produto cadastrado com este código."


class ServicoIndisponivel(ErroNegocio):
    status_code = 503
    erro = "servico_indisponivel"
    mensagem = "Serviço temporariamente indisponível. Tente novamente mais tarde."


def listar_produtos(repo: ProdutoRepository, categoria: str | None = None) -> list[Produto]:
    """Lista os produtos; se `categoria` for informada, filtra ignorando maiúsculas/minúsculas."""
    produtos = repo.listar()
    if categoria is not None:
        alvo = categoria.strip().casefold()
        produtos = [p for p in produtos if p.categoria.casefold() == alvo]
    return produtos


def obter_produto(repo: ProdutoRepository, codigo: str) -> Produto:
    if codigo == CODIGO_RESERVADO:
        raise ServicoIndisponivel()
    produto = repo.buscar(codigo)
    if produto is None:
        raise ProdutoNaoEncontrado()
    return produto


def cadastrar_produto(repo: ProdutoRepository, produto: Produto) -> Produto:
    if not repo.adicionar(produto):
        raise ProdutoDuplicado(f"Já existe um produto cadastrado com o código {produto.codigo}.")
    return produto


def listar_categorias(repo: ProdutoRepository) -> list[str]:
    """Categorias distintas, em ordem alfabética."""
    return sorted({p.categoria for p in repo.listar()}, key=str.casefold)
