"""Capa de IA: prompt, llamada a Gemini (free tier) y verificación de cifras.

Flujo:  KPIs (números ya calculados)  ->  prompt  ->  Gemini  ->  texto
                                                         |
                                       verificar_cifras: ¿cada número del texto
                                       existe en los datos? (control de alucinaciones)
"""
from __future__ import annotations

import json
import re
import time

PERFILES = {
    "Importador": "Pyme que importa productos o insumos pagados en dólares y los vende en pesos en Chile.",
    "Exportador": "Pyme que produce en Chile y vende al extranjero, cobrando en dólares.",
    "Comercio con arriendo en UF": "Comercio minorista que arrienda su local en UF y vende en pesos a hogares.",
    "Con crédito bancario": "Pyme con un crédito bancario a tasa variable para capital de trabajo.",
}

SISTEMA = (
    "Eres un analista económico que asesora a dueños de pymes chilenas. "
    "Escribes en español de Chile, claro y sin jerga. "
    "REGLAS ESTRICTAS: (1) Usa SOLO las cifras del JSON entregado; no inventes cifras, "
    "proyecciones numéricas ni fechas. (2) Si un dato viene marcado como desactualizado, dilo explícitamente. "
    "(3) No des recomendaciones de inversión; habla de decisiones operativas del negocio "
    "(precios, compras, inventario, deuda, contratación)."
)

FORMATO = """Responde en Markdown con exactamente estas secciones:
### Resumen en una frase
### Las 3 señales que más importan
(3 bullets, cada uno con la cifra que lo respalda)
### Qué significa para tu negocio
(3 bullets concretos para el perfil indicado)
### Qué vigilar el próximo mes
(2 bullets)
Máximo 220 palabras en total."""

MODELOS_RESPALDO = ["gemini-flash-latest", "gemini-flash-lite-latest"]


def construir_prompt(kpis: dict, senales: list[dict], meta: dict, perfil: str) -> str:
    datos = {}
    for codigo, k in kpis.items():
        datos[codigo] = {**k, "desactualizado": not meta.get(codigo, {}).get("fresco", True)}
    return (
        f"PERFIL DEL NEGOCIO: {PERFILES[perfil]}\n\n"
        f"DATOS (JSON, variaciones de precios en %, de tasas en puntos porcentuales 'pp'):\n"
        f"{json.dumps(datos, ensure_ascii=False, indent=1)}\n\n"
        f"SEÑALES DETECTADAS POR REGLAS:\n"
        + "\n".join(f"- [{x['nivel']}] {x['texto']}" for x in senales)
        + f"\n\n{FORMATO}"
    )


def generar_insight(prompt: str, api_key: str, modelo: str | None = None) -> dict:
    """Llama a Gemini. Prueba el modelo configurado y luego los de respaldo."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    candidatos = [m for m in [modelo, *MODELOS_RESPALDO] if m]
    ultimo_error = None
    for m in dict.fromkeys(candidatos):
        try:
            t0 = time.perf_counter()
            resp = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SISTEMA, temperature=0.3, max_output_tokens=2048),
            )
            latencia = time.perf_counter() - t0
            uso = resp.usage_metadata
            return {
                "texto": resp.text or "",
                "modelo": m,
                "latencia_s": round(latencia, 2),
                "tokens_entrada": getattr(uso, "prompt_token_count", None),
                "tokens_salida": getattr(uso, "candidates_token_count", None),
                "generado_en": time.time(),
            }
        except Exception as e:  # modelo no disponible, cuota agotada, red, etc.
            ultimo_error = e
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                break  # la cuota es por proyecto: probar otro modelo no suele ayudar
    raise RuntimeError(str(ultimo_error))


# ---------- Verificación de cifras (eval simple de alucinaciones) ----------

_NUM = re.compile(r"(?<![\w])\d+(?:[.,]\d+)*")


def _interpretaciones(token: str) -> set[float]:
    """'1.002,07' / '1,002.07' / '3,5' / '3.5' -> todos los floats posibles."""
    t = token.strip()
    out = set()
    for dec, mil in ((",", "."), (".", ",")):
        try:
            out.add(abs(float(t.replace(mil, "").replace(dec, "."))))
        except ValueError:
            pass
    return out


def _valores_permitidos(kpis: dict) -> list[float]:
    vals = []
    for k in kpis.values():
        for v in k.values():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.append(abs(float(v)))
    return vals


def verificar_cifras(texto: str, kpis: dict) -> dict:
    """Extrae cada número del texto y revisa si coincide con algún dato de entrada.

    Se ignoran enteros chicos (0-12: 'las 3 señales', '12 meses') y años (1990-2100),
    y el rango meta 2%-4% del Banco Central, que es conocimiento público estable.
    """
    # + rango meta (2%-4%) y ventanas de tiempo usadas en los KPIs (30 días, 365 días).
    permitidos = _valores_permitidos(kpis) + [2.0, 3.0, 4.0, 30.0, 365.0]
    revisadas, no_verificadas = 0, []
    for token in _NUM.findall(texto):
        cands = _interpretaciones(token)
        if not cands:
            continue
        if any(c.is_integer() and (0 <= abs(c) <= 12 or 1990 <= c <= 2100) for c in cands):
            continue
        revisadas += 1
        ok = any(abs(c - p) <= max(0.051, abs(p) * 0.005) for c in cands for p in permitidos)
        if not ok:
            no_verificadas.append(token)
    pct = 100.0 if revisadas == 0 else round((revisadas - len(no_verificadas)) / revisadas * 100, 1)
    return {"cifras_revisadas": revisadas, "no_verificadas": no_verificadas, "pct_verificadas": pct}
