"""Laboratório Forense — estudo documental de transcrições públicas brasileiras."""
from __future__ import annotations
import io
import json
import re
import importlib.util
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
from pypdf import PdfReader
from docx import Document
from engine import analyze, compare, fragments, times, summary
from fontes import catalogo, obter_texto, hash_documento

st.set_page_config(page_title="Laboratório Forense", page_icon="🔎",layout="wide")
st.markdown("""
<style>
.block-container {max-width:1450px;padding-top:1.5rem}
h1,h2,h3 {letter-spacing:-.035em}
[data-testid="stMetric"] {padding:12px;border:1px solid #8c91972e;border-radius:10px}
div[data-testid="stDataFrame"] {border-radius:10px}
</style>""",unsafe_allow_html=True)

@st.cache_data(ttl=3600,show_spinner=False)
def load_source(source):
    return obter_texto(source)

def read_upload(up):
    if up is None: return ""
    raw=up.getvalue()
    if len(raw)>15_000_000:
        raise ValueError("Arquivo excede 15 MB.")
    ext=up.name.lower().rsplit(".",1)[-1]
    if ext=="txt":
        return raw.decode("utf-8-sig",errors="replace")
    if ext=="pdf":
        pdf=PdfReader(io.BytesIO(raw))
        return "\n".join(f"[Página {i+1}]\n"+(p.extract_text() or "") for i,p in enumerate(pdf.pages))
    if ext=="docx":
        return "\n".join(p.text for p in Document(io.BytesIO(raw)).paragraphs)
    raise ValueError("Formato não suportado")

def put_document(slot, text, record=None):
    st.session_state["text_"+slot]=text
    st.session_state["origin_"+slot]=record or {"titulo":"Texto fornecido pelo usuário","url":None}

def document_box(slot):
    up=st.file_uploader("Importar TXT, PDF textual ou DOCX",type=["txt","pdf","docx"],key="upload_"+slot)
    if up is not None:
        signature=(up.name,len(up.getvalue()),hash_documento(up.getvalue().hex()))
        if st.session_state.get("uploaded_"+slot)!=signature:
            try:
                put_document(slot,read_upload(up))
                st.session_state["uploaded_"+slot]=signature
            except Exception as exc:
                st.error(f"Não foi possível ler o arquivo: {exc}")
    return st.text_area("Conteúdo do documento "+slot,key="text_"+slot,height=245,
                        placeholder="Selecione uma transcrição oficial na Biblioteca ou cole seu texto.")

def as_csv(rows, fields=None):
    return pd.DataFrame(rows,columns=fields).to_csv(index=False).encode("utf-8-sig")

st.title("🔎 Laboratório Forense")
st.caption("Análise documental · português brasileiro · corpus público rastreável")
tabs=st.tabs(["Biblioteca de transcrições", "Análise comparativa", "Ferramentas e metodologia"])

with tabs[0]:
    st.subheader("Transcrições integrais em português")
    st.write("Fonte primária: notas taquigráficas de sessões públicas do Senado Federal. O carregamento recupera os textos diretamente do portal oficial.")
    sources=catalogo()
    selected=st.selectbox("Documento oficial",sources,
        format_func=lambda item:item["titulo"],key="selected_source")
    st.caption(f'Fonte: {selected["proveniencia"]} · {selected["idioma"]} · {selected["tipo"]}')
    st.markdown(f'[Abrir documento na fonte oficial]({selected["url"]})')
    c1,c2,c3=st.columns([1,1,2])
    with c1: load_a=st.button("Carregar como A",type="primary",use_container_width=True)
    with c2: load_b=st.button("Carregar como B",use_container_width=True)
    if load_a or load_b:
        try:
            with st.spinner("Lendo texto na fonte oficial..."):
                fulltext=load_source(selected)
            put_document("A" if load_a else "B",fulltext,selected)
            st.session_state["last_loaded"]=selected["titulo"]
            st.success(f'Transcrição carregada: {len(fulltext):,} caracteres.')
        except Exception as exc:
            st.error(f'Falha ao recuperar transcrição: {exc}')
            st.info("Use o link oficial para consultar o texto no portal do Senado.")
    active=st.session_state.get("last_loaded")
    if active:
        st.caption(f"Última fonte carregada: {active}")
    preview=st.session_state.get("text_A") or st.session_state.get("text_B")
    if preview:
        with st.expander("Prévia do documento carregado",expanded=False):
            st.text(preview[:4500]+("\n[…]" if len(preview)>4500 else ""))
            st.download_button("Baixar transcrição TXT",preview.encode("utf-8"),
                               file_name="transcricao_senado.txt",mime="text/plain")

