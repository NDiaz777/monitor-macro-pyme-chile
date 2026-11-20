"""Capa de datos: descarga, limpieza y control de frescura.

Cadena de fuentes (de mejor a peor):
1. Banco Central de Chile (oficial) - solo para series en SERIES_BCCH y si hay token.
2. mindicador.cl (gratis, sin registro) - fuente principal.
3. data/snapshot.csv (copia guardada) - si las APIs fallan, la app igual funciona.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import requests

from src.config import INDICADORES, MAX_DIAS_ANTIGUEDAD, SERIES_BCCH

MINDICADOR_URL = "https://mindicador.cl/api/{codigo}/{anio}"
BCCH_URL = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"
SNAPSHOT = Path(__file__).resolve().parent.parent / "data" / "snapshot.csv"
TIMEOUT = 15


def _a_fecha_local(fechas: pd.Series) -> pd.Series:
    """mindicador entrega fechas en UTC (ej. 2026-11-19T03:00Z = 19-nov en Chile)."""
    f = pd.to_datetime(fechas, utc=True).dt.tz_convert("America/Santiago")
    return f.dt.tz_localize(None).dt.normalize()


def descargar_mindicador(codigo: str, anios: list[int]) -> pd.Series:
    registros = []
    for anio in anios:
        r = requests.get(MINDICADOR_URL.format(codigo=codigo, anio=anio), timeout=TIMEOUT)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        registros += r.json().get("serie", [])
    if not registros:
        return pd.Series(dtype=float, name=codigo)
    df = pd.DataFrame(registros)
    df["fecha"] = _a_fecha_local(df["fecha"])
    s = df.groupby("fecha")["valor"].last().astype(float).sort_index()
    s.name = codigo
    return s


def descargar_bcch(serie: str, token: str, desde: str, hasta: str) -> pd.Series:
    params = {"token": token, "function": "GetSeries", "timeseries": serie,
              "firstdate": desde, "lastdate": hasta}
    r = requests.get(BCCH_URL, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    obs = (r.json().get("Series") or {}).get("Obs") or []
    df = pd.DataFrame(obs)
    if df.empty:
        return pd.Series(dtype=float)
    df["fecha"] = pd.to_datetime(df["indexDateString"], format="%d-%m-%Y")
    df["valor"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna(subset=["valor"]).set_index("fecha")["valor"].sort_index()


def estado_frescura(s: pd.Series, frecuencia: str, hoy: dt.date | None = None) -> dict:
    hoy = hoy or dt.date.today()
    if s.empty:
        return {"ultima_fecha": None, "dias": None, "fresco": False}
    ultima = s.index.max().date()
    dias = (hoy - ultima).days
    return {"ultima_fecha": ultima, "dias": dias, "fresco": dias <= MAX_DIAS_ANTIGUEDAD[frecuencia]}


def _leer_snapshot() -> dict[str, pd.Series]:
    if not SNAPSHOT.exists():
        return {}
    df = pd.read_csv(SNAPSHOT, parse_dates=["fecha"])
    return {c: g.set_index("fecha")["valor"].sort_index() for c, g in df.groupby("indicador")}


def guardar_snapshot(series: dict[str, pd.Series]) -> None:
    filas = [pd.DataFrame({"indicador": c, "fecha": s.index, "valor": s.values})
             for c, s in series.items() if not s.empty]
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(filas).to_csv(SNAPSHOT, index=False)


def cargar_indicadores(anios_atras: int = 3, bcch_token: str | None = None,
                       usar_snapshot: bool = True) -> tuple[dict[str, pd.Series], dict[str, dict]]:
    """Devuelve (series, metadatos). metadatos[codigo] = fuente + frescura."""
    hoy = dt.date.today()
    anios = list(range(hoy.year - anios_atras, hoy.year + 1))
    snapshot = _leer_snapshot() if usar_snapshot else {}
    series, meta = {}, {}

    for codigo, cfg in INDICADORES.items():
        s, fuente = pd.Series(dtype=float), None

        if bcch_token and codigo in SERIES_BCCH:
            try:
                s = descargar_bcch(SERIES_BCCH[codigo], bcch_token, f"{anios[0]}-01-01", hoy.isoformat())
                fuente = "Banco Central de Chile (API BDE)"
            except Exception:
                s = pd.Series(dtype=float)

        if s.empty:
            try:
                s = descargar_mindicador(codigo, anios)
                fuente = "mindicador.cl"
            except Exception:
                s = pd.Series(dtype=float)

        if s.empty and codigo in snapshot:
            s, fuente = snapshot[codigo], "snapshot guardado (APIs no disponibles)"

        s.name = codigo
        series[codigo] = s
        meta[codigo] = {"fuente": fuente or "sin datos", **estado_frescura(s, cfg["frecuencia"], hoy)}

    return series, meta
