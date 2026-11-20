"""Busca códigos de series en el Banco Central (para verificar SERIES_BCCH en src/config.py).

Uso:  set BCCH_TOKEN=tu_token   (Windows)   y luego   python scripts/buscar_series.py IPC
"""
import os
import sys

import requests

token, palabra = os.environ["BCCH_TOKEN"], (sys.argv[1] if len(sys.argv) > 1 else "IPC").lower()
for freq in ("DAILY", "MONTHLY"):
    r = requests.get("https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx",
                     params={"token": token, "function": "SearchSeries", "frequency": freq}, timeout=30)
    for s in r.json().get("SeriesInfos", []):
        if palabra in (s.get("spanishTitle") or "").lower():
            print(f"{freq:8s} {s['seriesId']:35s} {s['spanishTitle']}")
