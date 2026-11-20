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

**Pendiente, en este orden:**
1. **Seguridad:** Nico pegó una API key de Gemini en un chat. Confirma con él que la borró en aistudio.google.com/apikey y creó una nueva. Nunca le pidas que pegue la clave en el chat.
2. Que Nico agregue `GEMINI_API_KEY` en los secrets del repo (Settings → Secrets and variables → Actions). Sugiérele `gh secret set GEMINI_API_KEY`, para que él mismo la escriba en la terminal sin que quede en el chat.
3. Probar la app local: `pip install -r requirements.txt` y `streamlit run app.py`, con `.streamlit/secrets.toml` creado por Nico. Revisar que el ID del modelo de Gemini funcione; si falla, pedirle el ID que aparece en AI Studio.
4. Deploy en Streamlit Community Cloud: https://share.streamlit.io/deploy?repository=NDiaz777/monitor-macro-pyme-chile&branch=main&mainModule=app.py (Nico entra con GitHub y pega el secreto en Advanced settings).
5. Correr el workflow de eval: `gh workflow run eval.yml`. Llenar la tabla de métricas del README (ES y EN) con las cifras reales: % de cifras verificadas, latencia, tokens y formato. Medir también la latencia con caché en la app.
6. Reemplazar `<tu-app>` en el README con la URL real de Streamlit.
7. Opcional: `BCCH_TOKEN` del Banco Central para tener el IPC al día. Verificar el código de serie con `scripts/buscar_series.py`.
8. Al terminar, darle a Nico un resumen para llevar al Project "AI Career Lab" de claude.ai: link de la demo, métricas y el bullet de CV, para actualizar el Registro de Proyectos y el Perfil Maestro.

## Reglas de trabajo
- Nunca subas `.streamlit/secrets.toml` ni claves. Las claves van en los Secrets de Streamlit o en variables de entorno.
- El ID del modelo de Gemini cambia seguido: pídele a Nico el que aparece en Google AI Studio.
- Antes de cada commit, corre `pytest -q`.
- README bilingüe ES/EN. Métricas solo si fueron medidas.
- Commits pequeños con mensajes claros en español.
