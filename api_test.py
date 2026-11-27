import os
import httpx

# Verificando se a API está acessível e retorna corretamente o produto de exemplo
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
CODIGO_DEMO = os.getenv("PRODUTO_DEMO", "PRD-001")
TIMEOUT = 5.0

resposta = httpx.get(f"{API_URL}/produtos/{CODIGO_DEMO}", timeout=TIMEOUT)
print("HTTP:", resposta.status_code)
resposta.raise_for_status()
produto_bruto = resposta.json()
print("Campos retornados:", list(produto_bruto))
print("JSON recebido:")
import json
print(json.dumps(produto_bruto, ensure_ascii=False, indent=2, default=str))