"""Eval de la capa de IA: corre los 4 perfiles y mide calidad, latencia y tokens.

Uso (PowerShell):  $env:GEMINI_API_KEY="tu_key"; python scripts/evaluar_ia.py
Resultado: docs/eval_resultados.csv + resumen en pantalla (cópialo al README).
Gasta ~4-8 llamadas del free tier.
"""
import csv
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.datos import cargar_indicadores  # noqa: E402
from src.ia import PERFILES, construir_prompt, generar_insight, verificar_cifras  # noqa: E402
from src.kpis import calcular_todos, generar_senales  # noqa: E402

REPETICIONES = int(os.getenv("REPETICIONES", "1"))
series, meta = cargar_indicadores(3)
kpis = calcular_todos(series)
senales = generar_senales(kpis)
filas = []
for perfil in PERFILES:
    for i in range(REPETICIONES):
        prompt = construir_prompt(kpis, senales, meta, perfil)
        r = generar_insight(prompt, os.environ["GEMINI_API_KEY"], os.getenv("GEMINI_MODEL"))
        v = verificar_cifras(r["texto"], kpis)
        palabras = len(r["texto"].split())
        secciones = sum(h in r["texto"] for h in ("Resumen", "señales", "negocio", "vigilar"))
        filas.append({"perfil": perfil, "rep": i + 1, "modelo": r["modelo"],
                      "latencia_s": r["latencia_s"], "tokens_in": r["tokens_entrada"],
                      "tokens_out": r["tokens_salida"], "palabras": palabras,
                      "secciones_ok": f"{secciones}/4", "pct_cifras_verificadas": v["pct_verificadas"],
                      "no_verificadas": " ".join(v["no_verificadas"])})
        print(filas[-1])
        time.sleep(7)  # respeta el límite de solicitudes por minuto del free tier

salida = RAIZ / "docs" / "eval_resultados.csv"
with open(salida, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=filas[0].keys())
    w.writeheader()
    w.writerows(filas)

n = len(filas)
print("\n=== RESUMEN (pegar en el README) ===")
print(f"Corridas: {n}")
print(f"Cifras verificadas (promedio): {sum(f['pct_cifras_verificadas'] for f in filas) / n:.1f}%")
print(f"Latencia promedio: {sum(f['latencia_s'] for f in filas) / n:.2f} s")
print(f"Tokens promedio entrada/salida: {sum(f['tokens_in'] or 0 for f in filas) / n:.0f} / "
      f"{sum(f['tokens_out'] or 0 for f in filas) / n:.0f}")
print(f"Respuestas con formato completo: {sum(f['secciones_ok'] == '4/4' for f in filas)}/{n}")
