# ============================================================
#  app/utils/helpers.py
#  Funciones de utilidad general
# ============================================================
from datetime import date, datetime, timedelta


def formato_moneda(valor: float) -> str:
    """Formatea un numero como moneda colombiana sin decimales."""
    return f"${valor:,.0f}".replace(",", ".")


def hoy() -> str:
    return date.today().isoformat()


def ayer() -> str:
    return (date.today() - timedelta(days=1)).isoformat()


def inicio_semana() -> str:
    hoy_dt = date.today()
    return (hoy_dt - timedelta(days=hoy_dt.weekday())).isoformat()


def inicio_mes() -> str:
    return date.today().replace(day=1).isoformat()


def fecha_hora_ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
