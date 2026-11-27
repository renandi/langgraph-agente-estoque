"""Testes automatizados da API de Estoque.

Todos os testes que gravam dados usam uma cópia temporária da base original
(fixture `caminho_dados`); o arquivo data/produtos.json nunca é modificado.
"""

import json
import shutil
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repository import (
    CAMINHO_ORIGINAL,
    CAMINHO_PADRAO,
    RAIZ_PROJETO,
    ProdutoRepository,
    restaurar_base_original,
)

CAMPOS = {
    "codigo": str,
    "nome": str,
    "categoria": str,
    "quantidade_atual": int,
    "estoque_minimo": int,
    "unidade": str,
}

NOVO = {
    "codigo": "PRD-020",
    "nome": "Teclado mecânico",
    "categoria": "Periféricos",
    "quantidade_atual": 15,
    "estoque_minimo": 5,
    "unidade": "un",
}


@pytest.fixture
def caminho_dados(tmp_path):
    """Cópia temporária da base original: cada teste começa com os 12 produtos iniciais."""
    destino = tmp_path / "produtos.json"
    shutil.copy(CAMINHO_ORIGINAL, destino)
    return destino


@pytest.fixture
def client(caminho_dados):
    return TestClient(create_app(caminho_dados))


# ------------------------------------------------------------------ 1. health


def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "service": "api-estoque", "version": "1.0.0"}


# ------------------------------------------------------------------ 2. listagem


def test_listar_produtos(client):
    resposta = client.get("/produtos")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["total"] == 12
    assert len(corpo["produtos"]) == 12


def test_listagem_ordenada_pelo_codigo_e_sem_codigo_reservado(client):
    codigos = [p["codigo"] for p in client.get("/produtos").json()["produtos"]]
    assert codigos == sorted(codigos)
    assert codigos == [f"PRD-{n:03d}" for n in range(1, 13)]
    assert "PRD-503" not in codigos


def test_filtrar_por_categoria(client):
    corpo = client.get("/produtos", params={"categoria": "periféricos"}).json()
    assert corpo["total"] == 3
    assert {p["categoria"] for p in corpo["produtos"]} == {"Periféricos"}


def test_filtrar_por_categoria_inexistente_retorna_lista_vazia(client):
    resposta = client.get("/produtos", params={"categoria": "Inexistente"})
    assert resposta.status_code == 200
    assert resposta.json() == {"total": 0, "produtos": []}


# ------------------------------------------------------------------ 3, 4, 5, 6. consulta e falhas


def test_consultar_produto_existente(client):
    resposta = client.get("/produtos/PRD-001")
    assert resposta.status_code == 200
    assert resposta.json() == {
        "codigo": "PRD-001",
        "nome": "Mouse sem fio",
        "categoria": "Periféricos",
        "quantidade_atual": 5,
        "estoque_minimo": 10,
        "unidade": "un",
    }


def test_consultar_produto_inexistente(client):
    resposta = client.get("/produtos/PRD-999")
    assert resposta.status_code == 404
    assert resposta.json() == {"erro": "produto_nao_encontrado", "mensagem": "Produto não encontrado."}


@pytest.mark.parametrize("codigo", ["ABC-001", "PRD-1", "PRD-0001", "prd-001", "PRD-00A", "PRD_001"])
def test_codigo_malformado_retorna_422(client, codigo):
    resposta = client.get(f"/produtos/{codigo}")
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["erro"] == "codigo_invalido"
    assert corpo["mensagem"]
    assert corpo["detail"][0]["loc"] == ["path", "codigo"]  # `detail` padrão do FastAPI preservado


def test_indisponibilidade_simulada_retorna_503(client):
    for _ in range(2):  # determinístico: sempre o mesmo resultado
        resposta = client.get("/produtos/PRD-503")
        assert resposta.status_code == 503
        assert resposta.json() == {
            "erro": "servico_indisponivel",
            "mensagem": "Serviço temporariamente indisponível. Tente novamente mais tarde.",
        }


def test_identificadores_de_erro_sao_distintos(client):
    client.post("/produtos", json=NOVO)
    erros = {
        client.get("/produtos/PRD-999").json()["erro"],
        client.get("/produtos/xx").json()["erro"],
        client.get("/produtos/PRD-503").json()["erro"],
        client.post("/produtos", json=NOVO).json()["erro"],  # duplicado
    }
    assert erros == {"produto_nao_encontrado", "codigo_invalido", "servico_indisponivel", "produto_duplicado"}


# ------------------------------------------------------------------ 7. consistência de campos e tipos


def test_campos_e_tipos_dos_produtos(client):
    for produto in client.get("/produtos").json()["produtos"]:
        assert set(produto) == set(CAMPOS)
        for campo, tipo in CAMPOS.items():
            assert type(produto[campo]) is tipo, f"{produto['codigo']}.{campo}"
        assert produto["quantidade_atual"] >= 0
        assert produto["estoque_minimo"] >= 0


