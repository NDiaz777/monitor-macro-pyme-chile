"""Configuración central: qué indicadores mostramos y cómo se interpretan.

Cada indicador tiene:
- nombre / unidad: para mostrar en pantalla.
- frecuencia: "diaria" o "mensual" (define cuándo un dato se considera viejo).
- tipo: "precio" -> las variaciones se miden en % ; "tasa" -> en puntos porcentuales (pp).
"""

INDICADORES = {
    "dolar": {"nombre": "Dólar observado", "unidad": "CLP", "frecuencia": "diaria", "tipo": "precio"},
    "euro": {"nombre": "Euro", "unidad": "CLP", "frecuencia": "diaria", "tipo": "precio"},
    "uf": {"nombre": "UF", "unidad": "CLP", "frecuencia": "diaria", "tipo": "precio"},
    "libra_cobre": {"nombre": "Cobre", "unidad": "USD/lb", "frecuencia": "diaria", "tipo": "precio"},
    "tpm": {"nombre": "Tasa de Política Monetaria", "unidad": "%", "frecuencia": "diaria", "tipo": "tasa"},
    "ipc": {"nombre": "IPC (var. mensual)", "unidad": "%", "frecuencia": "mensual", "tipo": "tasa"},
    "imacec": {"nombre": "Imacec (var. 12 meses)", "unidad": "%", "frecuencia": "mensual", "tipo": "tasa"},
    "tasa_desempleo": {"nombre": "Desempleo", "unidad": "%", "frecuencia": "mensual", "tipo": "tasa"},
}

# Máximo de días de antigüedad antes de marcar un dato como "desactualizado".
# Los mensuales se publican con rezago (el Imacec de septiembre sale a inicios de noviembre),
# por eso su umbral es más amplio.
MAX_DIAS_ANTIGUEDAD = {"diaria": 7, "mensual": 100}

# Fuente oficial opcional (Banco Central de Chile, API gratuita con registro).
# Se usa solo si existe el secreto BCCH_TOKEN. Verifica los códigos con scripts/buscar_series.py.
SERIES_BCCH = {
    "ipc": "F074.IPC.VAR.Z.Z.C.M",
}

# Meta de inflación del Banco Central de Chile: 3% anual, con rango de tolerancia ±1 pp.
META_INFLACION = 3.0
