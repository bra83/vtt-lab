"""Estudos criminais reais em modalidade cega.

Obtém registros de interrogatório publicados pelo TJAL (e-SAJ) e exibe apenas
a fala indireta da parte interrogada, omitindo nomes e andamento do processo.
Não inclui texto inventado ou declarações de terceiros como fala do investigado.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
import unicodedata
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

@dataclass(frozen=True)
class Caso:
    id: str
    titulo: str
    contexto: str
    perguntas: tuple[str,...]
    fonte: str
    aliases: tuple[tuple[str,str],...]
    aviso: str = "O registro é um termo judicial em discurso indireto, não uma transcrição fonética ou uma gravação."

CASOS = (
    Caso(
        id="CR-01",
        titulo="Caso CR-01 — Crime contra a vida",
        contexto=(
            "Em um município do interior de Alagoas, uma mulher morreu após ser atingida "
            "por disparos de arma de fogo durante um conflito ocorrido nas proximidades de "
            "uma residência. A investigação reuniu relatos sobre a sequência dos acontecimentos, "
            "a presença de pessoas no local e os deslocamentos posteriores. "
            "Você receberá o interrogatório judicial de uma pessoa acusada."
        ),
        perguntas=(
            "Reconstrua a sequência temporal anterior, durante e posterior aos disparos.",
            "Separe conhecimento direto, informações recebidas de terceiros e deduções do depoente.",
            "Identifique afirmações a confirmar com vestígios ou testemunhos independentes.",
            "Registre possíveis explicações alternativas para divergências aparentes.",
        ),
        fonte="https://www2.tjal.jus.br/cpopg/show.do?processo.codigo=1G00008PB0000&processo.foro=52",
        aliases=(
            ("Josedi Luiz da Penha", "INTERROGADO"),
            ("Maria José Gonçalves da Silva", "VÍTIMA"),
            ("Rosangela", "Pessoa A"), ("Rosângela", "Pessoa A"),
            ("Eliane", "Pessoa B"), ("Antonio", "Pessoa C"), ("Antônio", "Pessoa C"),
            ("Geraldo", "Pessoa D"), ("Dona Deusa", "Pessoa E"),
            ("Valparaíso", "Local A"), ("Várzea Bonita", "Local B"),
            ("Ibateguara", "Local C"), ("Alto Buzerá", "Local D"),
            ("São José da Laje", "Local E"), ("Usina Serra Grande", "Local F"),
        ),
    ),
    Caso(
        id="CR-02",
        titulo="Caso CR-02 — Conflito com vítimas fatais",
        contexto=(
            "Duas pessoas foram vítimas de um crime violento em uma cidade do interior de Alagoas. "
            "A investigação relacionou depoimentos sobre a localização de envolvidos na noite dos fatos, "
            "deslocamentos entre localidades e eventuais conflitos anteriores. "
            "Você terá acesso à versão apresentada por uma das pessoas acusadas, "
            "sem consultar inicialmente as conclusões judiciais."
        ),
        perguntas=(
            "Organize os pontos verificáveis do álibi e respectivos horários.",
            "Diferencie relatos do que foi visto de fatos conhecidos somente depois.",
            "Liste perguntas de acompanhamento que reduziriam ambiguidades.",
            "Indique que provas independentes poderiam confirmar ou refutar cada afirmação.",
        ),
        fonte="https://www2.tjal.jus.br/cpopg/show.do?processo.codigo=0T00000NP0000&processo.foro=33",
        aliases=(
            ("José Soares de Souza", "INTERROGADO"), ("Cristiano Alexandre da Silva", "Pessoa A"),
            ("Cristiano Wanderley da Silva", "Pessoa A"), ("Zitinho", "Pessoa E"),
            ("Adolfo Manoel", "Vítima A"), ("Marcos André", "Pessoa F"),
            ("Maria Luciene", "Pessoa I"), ("Neno", "Pessoa G"), ("Francisco", "Pessoa H"),
            ("Rua São Pedro", "Rua A"), ("Rua João Cassiano", "Rua B"),
            ("Rua Erasmo Porangaba", "Rua C"),
            ("Cristiano", "Pessoa A"), ("Adolfo", "Vítima A"), ("Márcio", "Vítima B"),
            ("Marcio", "Vítima B"), ("André", "Pessoa B"), ("Fabiana", "Pessoa C"),
            ("João Gabriel", "Pessoa D"),
            ("Paulo Jacinto", "Local A"), ("Maceió", "Local B"),
            ("Sítio Fernandes", "Local C"), ("Sitio Fernandes", "Local C"),
        ),
    ),
)

def by_id(id: str) -> Caso:
    return next(c for c in CASOS if c.id == id)

def limpar(texto: str) -> str:
    return re.sub(r"\s+"," ",texto or "").strip()

def extrair_interrogatorio(html: str) -> str:
    """Encontra um bloco PERGUNTADO/RESPONDEU até o encerramento do termo.

    Movimentações repetidas são ignoradas. Rejeita páginas sem texto substancial.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript","nav","footer","header"]):
        tag.decompose()
    body = limpar(soup.get_text(" ",strip=True))
    # Conversational portion begins at a judicial question, avoiding identification
    # and procedural outcomes which occur elsewhere in the case docket.
    starts = list(re.finditer(r"PERGUNTADO\s*:\s*(?:se\s+é\s+verdadeira|se,\s*em\s+não\s+sendo\s+verdadeira|onde\s+estava)", body, re.I))
    candidates=[]
    for m in starts:
        # Limit to one interrogation, never append adjacent rulings or testimony.
        segment=body[m.start():m.start()+25_000]
        boundaries=[i for i in (
            re.search(r"\bNada mais sendo dito\b",segment,re.I),
            re.search(r"\bmandou o MM\.\s*Juiz encerrar\b",segment,re.I),
            re.search(r"\bNada mais havendo\b",segment,re.I),
            re.search(r"\bOBS\.?\s*:\s*Art\.?\s*189\b",segment,re.I),
            re.search(r"\bEm seguida pelo M\.M\.",segment,re.I),
            re.search(r"\bA seguir o MM\.",segment,re.I),
        ) if i is not None]
        if boundaries:
            segment=segment[:min(x.start() for x in boundaries)]
        # If another section begins but the first isn't closed, stop, not concatenate.
        for phrase in (r"\bSENTENÇA\b",r"\bRELATÓRIO\b",r"\bDISPOSITIVO\b",
                       r"\bDECISÃO DE PRONÚNCIA\b"):
            p=re.search(phrase,segment[300:],re.I)
            if p is not None:
                segment=segment[:300+p.start()]
        if len(segment)>=850 and len(re.findall(r"\bRESPONDEU\s*:",segment,re.I))>=5:
            # Prefer segments that end at an official interrogation delimiter.
            candidates.append((bool(boundaries),segment))
    if not candidates:
        raise ValueError("O documento judicial não contém interrogatório isolável e verificável.")
    # Prefer fuller records, capped to avoid incidental documents. Same interrogatório
    # may appear multiple times on the process page.
    result=max(candidates,key=lambda item:(item[0],len(item[1])))[1]
    if len(result)>=20_000:
        raise ValueError("Não foi possível isolar com segurança um único interrogatório.")
    result=re.sub(r"(?i)(?<!\w)(PERGUNTADO\s*:)",r"\n\n\1",result)
    result=re.sub(r"(?i)(?<!\w)(RESPONDEU\s*:)",r"\n\1",result)
    result=re.sub(r"\n{3,}","\n\n",result).strip()
    return result

