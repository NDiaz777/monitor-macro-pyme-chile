# Guía de Nico — Proyecto #1: Monitor Macro Pyme Chile

> Para ti, no para el reclutador. Aquí está cómo publicarlo, qué hace cada pieza y cómo defenderlo en una entrevista.

---

## 1. Publicarlo en 5 pasos (≈30 min, $0, sin instalar nada)

### Paso 1 — API key de Gemini (gratis, sin tarjeta)
1. Entra a **aistudio.google.com** con tu Gmail.
2. **Get API key → Create API key**. Cópiala y guárdala en un lugar privado.
3. En AI Studio revisa el **ID exacto del modelo Flash** disponible (por ejemplo `gemini-flash-latest`). Los nombres cambian seguido.
4. ⚠️ No le agregues facturación al proyecto: sin facturación, al llegar al límite la API solo responde "cuota agotada" y nunca cobra.

### Paso 2 — Subir el código a GitHub
1. Crea tu cuenta en **github.com**. Elige un usuario profesional (por ejemplo `nicodiazbarra`).
2. **New repository** → nombre `monitor-macro-pyme-chile` → **Public** → sin README → *Create*.
3. Haz clic en **"uploading an existing file"** y arrastra **todo el contenido** de la carpeta descomprimida, incluidas `.github` y `.streamlit` → *Commit changes*.
4. Revisa que **NO** subiste ningún archivo `secrets.toml` (solo debe estar `secrets.toml.example`).

**Alternativa con Claude Code:** abre la carpeta y pídele:
`Inicializa git en esta carpeta, crea el repo público monitor-macro-pyme-chile en mi GitHub con gh y súbelo. Verifica que .streamlit/secrets.toml no se suba.`

### Paso 3 — Publicar la demo en Streamlit Community Cloud
1. Entra a **share.streamlit.io** → *Continue with GitHub*.
2. **Create app** → repo `monitor-macro-pyme-chile`, rama `main`, archivo `app.py`.
3. Elige una URL linda (por ejemplo `monitor-macro-pyme`).
4. **Advanced settings → Secrets** y pega:
   ```
   GEMINI_API_KEY = "tu-key"
   GEMINI_MODEL = "el-id-que-viste-en-AI-Studio"
   ```
5. **Deploy**. Espera unos 2 minutos.

### Paso 4 — Activar el respaldo diario (GitHub Actions)
1. En tu repo, pestaña **Actions** → habilita los workflows.
2. Abre **"Actualizar snapshot diario"** → **Run workflow**.
3. Si termina en ✅ se crea `data/snapshot.csv` y el log muestra qué indicadores están OK o VIEJOS. Esa es la primera prueba real de que las APIs responden.
4. Si falla con un error de permisos: *Settings → Actions → General → Workflow permissions → Read and write*.

### Paso 5 — Medir y completar el README (en Google Colab, gratis)
Abre **colab.research.google.com** → nuevo notebook → ejecuta:
```python
!git clone https://github.com/TU-USUARIO/monitor-macro-pyme-chile
%cd monitor-macro-pyme-chile
!pip install -q -r requirements.txt
import os; os.environ["GEMINI_API_KEY"] = "tu-key"; os.environ["REPETICIONES"] = "2"
!python scripts/evaluar_ia.py
```
Copia el **RESUMEN** a la tabla de métricas del README. Mide también la latencia con caché: en la app, genera el mismo análisis dos veces y anota la latencia de la segunda vez. **Esas cifras son reales y van a tu CV.**

**Opcional (fuente oficial del IPC):** crea una cuenta gratis en la BDE del Banco Central (si3.bcentral.cl), activa la API, copia tu *Apikey Token* y agrégalo como `BCCH_TOKEN` en los Secrets de Streamlit y de GitHub. Así el IPC vuelve a estar al día.

---

## 2. Qué hace cada archivo
| Archivo | Rol (en lenguaje de negocio) |
|---|---|
| `src/config.py` | El "catálogo": qué indicadores se muestran y cuándo un dato se considera viejo |
| `src/datos.py` | El "proveedor": trae los datos, los limpia y tiene plan B y plan C si una fuente falla |
| `src/kpis.py` | El "analista junior": calcula las variaciones y aplica reglas fijas (el semáforo) |
| `src/ia.py` | El "redactor": arma el encargo para la IA y después revisa que no haya inventado cifras |
| `app.py` | La "vitrina": el dashboard que ve el usuario |
| `scripts/evaluar_ia.py` | El "control de calidad": mide la IA con números |
| `scripts/actualizar_snapshot.py` + `.github/workflows/` | El "turno de noche": guarda una copia de los datos todos los días, solo |
| `tests/` | Pruebas automáticas que comprueban que las fórmulas calculan bien |

