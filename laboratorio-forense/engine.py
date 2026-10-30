"""Motor determinístico de triagem documental, com rastreabilidade dos achados."""
from __future__ import annotations
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PATTERNS = {
    "Incerteza": r"\b(?:talvez|possivelmente|provavelmente|acho que|creio que|pelo que lembro|se não me engano|não (?:me )?lembro|não tenho certeza|parece que)\b",
    "Reformulação": r"\b(?:ou melhor|quer dizer|na verdade|corrigindo|retificando|me corrijo)\b",
    "Negação": r"\b(?:não|nunca|jamais|ninguém|nada|nem)\b",
    "Afirmação enfática": r"\b(?:com certeza|absolutamente|sem dúvida|tenho certeza|categoricamente)\b",
    "Referência temporal": r"\b(?:ontem|hoje|amanhã|antes|depois|naquela noite|naquele dia|pela manhã|à tarde|às \d{1,2}|por volta de)\b",
}
TIME_RE = re.compile(r"(?<!\d)(?:[01]?\d|2[0-3])\s*(?:h|:)\s*[0-5]\d(?!\d)|\b(?:[01]?\d|2[0-3])\s*horas?\b", re.I)
NUM_RE = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)")
NEG_RE = re.compile(r"\b(?:não|nunca|jamais|ninguém|nem)\b", re.I)
SPEAKER_RE = re.compile(r"(?:^|\n)\s*(?:O SR\.|A SRA\.|O SENADOR|A SENADORA|A TESTEMUNHA|A DEPOENTE|O DEPOENTE)\s+[^:\n]{2,100}?\s*[-–:]", re.I)
SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ú0-9])|\n{2,}")

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))

def fragments(text: str, limit: int = 280) -> list[dict]:
    """Preserva trecho e posição aproximada; evita comparações quadráticas gigantes."""
    source = (text or "").strip()
    if not source:
        return []
    source = source[:800_000]
    pieces = []
    for match in SPLIT_RE.finditer(source):
        start = 0 if not pieces else 0  # unused: split positions below
    last = 0
    chunks = []
    for match in SPLIT_RE.finditer(source):
        raw = source[last:match.start()]
        if raw.strip():
            chunks.append((last, raw.strip()))
        last = match.end()
    if source[last:].strip():
        chunks.append((last, source[last:].strip()))
    # Long paragraphs and transcript turns also receive length-bounded fragments.
    for start, chunk in chunks:
        for n in range(0, len(chunk), 720):
            part = chunk[n:n + 720].strip()
            if len(part) >= 18:
                pieces.append({"id": len(pieces)+1, "inicio": start+n, "texto": part})
            if len(pieces) >= limit:
                return pieces
    return pieces

def analyze(text: str, origin: str = "A", limit: int = 280) -> list[dict]:
    result = []
    for part in fragments(text, limit):
        p = part["texto"]
        matches = [name for name,pattern in PATTERNS.items() if re.search(pattern, p, re.I)]
        times = TIME_RE.findall(p)
        if times and "Referência temporal" not in matches:
            matches.append("Referência temporal")
        if matches:
            result.append({"Origem": origin, "Trecho": part["id"],
                "Posição": part["inicio"], "Categorias": ", ".join(matches),
                "Horários": ", ".join(times[:8]), "Texto": p})
    return result

def times(text: str, origin: str) -> list[dict]:
    rows=[]
    for p in fragments(text):
        found=TIME_RE.findall(p["texto"])
        for value in found[:8]:
            rows.append({"Origem": origin,"Trecho":p["id"],"Horário":value,"Contexto":p["texto"][:360]})
    return rows

def compare(a: str, b: str, threshold: float = .18, limit: int = 220) -> list[dict]:
    a_parts,b_parts=fragments(a,limit),fragments(b,limit)
    if not a_parts or not b_parts:
        return []
    all_parts=[x["texto"] for x in a_parts+b_parts]
    vec=TfidfVectorizer(strip_accents="unicode",ngram_range=(1,2),min_df=1,max_features=45000)
    try:
        matrix=vec.fit_transform(all_parts)
    except ValueError:
        return []
    # Limit controlled by fragment cap.
    sims=cosine_similarity(matrix[:len(a_parts)],matrix[len(a_parts):])
    seen=set()
    rows=[]
    for ai, p in enumerate(a_parts):
        candidates=sims[ai].argsort()[-3:][::-1]
        for j in candidates:
            score=float(sims[ai,j])
            if score < threshold or (ai,int(j)) in seen:
                continue
            seen.add((ai,int(j)))
            q=b_parts[int(j)]
            x,y=p["texto"],q["texto"]
            a_times={normalize(t.replace(" ","")) for t in TIME_RE.findall(x)}
            b_times={normalize(t.replace(" ","")) for t in TIME_RE.findall(y)}
            a_nums={n for n in NUM_RE.findall(x) if len(n)>0}
            b_nums={n for n in NUM_RE.findall(y) if len(n)>0}
            flags=[]
            if bool(NEG_RE.search(x)) != bool(NEG_RE.search(y)):
                flags.append("Negação divergente")
            if a_times and b_times and a_times != b_times:
                flags.append("Horários diferentes")
            if a_nums and b_nums and a_nums != b_nums:
                flags.append("Números diferentes")
            if not flags:
                flags.append("Trechos relacionados")
            rows.append({"Trecho A":p["id"],"Trecho B":q["id"],
                "Similaridade":round(score,3),"Sinais":", ".join(flags),
                "Texto A":x,"Texto B":y})
    return sorted(rows,key=lambda r:(
        not any(s in r["Sinais"] for s in ("divergente","diferentes")),
        -r["Similaridade"]))[:150]

def summary(a: str, b: str) -> dict:
    fa,fb=fragments(a),fragments(b)
    return {"Trechos A":len(fa),"Trechos B":len(fb),
        "Palavras A":len(a.split()),"Palavras B":len(b.split()),
        "Marcadores A":len(analyze(a,"A")),"Marcadores B":len(analyze(b,"B"))}
