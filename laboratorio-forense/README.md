# Laboratório Forense — Streamlit

Protótipo offline para análise exploratória de depoimentos em português. Analisa marcadores linguísticos, frases e similaridade TF-IDF, sem dependência de API externa. Não inclui corpus real validado nem transcrição de áudio nesta versão.

## Executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Para acessar no celular na mesma rede: `streamlit run app.py --server.address 0.0.0.0` e abrir `http://IP_DO_COMPUTADOR:8501`. Não exponha o servidor à internet sem autenticação e proteção dos dados.

## Recursos

- TXT, PDF com texto e DOCX
- Dois depoimentos e identificação de frases semelhantes
- Marcadores de incerteza, autocorreção, negação e tempo
- Exportação CSV dos trechos sinalizados

Os resultados são sinais de revisão documental e não substituem a leitura contextual. PDFs digitalizados precisam de OCR adicional.
