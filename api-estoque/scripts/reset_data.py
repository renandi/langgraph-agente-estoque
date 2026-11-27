"""Restaura a base de dados original (12 produtos fictícios).

ATENÇÃO: sobrescreve data/produtos.json e, portanto, REMOVE os produtos cadastrados
posteriormente via POST /produtos. O arquivo data/produtos_original.json nunca é alterado.

Uso (a partir da raiz do projeto, com o ambiente virtual ativo):

    python scripts/reset_data.py
"""

import argparse
import sys
from pathlib import Path

# Permite executar `python scripts/reset_data.py` sem instalar o projeto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.repository import CAMINHO_ORIGINAL, CAMINHO_PADRAO, ErroArmazenamento, restaurar_base_original  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Restaura data/produtos.json a partir da base original.")
    # Opções avançadas, usadas principalmente pelos testes automatizados.
    parser.add_argument("--origem", type=Path, default=CAMINHO_ORIGINAL, help=argparse.SUPPRESS)
    parser.add_argument("--destino", type=Path, default=CAMINHO_PADRAO, help=argparse.SUPPRESS)
    args = parser.parse_args()

    try:
        total = restaurar_base_original(args.origem, args.destino)
    except ErroArmazenamento as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Base restaurada: {total} produtos gravados em {args.destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