---

## 3. Conceptos clave (con analogía de negocio)
- **Inferencia:** cada vez que el modelo genera una respuesta. *Como encargarle un informe a un consultor: cada encargo tiene costo y demora.*
- **Tokens:** los pedazos de texto (≈ ¾ de palabra) que el modelo lee y escribe. Son la unidad de cobro y de límite. *Como las horas facturables del consultor.* Por eso le mandamos **KPIs ya calculados** (~1k tokens) y no 3 años de datos (~30k).
- **Latencia:** cuánto tarda la respuesta. *El tiempo de espera en caja.*
- **Caching:** guardar una respuesta para reutilizarla. *Si diez clientes piden el mismo informe, lo fotocopias en vez de pagarlo diez veces.* En la app: mismos datos + mismo perfil = 0 tokens.
- **Grounding:** obligar al modelo a basarse solo en los datos que le entregas. *Darle al consultor la planilla oficial y prohibirle opinar sin números.*
- **Alucinación:** cuando el modelo inventa algo con seguridad. *Un vendedor que inventa una cifra para cerrar la venta.*
- **Eval:** una prueba medible de calidad de la IA. *El control de calidad en la línea de producción.* La nuestra mide el % de cifras verificadas, la latencia, los tokens y el formato.
- **Pipeline / cron:** un proceso automático que corre a una hora fija. *El camión de reparto que sale todos los días a las 8:00 sin que nadie lo llame.*

---

## 4. Decisiones que debes poder defender
1. **Las reglas deciden, la IA explica.** El semáforo es determinista y auditable; la IA solo redacta. Alternativa: dejar que la IA decida, que es más flexible pero puede cambiar de opinión entre corridas.
2. **mindicador.cl + BCCh opcional.** Prioricé que funcione sin registro. El hallazgo de que el IPC estaba congelado justificó agregar el control de frescura y la fuente oficial.
3. **Gemini free tier en vez de Ollama.** Permite una demo pública interactiva a $0. El riesgo es la cuota, que se mitiga con caché de 12 h, un límite de 5 análisis por sesión y mensajes claros cuando se agota.
4. **Verificador por regex en vez de "LLM como juez".** Gratis, instantáneo y explicable. Limitación honesta: detecta cifras inventadas, no razonamientos malos.

---

## 5. Preguntas de entrevista (y qué responder)

**1. "¿Cómo evitas que la IA invente datos?"**
→ "En tres capas. Primero, el modelo solo recibe KPIs ya calculados y tiene una regla explícita de no inventar cifras (grounding). Segundo, las decisiones del semáforo las toman reglas fijas, no la IA. Tercero, un verificador automático extrae cada número de la respuesta y lo compara con los datos de entrada; en mis evals el resultado fue [X]% de cifras verificadas, y la app muestra en pantalla cualquier cifra no respaldada."

**2. "¿Por qué no usaste un modelo más potente o una API pagada?"**
→ "Por la restricción de negocio: costo cero y una demo pública. Para redactar 200 palabras a partir de datos estructurados basta un modelo Flash. Lo difícil no era la potencia del modelo, sino la calidad de los datos y el control de errores. Si escalara, mediría con el mismo eval si un modelo mayor mejora lo suficiente como para justificar su costo."

**3. "¿Qué pasa si la fuente de datos se cae o la cuota se agota?"**
→ "Diseñé una cadena de respaldo: Banco Central → mindicador → un snapshot que GitHub Actions guarda todos los días. Para la IA uso caché de 12 h, así que la mayoría de las consultas no gasta cuota, y un límite por sesión. Si aun así se agota, la app sigue mostrando los KPIs y las señales; solo se pausa la redacción."

**4. "¿Qué fue lo más difícil o lo más interesante?"**
→ "Descubrir que una fuente pública muy usada tenía el IPC congelado desde diciembre de 2025. Si no lo hubiera revisado, la IA habría explicado con total seguridad un dato de hace casi un año. Me enseñó que en IA aplicada la calidad de los datos pesa más que el modelo, y por eso agregué un control de frescura visible."

**5. "¿Cómo lo convertirías en un producto real?"**
→ "Validaría con 10 dueños de pymes qué decisión les duele más. Después agregaría alertas por correo o WhatsApp cuando cambie una señal y personalización por rubro con sus propios costos. El modelo de negocio podría ser freemium o una herramienta de captación para un banco o contador. Mediría el uso semanal y si las alertas llevan a una acción."