with tabs[1]:
    st.subheader("Corpus de trabalho")
    a_col,b_col=st.columns(2)
    with a_col:
        st.markdown("**Documento A**")
        document_box("A")
        st.caption(st.session_state.get("origin_A",{}).get("titulo",""))
    with b_col:
        st.markdown("**Documento B**")
        document_box("B")
        st.caption(st.session_state.get("origin_B",{}).get("titulo",""))
    max_frag=st.slider("Quantidade máxima de trechos por documento",40,280,160,20,
        help="Para documentos extensos, compare os trechos iniciais ou importe seções específicas.")
    level=st.slider("Similaridade lexical mínima",0.10,0.85,0.24,0.01)
    if st.button("Executar análise",type="primary",use_container_width=True):
        a=st.session_state.get("text_A","").strip()
        b=st.session_state.get("text_B","").strip()
        if not (a or b):
            st.error("Carregue ou digite ao menos um documento.")
        else:
            with st.spinner("Processando trechos e relações textuais..."):
                metrics=summary(a,b)
                notes=analyze(a,"A",max_frag)+analyze(b,"B",max_frag)
                timeline=times(a,"A")+times(b,"B")
                relations=compare(a,b,level,min(max_frag,220)) if a and b else []
                st.session_state["result"]={"metrics":metrics,"notes":notes,
                    "timeline":timeline,"relations":relations,"ts":datetime.now(timezone.utc).isoformat(),
                    "proveniencia":{"A":st.session_state.get("origin_A",{}),"B":st.session_state.get("origin_B",{})},
                    "sha256":{"A":hash_documento(a),"B":hash_documento(b)},
                    "limites":{"trechos":max_frag,"similaridade_minima":level}}
    result=st.session_state.get("result")
    if result:
        m=result["metrics"]
        cols=st.columns(4)
        cols[0].metric("Palavras A",f'{m["Palavras A"]:,}')
        cols[1].metric("Palavras B",f'{m["Palavras B"]:,}')
        cols[2].metric("Trechos marcados",len(result["notes"]))
        cols[3].metric("Pares relacionados",len(result["relations"]))
        rt=st.tabs(["Comparação", "Marcadores linguísticos", "Cronologia", "Relatório"])
        with rt[0]:
            st.caption("Pares ordenados por sinais de revisão e semelhança lexical. Um par relacionado não implica contradição.")
            st.dataframe(pd.DataFrame(result["relations"]),use_container_width=True,hide_index=True,height=430)
            st.download_button("Exportar comparação CSV",as_csv(result["relations"]),
                "comparacao.csv","text/csv")
        with rt[1]:
            st.dataframe(pd.DataFrame(result["notes"]),use_container_width=True,hide_index=True,height=430)
            st.download_button("Exportar marcadores CSV",as_csv(result["notes"]),"marcadores.csv","text/csv")
        with rt[2]:
            st.dataframe(pd.DataFrame(result["timeline"]),use_container_width=True,hide_index=True,height=380)
            st.download_button("Exportar referências temporais",as_csv(result["timeline"]),
                "referencias_temporais.csv","text/csv")
        with rt[3]:
            st.json({"gerado_em":result["ts"],"resumo":result["metrics"],"fontes":result["proveniencia"],
                "hashes":result["sha256"],"limites":result["limites"]})
            st.download_button("Exportar relatório JSON",
                json.dumps(result,ensure_ascii=False,indent=2).encode("utf-8"),
                "relatorio_forense.json","application/json")

with tabs[2]:
    st.subheader("Bibliotecas Python — diagnóstico de ambiente")
    deps={"spaCy":"spacy","NLTK":"nltk","scikit-learn":"sklearn",
          "Sentence Transformers":"sentence_transformers","RapidFuzz":"rapidfuzz",
          "NetworkX":"networkx","Plotly":"plotly","librosa":"librosa",
          "faster-whisper":"faster_whisper","pandas":"pandas","pypdf":"pypdf"}
    status=[{"Biblioteca":label,"Disponibilidade":"Instalada" if importlib.util.find_spec(module) else "Ausente"}
            for label,module in deps.items()]
    st.dataframe(pd.DataFrame(status),use_container_width=True,hide_index=True)
    st.info("A análise principal utiliza scikit-learn e regras linguísticas em português. "
        "As demais bibliotecas aparecem no diagnóstico para distinguir instalação de integração funcional.")
    st.markdown("""
**Como interpretar a análise**

- **Marcadores linguísticos:** localizam expressões de certeza, dúvida, reformulação e referência temporal.
- **Comparação textual:** TF-IDF relaciona trechos lexicalmente próximos, destacando diferenças verificáveis em números, horários e negações.
- **Cronologia:** reúne horários explícitos com os trechos de origem.
- **Proveniência:** o relatório registra links, data da análise e hashes dos documentos.

A publicação do Senado contém falas de depoentes, senadores e outras pessoas: a análise considera o documento completo, e não atribui automaticamente todas as falas ao depoente. Para análise individual, separe previamente as falas de interesse.
""")
