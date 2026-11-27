"""Leitura e persistência dos produtos em arquivo JSON.

Atenção: esta persistência é destinada a uma única instância local de desenvolvimento.
O lock abaixo apenas serializa as operações dentro de um mesmo processo; não há
garantias de um banco de dados transacional nem suporte a múltiplos processos escrevendo.
"""

import json
import os
import tempfile
import threading
from pathlib import Path

from pydantic import ValidationError

from app.models import Produto

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO = RAIZ_PROJETO / "data" / "produtos.json"
CAMINHO_ORIGINAL = RAIZ_PROJETO / "data" / "produtos_original.json"


class ErroArmazenamento(Exception):
    """Falha ao ler ou gravar o arquivo de dados."""


def ler_produtos(caminho: Path) -> list[Produto]:
    """Lê e valida os produtos de um arquivo JSON."""
    try:
        dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
        return [Produto.model_validate(item) for item in dados]
    except OSError as exc:
        raise ErroArmazenamento(f"Não foi possível ler o arquivo de dados ({caminho}): {exc}") from exc
    except (ValueError, TypeError, ValidationError) as exc:
        # json.JSONDecodeError e ValidationError herdam de ValueError
        raise ErroArmazenamento(f"O arquivo de dados ({caminho}) é inválido: {exc}") from exc


def gravar_produtos(caminho: Path, produtos: list[Produto]) -> None:
    """Grava os produtos de forma atômica: escreve em arquivo temporário e substitui o original.

    Se algo falhar no meio da gravação, o arquivo original permanece intacto.
    """
    caminho = Path(caminho)
    conteudo = json.dumps([p.model_dump() for p in produtos], ensure_ascii=False, indent=2) + "\n"
    temporario: str | None = None
    try:
        # O temporário fica no mesmo diretório para que os.replace seja atômico.
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=caminho.parent, prefix=caminho.name + ".", suffix=".tmp", delete=False
        ) as arquivo:
            temporario = arquivo.name
            arquivo.write(conteudo)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    except OSError as exc:
        if temporario is not None:
            try:
                os.unlink(temporario)
            except OSError:
                pass
        raise ErroArmazenamento(f"Não foi possível gravar o arquivo de dados ({caminho}): {exc}") from exc


def restaurar_base_original(origem: Path = CAMINHO_ORIGINAL, destino: Path = CAMINHO_PADRAO) -> int:
    """Restaura `destino` com o conteúdo de `origem`. Retorna a quantidade de produtos restaurados.

    A origem é validada antes de qualquer gravação e nunca é modificada.
    """
    produtos = ler_produtos(origem)
    gravar_produtos(destino, produtos)
    return len(produtos)


class ProdutoRepository:
    """Acesso aos produtos persistidos em um arquivo JSON.

    O arquivo é relido a cada operação; assim, uma restauração feita pelo script
    `scripts/reset_data.py` com a API em execução é refletida imediatamente.
    """

    def __init__(self, caminho: Path = CAMINHO_PADRAO) -> None:
        self.caminho = Path(caminho)
        self._lock = threading.Lock()

    def listar(self) -> list[Produto]:
        """Todos os produtos, ordenados pelo código."""
        with self._lock:
            return sorted(ler_produtos(self.caminho), key=lambda p: p.codigo)

    def buscar(self, codigo: str) -> Produto | None:
        return next((p for p in self.listar() if p.codigo == codigo), None)

    def adicionar(self, produto: Produto) -> bool:
        """Insere e persiste o produto. Retorna False (sem gravar) se o código já existir."""
        with self._lock:
            produtos = ler_produtos(self.caminho)
            if any(p.codigo == produto.codigo for p in produtos):
                return False
            produtos.append(produto)
            gravar_produtos(self.caminho, sorted(produtos, key=lambda p: p.codigo))
            return True