def test_base_inicial_tem_todas_as_situacoes_de_estoque(client):
    """Garante que os dados cobrem os casos que os estudantes precisarão distinguir."""
    produtos = client.get("/produtos").json()["produtos"]
    assert any(p["quantidade_atual"] == 0 for p in produtos)
    assert any(0 < p["quantidade_atual"] < p["estoque_minimo"] for p in produtos)
    assert any(p["quantidade_atual"] == p["estoque_minimo"] > 0 for p in produtos)
    assert any(p["quantidade_atual"] > p["estoque_minimo"] for p in produtos)


def test_categorias(client):
    corpo = client.get("/categorias").json()
    assert corpo["total"] == len(corpo["categorias"]) == 8
    assert corpo["categorias"] == sorted(corpo["categorias"], key=str.casefold)
    assert "Periféricos" in corpo["categorias"]


# ------------------------------------------------------------------ 8, 9. cadastro


def test_cadastro_bem_sucedido(client):
    resposta = client.post("/produtos", json=NOVO)
    assert resposta.status_code == 201
    assert resposta.json() == NOVO


def test_consulta_apos_cadastro(client):
    client.post("/produtos", json=NOVO)

    assert client.get("/produtos/PRD-020").json() == NOVO
    corpo = client.get("/produtos").json()
    assert corpo["total"] == 13
    assert corpo["produtos"][-1] == NOVO


def test_categoria_nova_aparece_em_categorias(client):
    client.post("/produtos", json={**NOVO, "categoria": "Redes"})
    assert "Redes" in client.get("/categorias").json()["categorias"]


def test_campos_textuais_sao_normalizados(client):
    corpo = {**NOVO, "codigo": " PRD-030 ", "nome": "  Teclado mecânico  ", "categoria": " Periféricos ", "unidade": " un "}
    resposta = client.post("/produtos", json=corpo)
    assert resposta.status_code == 201
    assert resposta.json() == {**NOVO, "codigo": "PRD-030"}


# ------------------------------------------------------------------ 10, 11, 12, 13. cadastro inválido


def test_cadastro_duplicado_retorna_409(client):
    resposta = client.post("/produtos", json={**NOVO, "codigo": "PRD-001"})
    assert resposta.status_code == 409
    assert resposta.json()["erro"] == "produto_duplicado"
    # a base não foi alterada
    assert client.get("/produtos").json()["total"] == 12
    assert client.get("/produtos/PRD-001").json()["nome"] == "Mouse sem fio"


def test_segundo_cadastro_do_mesmo_codigo_retorna_409(client):
    assert client.post("/produtos", json=NOVO).status_code == 201
    assert client.post("/produtos", json=NOVO).status_code == 409


def test_cadastro_com_quantidade_negativa(client):
    resposta = client.post("/produtos", json={**NOVO, "quantidade_atual": -1})
    assert resposta.status_code == 422
    corpo = resposta.json()
    assert corpo["erro"] == "dados_invalidos"
    assert "quantidade_atual" in corpo["mensagem"]
    assert client.get("/produtos/PRD-020").status_code == 404


def test_cadastro_com_campo_obrigatorio_ausente(client):
    sem_nome = {k: v for k, v in NOVO.items() if k != "nome"}
    resposta = client.post("/produtos", json=sem_nome)
    assert resposta.status_code == 422
    assert resposta.json()["detail"][0]["loc"] == ["body", "nome"]


def test_cadastro_com_corpo_ausente(client):
    assert client.post("/produtos").status_code == 422


def test_cadastro_rejeita_codigo_reservado(client):
    resposta = client.post("/produtos", json={**NOVO, "codigo": "PRD-503"})
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "dados_invalidos"
    # continua simulando indisponibilidade e não aparece entre os produtos reais
    assert client.get("/produtos/PRD-503").status_code == 503
    assert "PRD-503" not in [p["codigo"] for p in client.get("/produtos").json()["produtos"]]


@pytest.mark.parametrize(
    "alteracao",
    [
        {"codigo": "PRD-2"},
        {"codigo": "ABC-020"},
        {"nome": ""},
        {"nome": "   "},
        {"categoria": ""},
        {"unidade": "  "},
        {"estoque_minimo": -5},
        {"quantidade_atual": "15"},  # texto não é convertido em inteiro
        {"quantidade_atual": 15.5},
        {"quantidade_atual": True},
        {"estoque_minimo": None},
        {"nome": 123},
        {"campo_extra": "x"},
    ],
)
def test_cadastro_com_dados_invalidos(client, alteracao):
    resposta = client.post("/produtos", json={**NOVO, **alteracao})
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "dados_invalidos"
    assert client.get("/produtos").json()["total"] == 12


def test_quantidade_zero_e_valida(client):
    resposta = client.post("/produtos", json={**NOVO, "quantidade_atual": 0, "estoque_minimo": 0})
    assert resposta.status_code == 201


# ------------------------------------------------------------------ 14. persistência


