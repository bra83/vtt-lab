"""Catálogo de transcrições oficiais, baixadas sob demanda e não alteradas."""
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

def catalogo():
    return json.loads((Path(__file__).parent / "fontes_reais.json").read_text(encoding="utf-8"))

def obter_texto(item, timeout=25):
    url = item["url"]
    if not url.startswith("https://www25.senado.leg.br/web/atividade/notas-taquigraficas/"):
        raise ValueError("Origem não autorizada")
    response = requests.get(url, timeout=timeout, headers={"User-Agent":"LaboratorioForenseResearch/0.2"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script","style","nav","footer"]):
        tag.decompose()
    texto = (soup.select_one("main") or soup).get_text("\n",strip=True)
    if len(texto) < 1000:
        raise ValueError("Transcrição insuficiente; verifique a fonte")
    return texto