def anonimizar(texto: str, caso: Caso) -> str:
    """Substituição ordenada: preserva relações entre pseudônimos e lugares."""
    for original, alias in sorted(caso.aliases,key=lambda row:-len(row[0])):
        texto=re.sub(r"(?i)(?<!\w)"+re.escape(original)+r"(?!\w)",alias,texto)
    # No change to timings, quantities, negations, names of object types or claims.
    return texto

def obter_interrogatorio(caso: Caso,timeout=35) -> str:
    parsed=urlparse(caso.fonte)
    if parsed.scheme!="https" or parsed.netloc!="www2.tjal.jus.br" or parsed.path!="/cpopg/show.do":
        raise ValueError("Fonte judicial não autorizada")
    r=requests.get(caso.fonte,timeout=timeout,
                   headers={"User-Agent":"Mozilla/5.0 (compatible; LaboratorioForense/0.4)"})
    r.raise_for_status()
    r.encoding=r.apparent_encoding or "utf-8"
    texto=extrair_interrogatorio(r.text)
    texto=anonimizar(texto,caso)
    if len(texto)<850:
        raise ValueError("Interrogatório extraído é insuficiente")
    return texto


def somente_respostas(interrogatorio: str) -> str:
    """Retorna somente respostas atribuídas ao interrogado, mantendo a ordem.

    Perguntas judiciais não entram na extração de marcadores linguísticos.
    Os códigos numéricos indicam a posição da resposta no termo integral.
    """
    blocos = re.findall(
        r"\bRESPONDEU\s*:\s*(.*?)(?=\s*PERGUNTADO\s*:|\Z)",
        interrogatorio,
        flags=re.I | re.S,
    )
    falas=[]
    for indice, bloco in enumerate(blocos, start=1):
        fala=limpar(bloco)
        if fala:
            falas.append(f"Resposta {indice:02d}. {fala}")
    if not falas:
        raise ValueError("Nenhuma resposta do interrogado identificada no documento.")
    return "\n\n".join(falas)