def test_persistencia_apos_recarregar_repositorio(caminho_dados):
    primeira_instancia = TestClient(create_app(caminho_dados))
    assert primeira_instancia.post("/produtos", json=NOVO).status_code == 201

    # Repositório novo, lendo o mesmo arquivo (equivale a reiniciar a API)
    assert ProdutoRepository(caminho_dados).buscar("PRD-020").model_dump() == NOVO

    segunda_instancia = TestClient(create_app(caminho_dados))
    assert segunda_instancia.get("/produtos/PRD-020").json() == NOVO
    assert segunda_instancia.get("/produtos").json()["total"] == 13


def test_arquivo_json_permanece_valido_e_sem_temporarios(client, caminho_dados):
    client.post("/produtos", json=NOVO)
    dados = json.loads(caminho_dados.read_text(encoding="utf-8"))
    assert len(dados) == 13
    assert {p["codigo"] for p in dados} >= {"PRD-001", "PRD-020"}
    assert [arq.name for arq in caminho_dados.parent.iterdir()] == ["produtos.json"]


def test_arquivo_corrompido_retorna_500_estruturado(caminho_dados):
    caminho_dados.write_text("{ isto não é json", encoding="utf-8")
    resposta = TestClient(create_app(caminho_dados)).get("/produtos")
    assert resposta.status_code == 500
    assert resposta.json()["erro"] == "erro_armazenamento"


# ------------------------------------------------------------------ 15. restauração


def test_restauracao_da_base_original(client, caminho_dados):
    client.post("/produtos", json=NOVO)
    assert client.get("/produtos").json()["total"] == 13

    total = restaurar_base_original(CAMINHO_ORIGINAL, caminho_dados)

    assert total == 12
    assert client.get("/produtos").json()["total"] == 12  # a API em execução enxerga a restauração
    assert client.get("/produtos/PRD-020").status_code == 404
    assert caminho_dados.read_text(encoding="utf-8") == CAMINHO_ORIGINAL.read_text(encoding="utf-8")


def test_script_reset_data(client, caminho_dados):
    client.post("/produtos", json=NOVO)
    original_antes = CAMINHO_ORIGINAL.read_bytes()

    resultado = subprocess.run(
        [sys.executable, "scripts/reset_data.py", "--destino", str(caminho_dados)],
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 0, resultado.stderr
    assert "12 produtos" in resultado.stdout
    assert client.get("/produtos").json()["total"] == 12
    assert CAMINHO_ORIGINAL.read_bytes() == original_antes  # a base original nunca é modificada


def test_restauracao_nao_altera_destino_se_origem_for_invalida(tmp_path, caminho_dados):
    origem_invalida = tmp_path / "invalido.json"
    origem_invalida.write_text("[{\"codigo\": \"errado\"}]", encoding="utf-8")
    antes = caminho_dados.read_bytes()

    resultado = subprocess.run(
        [sys.executable, "scripts/reset_data.py", "--origem", str(origem_invalida), "--destino", str(caminho_dados)],
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
    )

    assert resultado.returncode == 1
    assert caminho_dados.read_bytes() == antes


def test_base_original_e_a_base_inicial_tem_12_produtos():
    original = json.loads(CAMINHO_ORIGINAL.read_text(encoding="utf-8"))
    assert len(original) == 12
    assert len({p["codigo"] for p in original}) == 12


# ------------------------------------------------------------------ 16. isolamento


def test_testes_nao_alteram_a_base_principal(client):
    principal_antes = CAMINHO_PADRAO.read_bytes()
    original_antes = CAMINHO_ORIGINAL.read_bytes()

    assert client.post("/produtos", json=NOVO).status_code == 201
    assert client.post("/produtos", json={**NOVO, "codigo": "PRD-021"}).status_code == 201

    assert CAMINHO_PADRAO.read_bytes() == principal_antes
    assert CAMINHO_ORIGINAL.read_bytes() == original_antes


def test_cada_teste_comeca_com_a_base_limpa(client):
    # PRD-020 foi cadastrado em outros testes; aqui ele não deve existir.
    assert client.get("/produtos/PRD-020").status_code == 404
    assert client.get("/produtos").json()["total"] == 12


# ------------------------------------------------------------------ documentação


@pytest.mark.parametrize("caminho", ["/docs", "/redoc", "/openapi.json"])
def test_documentacao_disponivel(client, caminho):
    assert client.get(caminho).status_code == 200


def test_schema_openapi(client):
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "API de Estoque — Projeto Avaliativo de Agentes de IA"
    assert schema["info"]["version"] == "1.0.0"
    assert set(schema["paths"]) == {"/health", "/produtos", "/produtos/{codigo}", "/categorias"}
    assert set(schema["paths"]["/produtos"]) == {"get", "post"}  # sem PUT/PATCH/DELETE
    assert set(schema["paths"]["/produtos"]["post"]["responses"]) >= {"201", "409", "422"}
    assert set(schema["paths"]["/produtos/{codigo}"]["get"]["responses"]) >= {"200", "404", "422", "503"}
