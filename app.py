"""Monitor Macro Pyme Chile - app Streamlit.

Ejecutar local:  streamlit run app.py
"""
import time

import plotly.express as px
import streamlit as st

from src.config import INDICADORES
from src.datos import cargar_indicadores
from src.ia import PERFILES, construir_prompt, generar_insight, verificar_cifras
from src.kpis import calcular_todos, generar_senales

st.set_page_config(page_title="Monitor Macro Pyme Chile", page_icon="📈", layout="wide")

LIMITE_IA_POR_SESION = 5  # protege la cuota gratuita de Gemini


def secreto(nombre, defecto=None):
    try:
        return st.secrets.get(nombre, defecto)
    except Exception:
        return defecto


# ---------- Caché: datos (6 h) e insights (12 h) ----------
@st.cache_data(ttl=6 * 3600, show_spinner="Descargando indicadores...")
def datos_cacheados(anios):
    t0 = time.perf_counter()
    series, meta = cargar_indicadores(anios, bcch_token=secreto("BCCH_TOKEN"))
    return series, meta, round(time.perf_counter() - t0, 2)


@st.cache_data(ttl=12 * 3600, show_spinner=False)
def insight_cacheado(prompt, modelo):
    # La llave de caché es el prompt: mismos datos + mismo perfil = misma respuesta, 0 tokens.
    return generar_insight(prompt, secreto("GEMINI_API_KEY"), modelo)


def fmt(v, dec=2):
    if v is None:
        return "s/d"
    return f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------- Sidebar ----------
with st.sidebar:
    st.header("Configuración")
    perfil = st.selectbox("Perfil de tu pyme", list(PERFILES))
    st.caption(PERFILES[perfil])
    anios = st.radio("Historia a mostrar", [1, 3], index=1, format_func=lambda x: f"{x} año(s)")
    st.divider()
    st.caption("Fuentes: mindicador.cl y Banco Central de Chile (BDE). "
               "Los datos son propiedad de sus fuentes; el análisis es responsabilidad del autor.")
    st.caption("Esto no es asesoría financiera.")

# ---------- Datos ----------
series, meta, seg_carga = datos_cacheados(anios)
kpis = calcular_todos(series)
senales = generar_senales(kpis)

st.title("📈 Monitor Macro Pyme Chile")
st.markdown("**¿Subo precios, importo ahora o espero?** Los indicadores que mueven a una pyme chilena, "
            "en un solo lugar, con una lectura generada por IA para tu tipo de negocio.")

viejos = [f"{INDICADORES[c]['nombre']} (último dato: {m['ultima_fecha']})"
          for c, m in meta.items() if not m["fresco"]]
if viejos:
    st.warning("**Datos desactualizados en la fuente:** " + "; ".join(viejos) +
               ". Se muestran igual, pero tómalos con cautela.")

# ---------- KPIs ----------
orden = ["dolar", "uf", "tpm", "ipc", "imacec", "tasa_desempleo", "libra_cobre", "euro"]
for fila in (orden[:4], orden[4:]):
    cols = st.columns(4)
    for col, c in zip(cols, fila):
        k = kpis.get(c)
        if not k:
            col.metric(INDICADORES[c]["nombre"], "s/d")
            continue
        valor = k.get("acumulado_12m", k["ultimo"]) if c == "ipc" else k["ultimo"]
        etiqueta = "IPC (acum. 12 meses)" if c == "ipc" and "acumulado_12m" in k else k["indicador"]
        unidad = "%" if k["unidad"] == "%" else f" {k['unidad']}"
        delta = k["cambio_12m"] if c in ("ipc", "imacec", "tasa_desempleo") else k["cambio_30d"]
        ventana = "12m" if c in ("ipc", "imacec", "tasa_desempleo") else "30d"
        col.metric(
            etiqueta, f"{fmt(valor)}{unidad}",
            None if delta is None else f"{fmt(delta)} {k['unidad_cambio']} ({ventana})",
            delta_color="inverse" if c in ("dolar", "euro", "ipc", "tasa_desempleo", "tpm") else "normal",
            help=f"Último dato: {k['fecha']} · Fuente: {meta[c]['fuente']}",
        )

# ---------- Señales (reglas) ----------
st.subheader("🚦 Señales detectadas")
st.caption("Generadas por reglas fijas y auditables (no por IA).")
iconos = {"alerta": "🔴", "atencion": "🟡", "favorable": "🟢"}
for s in senales or [{"nivel": "atencion", "texto": "Sin señales fuertes en este momento."}]:
    st.markdown(f"{iconos[s['nivel']]} {s['texto']}")

# ---------- Gráficos ----------
st.subheader("📊 Evolución")
grupos = {
    "Tipo de cambio": ["dolar", "euro"],
    "UF": ["uf"],
    "Tasas e inflación": ["tpm", "ipc"],
    "Actividad y empleo": ["imacec", "tasa_desempleo"],
    "Cobre": ["libra_cobre"],
}
for tab, codigos in zip(st.tabs(list(grupos)), grupos.values()):
    with tab:
        cols = st.columns(len(codigos))
        for col, c in zip(cols, codigos):
            s = series.get(c)
            if s is None or s.empty:
                col.info(f"Sin datos para {INDICADORES[c]['nombre']}")
                continue
            fig = px.line(s.reset_index(), x="fecha", y=c,
                          labels={"fecha": "", c: INDICADORES[c]["unidad"]},
                          title=INDICADORES[c]["nombre"])
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
            col.plotly_chart(fig, width="stretch")

# ---------- IA ----------
st.subheader("🤖 Lectura con IA para tu negocio")
api_key = secreto("GEMINI_API_KEY")
st.session_state.setdefault("usos_ia", 0)

if not api_key:
    st.info("Falta configurar GEMINI_API_KEY en los *secrets* de la app para activar el análisis.")
elif st.button(f"Generar análisis para: {perfil}", type="primary"):
    if st.session_state.usos_ia >= LIMITE_IA_POR_SESION:
        st.warning("Llegaste al límite de análisis por sesión (protege la cuota gratuita). Recarga más tarde.")
    else:
        prompt = construir_prompt(kpis, senales, meta, perfil)
        t0 = time.perf_counter()
        try:
            with st.spinner("Analizando con Gemini..."):
                r = insight_cacheado(prompt, secreto("GEMINI_MODEL"))
            desde_cache = time.time() - r["generado_en"] > 2
            if not desde_cache:
                st.session_state.usos_ia += 1
            st.markdown(r["texto"])
            v = verificar_cifras(r["texto"], kpis)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Cifras verificadas", f"{v['pct_verificadas']}%",
                      help="% de números del texto que coinciden con los datos de entrada.")
            c2.metric("Latencia", f"{time.perf_counter() - t0:.2f} s" if desde_cache else f"{r['latencia_s']} s")
            c3.metric("Tokens (entrada/salida)", f"{r['tokens_entrada']}/{r['tokens_salida']}")
            c4.metric("Origen", "Caché (0 tokens)" if desde_cache else r["modelo"])
            if v["no_verificadas"]:
                st.caption("⚠️ Cifras no encontradas en los datos: " + ", ".join(v["no_verificadas"]))
            with st.expander("Ver el prompt enviado al modelo"):
                st.code(prompt, language="markdown")
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                st.error("Se agotó la cuota gratuita de Gemini por ahora. Intenta más tarde.")
            else:
                st.error(f"No se pudo generar el análisis: {msg[:300]}")

st.divider()
st.caption(f"Datos cargados en {seg_carga} s (en caché 6 h). Proyecto de portafolio · "
           "github.com/NDiaz777/monitor-macro-pyme-chile")
