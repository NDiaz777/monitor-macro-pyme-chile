"""Descarga los indicadores y guarda data/snapshot.csv (respaldo si las APIs caen).

Uso:  python scripts/actualizar_snapshot.py
Lo ejecuta también GitHub Actions todos los días (.github/workflows/snapshot.yml).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.datos import cargar_indicadores, guardar_snapshot  # noqa: E402

series, meta = cargar_indicadores(3, bcch_token=os.getenv("BCCH_TOKEN"), usar_snapshot=False)
guardar_snapshot(series)
for c, m in meta.items():
    estado = "OK " if m["fresco"] else "VIEJO"
    print(f"[{estado}] {c:15s} {len(series[c]):5d} obs · último {m['ultima_fecha']} · {m['fuente']}")
