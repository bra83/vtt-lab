"""Leitor de notas taquigráficas do Senado; preserva procedência e texto público."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

BASE = Path(__file__).parent
HOST = "www25.senado.leg.br"
PREFIX = "/web/atividade/notas-taquigraficas/-/notas/r/"

def catalogo():
    return json.loads((BASE / "fontes_reais.json").read_text(encoding="utf-8"))

def extrair_html(html: str) -> str:
    soup=BeautifulSoup(html,"html.parser")
    for tag in soup(["script","style","noscript","nav","footer","header"]):
        tag.decompose()
    # The Senate publishes time-stamped speech turns as HTML table rows.
    candidates=[]
    for table in soup.find_all("table"):
        lines=[]
        for row in table.select("tr"):
            cells=row.find_all(["td","th"],recursive=False)
            if len(cells)<2:
                continue
            first=cells[0].get_text(" ",strip=True)
            spoken=cells[-1].get_text(" ",strip=True)
            if len(spoken)<20:
                continue
            if re.search(r"\d{1,2}:\d{2}",first):
                lines.append(first+" | "+spoken)
            else:
                lines.append(spoken)
        if lines:
            candidates.append("\n\n".join(lines))
    if candidates:
        result=max(candidates,key=len)
        if len(result)>=600:
            return result
    # Fallback for alternate Senate HTML, but do not return a bare navigation menu.
    main=soup.find("main") or soup.find(id=re.compile("conteudo|content",re.I)) or soup.body
    result=main.get_text("\n",strip=True) if main else ""
    anchor=result.find("Texto com revisão")
    if anchor>=0:
        result=result[anchor+len("Texto com revisão"):]
    result=re.sub(r"\n{3,}","\n\n",result)
    if len(result)<600 or not re.search(r"\b(?:O SR\.|A SRA\.|O SENADOR|A SENADORA)\b",result,re.I):
        raise ValueError("Página sem transcrição identificável")
    return result

def obter_texto(item, timeout=30):
    url=item["url"]
    parsed=urlparse(url)
    if parsed.scheme!="https" or parsed.netloc!=HOST or not parsed.path.startswith(PREFIX):
        raise ValueError("Origem não autorizada")
    r=requests.get(url,timeout=timeout,headers={"User-Agent":"Mozilla/5.0 (compatible; LaboratorioForense/0.3; public research)"})
    r.raise_for_status()
    r.encoding=r.apparent_encoding or "utf-8"
    return extrair_html(r.text)

def hash_documento(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()
