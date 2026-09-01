# VTT Lab

Laboratório de desenvolvimento e testes dos VTTs.

Este repositório **não substitui o Braseiro Build**. A separação é intencional:

- **vtt-lab**: recebe e testa o VTT durante o desenvolvimento.
- **braseirobuild**: recebe o ZIP Android final e gera o APK.

## Fluxo

Concept art / projeto → ChatGPT → VTT Lab → Playwright → correções → ZIP Android → Braseiro Build → APK.

## Tela-alvo

Os testes móveis usam por padrão **415 × 915 px**.

## Pastas

- `current/`: área reservada para o VTT em desenvolvimento.
- `tests/`: testes Playwright.
- `.github/workflows/`: automação dos testes no GitHub.

O usuário não precisa operar o Playwright manualmente; a automação do GitHub executa os testes.
