# Laboratório Forense — Streamlit

Análise exploratória de declarações e documentos em português brasileiro, com exercícios cegos baseados em interrogatórios judiciais reais.

## Testar no Streamlit Community Cloud

- Repositório: bra83/vtt-lab
- Branch: laboratorio-forense-streamlit-v2
- Main file path: laboratorio-forense/app.py

### Biblioteca de transcrições — modo cego criminal

1. Abra **Biblioteca de transcrições** e selecione **Depoimentos criminais — investigação cega**, depois CR-01 ou CR-02.
2. Leia o **contexto neutro do crime** e as perguntas de apoio.
3. Clique **Carregar depoimento do suspeito**. O aplicativo recupera o documento do tribunal, pseudonimiza nomes e locais e separa as respostas das perguntas judiciais.
4. Os resultados preliminares são exibidos na biblioteca. Clique **Analisar como documento A** para enviar as respostas do suspeito ao motor de análise e calcular os indicadores automaticamente; abra a aba **Análise comparativa** para ver o relatório detalhado. Você também pode carregar um segundo depoimento como B para comparação.
5. Registre seu parecer (fatos, hipóteses, explicações alternativas e verificações). Depois disso, o link do processo oficial fica disponível para conferência.

**Tipo documental:** termo judicial em discurso indireto; não é gravação ou transcrição fonética. O aplicativo não apresenta o histórico do processo como se fosse um depoimento.

**Fonte primária:** registros públicos do Portal e-SAJ do Tribunal de Justiça de Alagoas. Os exercícios CR não usam texto ficcional.

## Biblioteca parlamentar

Na mesma **Biblioteca de transcrições**, alterne o acervo para **Audiências públicas — Senado Federal**. As notas taquigráficas oficiais podem ser carregadas como A ou B, para análise no mesmo fluxo.

## Funções de análise

- Importar TXT, PDF textual e DOCX.
- Marcadores de dúvida, reformulação, negação, afirmações enfáticas e tempo.
- Pareamento textual TF-IDF e diferenças de números, horários e negações.
- Extração de referências temporais e relatórios CSV e JSON com fontes e hashes.
- Diagnóstico das bibliotecas Python instaladas.

Os indicadores são destinados a orientar revisão de documentos; uma correlação textual não equivale à confirmação de um fato.

## Executar localmente

    pip install -r requirements.txt
    streamlit run app.py

O carregamento de fontes públicas requer conexão HTTPS. Documentos próprios são analisados pelo motor local e não enviados a serviços externos de IA.

## Verificação

O CI instala dependências, executa testes unitários, o teste de interface Streamlit, o teste HTTP e a recuperação real dos registros públicos. Também verifica que um documento criminal excessivamente extenso não seja confundido com um único interrogatório.
