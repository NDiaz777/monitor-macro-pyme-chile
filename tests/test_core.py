import datetime as dt
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import datos  # noqa: E402
from src.ia import PERFILES, construir_prompt, verificar_cifras  # noqa: E402
from src.kpis import calcular_kpis, calcular_todos, generar_senales  # noqa: E402


def serie_diaria(inicio, valores):
    idx = pd.date_range(inicio, periods=len(valores), freq="D")
    return pd.Series(valores, index=idx, dtype=float)


def test_kpis_precio_en_porcentaje():
    s = serie_diaria("2025-01-01", [900.0] * 400 + [990.0])
    k = calcular_kpis(s, "dolar")
    assert k["ultimo"] == 990.0
    assert k["cambio_30d"] == 10.0          # +10%
    assert k["unidad_cambio"] == "%"
    assert k["percentil_periodo"] == 100


def test_kpis_tasa_en_puntos_porcentuales():
    s = serie_diaria("2025-01-01", [5.0] * 400 + [4.5])
    k = calcular_kpis(s, "tpm")
    assert k["cambio_12m"] == -0.5
    assert k["unidad_cambio"] == "pp"


def test_ipc_acumulado_12m():
    idx = pd.date_range("2025-01-01", periods=12, freq="MS")
    k = calcular_kpis(pd.Series([0.3] * 12, index=idx), "ipc")
    assert abs(k["acumulado_12m"] - 3.66) < 0.01


def test_senales_dolar_y_tpm():
    series = {"dolar": serie_diaria("2025-01-01", [900.0] * 400 + [950.0]),
              "tpm": serie_diaria("2025-01-01", [5.0] * 400 + [4.5])}
    textos = " ".join(s["texto"] for s in generar_senales(calcular_todos(series)))
    assert "dólar subió" in textos and "TPM bajó" in textos


def test_frescura():
    s = serie_diaria("2025-12-01", [1.0])
    assert datos.estado_frescura(s, "mensual", dt.date(2026, 11, 19))["fresco"] is False
    assert datos.estado_frescura(s, "mensual", dt.date(2026, 1, 15))["fresco"] is True


def test_parseo_mindicador(monkeypatch):
    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return {"serie": [{"fecha": "2026-11-19T03:00:00.000Z", "valor": 1002.07},
                              {"fecha": "2026-11-18T03:00:00.000Z", "valor": 996.68}]}
    monkeypatch.setattr(datos.requests, "get", lambda *a, **k: R())
    s = datos.descargar_mindicador("dolar", [2026])
    assert s.index[-1] == pd.Timestamp("2026-11-19") and s.iloc[-1] == 1002.07


def test_verificar_cifras_detecta_inventos():
    kpis = {"dolar": {"ultimo": 1002.07, "cambio_30d": 3.2}}
    ok = verificar_cifras("El dólar está en $1.002,07 y subió 3,2% en 30 días.", kpis)
    assert ok["pct_verificadas"] == 100.0
    malo = verificar_cifras("El dólar llegará a 1.100 y subió 3,2%.", kpis)
    assert malo["no_verificadas"] == ["1.100"]


def test_prompt_marca_desactualizados():
    kpis = {"ipc": {"ultimo": 0.3}}
    p = construir_prompt(kpis, [], {"ipc": {"fresco": False}}, list(PERFILES)[0])
    assert '"desactualizado": true' in p
