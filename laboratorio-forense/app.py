import io
import re
import unicodedata
import pandas as pd
import streamlit as st
from pypdf import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

st.set_page_config(page_title="Laboratório Forense", page_icon="🔎", layout="wide")
st.title("Laboratório Forense")
st.caption("Análise exploratória de depoimentos · processamento local")

PATTERNS = {
    "Autocorreção": r"\b(quer dizer|ou melhor|na verdade|corrigindo)\b",
    "Incerteza": r"\b(talvez|acho que|não lembro|nao lembro|não tenho certeza|parece que)\b",
    "Negação": r"\b(não|nao|nunca|jamais|ninguém|ninguem)\b",
    "Tempo": r"\b(\d{1,2}[:h]\d{2}|ontem|hoje|amanhã|amanha|antes|depois|horas?)\b",
}
def read_file(upload):
    if upload is None:
        return ""
    raw = upload.getvalue()
    if upload.name.lower().endswith(".txt"):
        return raw.decode("utf-8-sig", errors="replace")
    if upload.name.lower().endswith(".pdf"):
        pdf = PdfReader(io.BytesIO(raw))
        return "\n".join(f"[Página {i+1}]\n" + (p.extract_text() or "") for i,p in enumerate(pdf.pages))
    if upload.name.lower().endswith(".docx"):
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""
def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.strip()) >= 12]
def analyze(text, label):
    rows = []
    for i,s in enumerate(sentences(text),1):
        marks = [name for name,pat in PATTERNS.items() if re.search(pat,s,re.I)]
        if marks:
            rows.append({"Origem":label,"Trecho":i,"Marcadores":", ".join(marks),"Texto":s})
    return rows
def comparisons(a,b):
    aa,bb=sentences(a),sentences(b)
    if not aa or not bb: return []
    vectorizer=TfidfVectorizer(ngram_range=(1,2),strip_accents="unicode",max_features=30000)
    mat=vectorizer.fit_transform(aa+bb)
    scores=cosine_similarity(mat[:len(aa)],mat[len(aa):])
    pairs=[]
    for i in range(len(aa)):
        j=int(scores[i].argmax())
        score=float(scores[i,j])
        if score>=0.15:
            pairs.append({"Trecho A":aa[i],"Trecho B":bb[j],"Similaridade":round(score,3)})
    return sorted(pairs,key=lambda x:-x["Similaridade"])
left,right=st.columns(2)
with left:
    fa=st.file_uploader("Depoimento A",type=["txt","pdf","docx"],key="a")
    ta=st.text_area("Texto A",value=read_file(fa),height=240)
with right:
    fb=st.file_uploader("Depoimento B",type=["txt","pdf","docx"],key="b")
    tb=st.text_area("Texto B",value=read_file(fb),height=240)
if st.button("Analisar depoimentos",type="primary"):
    if not (ta.strip() or tb.strip()):
        st.warning("Insira pelo menos um depoimento.")
    else:
        rows=analyze(ta,"A")+analyze(tb,"B")
        st.subheader("Trechos para revisão")
        df=pd.DataFrame(rows,columns=["Origem","Trecho","Marcadores","Texto"])
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Exportar CSV",df.to_csv(index=False).encode("utf-8-sig"),file_name="achados.csv",mime="text/csv")
        if ta.strip() and tb.strip():
            st.subheader("Correspondências entre depoimentos")
            st.caption("Similaridade lexical TF-IDF; requer avaliação humana para identificar divergências.")
            st.dataframe(pd.DataFrame(comparisons(ta,tb)),use_container_width=True,hide_index=True)
