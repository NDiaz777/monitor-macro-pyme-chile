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

## Estado (19-nov-2026)
- Código completo; `pytest -q` → 9/9 pasan. APIs reales probadas vía GitHub Actions (19-nov): 7/8 indicadores al día, IPC VIEJO.
- Hallazgo: en mindicador.cl el IPC está congelado en dic-2025. La app lo marca como desactualizado.
- **Pendiente:**
  3. Deploy en Streamlit Cloud con secrets.
  5. Correr `scripts/evaluar_ia.py` y llenar la tabla de métricas del README con cifras reales (nunca inventadas).
  6. Reemplazar `<tu-app>` en el README con la URL real de Streamlit.

## Reglas de trabajo
- Nunca subas `.streamlit/secrets.toml` ni claves. Las claves van en los Secrets de Streamlit o en variables de entorno.
- El ID del modelo de Gemini cambia seguido: pídele a Nico el que aparece en Google AI Studio.
- Antes de cada commit, corre `pytest -q`.
- README bilingüe ES/EN. Métricas solo si fueron medidas.
- Commits pequeños con mensajes claros en español.
