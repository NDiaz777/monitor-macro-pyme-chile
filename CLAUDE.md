# CLAUDE.md — Monitor Macro Pyme Chile (Proyecto #1 del portafolio)

## Quién es el usuario
Nico, estudiante de Ingeniería Comercial UAI. **No programa**: él dirige y tú construyes. Todo lo que hagas explícalo en español simple: QUÉ hace, POR QUÉ se hace así y QUÉ alternativas había. Necesita poder defenderlo en una entrevista. Windows 11, sin GPU.

## Restricción dura: costo CERO
Solo herramientas gratuitas: GitHub, Streamlit Community Cloud, Google Colab y el free tier de Gemini (sin tarjeta). Nunca agregues una API pagada ni actives facturación. Si algo cuesta plata, avisa y propone la alternativa gratis.

## Qué es el proyecto
Dashboard Streamlit con 8 indicadores macro de Chile (dólar, euro, UF, TPM, IPC, Imacec, desempleo y cobre), pensado para pymes. Incluye:
- `src/datos.py`: cadena de fuentes BCCh (opcional, con `BCCH_TOKEN`) → mindicador.cl → `data/snapshot.csv`, más un control de frescura.
- `src/kpis.py`: cambios a 30 días y 12 meses (% para precios, pp para tasas), percentil y señales por **reglas fijas**. Principio: las reglas deciden y la IA explica.
- `src/ia.py`: prompt con KPIs ya calculados → Gemini (`google-genai`) → `verificar_cifras` (eval de alucinaciones por regex).
- `app.py`: UI con caché de 6 h para datos y 12 h para la IA, y límite de 5 análisis por sesión.
- `scripts/evaluar_ia.py`: eval de 4 perfiles que genera `docs/eval_resultados.csv`.
- `.github/workflows/snapshot.yml`: cron diario que guarda el snapshot.
- `docs/GUIA_NICO.md`: guía de publicación, conceptos y preguntas de entrevista.

## Estado (19-nov-2026, fin de la sesión en el chat)
**Hecho:**
- Repo público: https://github.com/NDiaz777/monitor-macro-pyme-chile (rama `main`).
- `pytest -q` → 9/9 pasan.
- APIs reales probadas con el workflow `snapshot.yml` en GitHub Actions: 7/8 indicadores al día; el IPC de mindicador.cl sigue congelado en dic-2025 (la app lo marca como VIEJO). `data/snapshot.csv` ya está en el repo.
- Arreglado: la UF se publica por adelantado, así que se corta en la fecha de hoy.
- Workflow manual `eval.yml`: corre `scripts/evaluar_ia.py` con el secreto `GEMINI_API_KEY` del repo y guarda `docs/eval_resultados.csv`.

**Hecho el 20-nov-2026:**
- Clave Gemini nueva guardada como secret `GEMINI_API_KEY` (con `gh secret set`). `gh` instalado y logueado en la PC de Nico (`C:\Program Files\GitHub CLI\gh.exe`).
- IDs de modelo corregidos en `src/ia.py` (`gemini-3.5-flash`, `gemini-2.5-flash`, `gemini-3.5-flash-lite`) y `max_output_tokens=8192` (con 2048 salían respuestas cortadas).
- Eval corrido: 100 % cifras verificadas, mediana ~14 s, ~1.670/~405 tokens, 8/8 formato. Métricas ya en el README (ES y EN), salvo latencia con caché.
- La instalación local con Python 3.14 se colgó (pandas); la prueba local se omitió, se valida directo en Streamlit Cloud.

**Pendiente, en este orden:**
1. Deploy en Streamlit Community Cloud: https://share.streamlit.io/deploy?repository=NDiaz777/monitor-macro-pyme-chile&branch=main&mainModule=app.py (Nico entra con GitHub y pega `GEMINI_API_KEY = "..."` en Advanced settings → Secrets). Lo hace Nico.
2. Con la URL: reemplazar `<tu-app>` en el README, medir latencia con caché (origen "Caché") y llenar esa fila.
3. Opcional: `BCCH_TOKEN` del Banco Central para el IPC al día (`scripts/buscar_series.py`).
4. Resumen para el Project "AI Career Lab" de claude.ai: link de la demo, métricas y bullet de CV.

## Reglas de trabajo
- Nunca subas `.streamlit/secrets.toml` ni claves. Las claves van en los Secrets de Streamlit o en variables de entorno.
- El ID del modelo de Gemini cambia seguido: pídele a Nico el que aparece en Google AI Studio.
- Antes de cada commit, corre `pytest -q`.
- README bilingüe ES/EN. Métricas solo si fueron medidas.
- Commits pequeños con mensajes claros en español.
