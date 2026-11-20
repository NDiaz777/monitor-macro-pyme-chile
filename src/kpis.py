"""KPIs y señales: la parte determinística (reglas fijas, sin IA).

Principio de diseño: las REGLAS deciden qué está pasando; la IA solo lo EXPLICA.
Así el semáforo es auditable y no depende de que el modelo "adivine" bien.
"""
from __future__ import annotations

import pandas as pd

from src.config import INDICADORES, META_INFLACION


def n(v) -> str:
    """Formato chileno: 1.002,07"""
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".").rstrip("0").rstrip(",")


def _valor_hace(s: pd.Series, dias: int):
    objetivo = s.index[-1] - pd.Timedelta(days=dias)
    previo = s[s.index <= objetivo]
    return float(previo.iloc[-1]) if len(previo) else None


def _cambio(actual, previo, tipo):
    if previo is None:
        return None
    if tipo == "precio":
        return round((actual / previo - 1) * 100, 2) if previo else None
    return round(actual - previo, 2)  # puntos porcentuales


def calcular_kpis(s: pd.Series, codigo: str) -> dict | None:
    s = s.dropna()
    if s.empty:
        return None
    cfg = INDICADORES[codigo]
    ultimo = float(s.iloc[-1])
    k = {
        "indicador": cfg["nombre"],
        "unidad": cfg["unidad"],
        "fecha": s.index[-1].date().isoformat(),
        "ultimo": round(ultimo, 2),
        "cambio_30d": _cambio(ultimo, _valor_hace(s, 30), cfg["tipo"]),
        "cambio_12m": _cambio(ultimo, _valor_hace(s, 365), cfg["tipo"]),
        "unidad_cambio": "%" if cfg["tipo"] == "precio" else "pp",
        "minimo_periodo": round(float(s.min()), 2),
        "maximo_periodo": round(float(s.max()), 2),
        # Percentil: 90 = el valor actual está más alto que el 90% de los datos del periodo.
        "percentil_periodo": round(float((s <= ultimo).mean() * 100), 0),
    }
    if codigo == "ipc":
        ult12 = s.iloc[-12:]
        if len(ult12) == 12:
            k["acumulado_12m"] = round(float(((1 + ult12 / 100).prod() - 1) * 100), 2)
    return k


def calcular_todos(series: dict[str, pd.Series]) -> dict[str, dict]:
    return {c: k for c, s in series.items() if (k := calcular_kpis(s, c))}


def generar_senales(k: dict[str, dict]) -> list[dict]:
    """Reglas simples y explicables. nivel: 'alerta' | 'atencion' | 'favorable'."""
    s = []

    def add(nivel, texto):
        s.append({"nivel": nivel, "texto": texto})

    d = k.get("dolar")
    if d and d["cambio_30d"] is not None:
        if d["cambio_30d"] >= 3:
            add("alerta", f"El dólar subió {n(d['cambio_30d'])}% en 30 días: encarece importaciones e insumos.")
        elif d["cambio_30d"] <= -3:
            add("favorable", f"El dólar bajó {n(abs(d['cambio_30d']))}% en 30 días: buena ventana para importar.")
    if d and d["percentil_periodo"] >= 80:
        add("atencion", f"El dólar está en la zona alta del periodo (percentil {d['percentil_periodo']:.0f}).")

    t = k.get("tpm")
    if t and t["cambio_12m"] is not None:
        if t["cambio_12m"] < 0:
            add("favorable", f"La TPM bajó {n(abs(t['cambio_12m']))} pp en 12 meses: el crédito tiende a abaratarse.")
        elif t["cambio_12m"] > 0:
            add("alerta", f"La TPM subió {n(t['cambio_12m'])} pp en 12 meses: el crédito se encarece.")

    i = k.get("ipc")
    if i and "acumulado_12m" in i:
        a = i["acumulado_12m"]
        if a > META_INFLACION + 1:
            add("alerta", f"Inflación 12 meses de {n(a)}%: sobre el rango meta del Banco Central (2%-4%).")
        elif a < META_INFLACION - 1:
            add("atencion", f"Inflación 12 meses de {n(a)}%: bajo el rango meta (2%-4%), señal de demanda débil.")
        else:
            add("favorable", f"Inflación 12 meses de {n(a)}%: dentro del rango meta (2%-4%).")

    m = k.get("imacec")
    if m:
        if m["ultimo"] < 0:
            add("alerta", f"Imacec de {n(m['ultimo'])}%: la actividad económica se contrae.")
        elif m["ultimo"] >= 2:
            add("favorable", f"Imacec de {n(m['ultimo'])}%: la actividad crece a buen ritmo.")
        else:
            add("atencion", f"Imacec de {n(m['ultimo'])}%: crecimiento bajo.")

    u = k.get("tasa_desempleo")
    if u and u["cambio_12m"] is not None and u["cambio_12m"] >= 0.5:
        add("alerta", f"El desempleo subió {n(u['cambio_12m'])} pp en 12 meses: ojo con la demanda de los hogares.")

    return s
