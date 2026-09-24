# ============================================================
#  app/printing/ticket_formatter.py
#  Utilidades de formato para tickets termicos
# ============================================================


def centrar(texto: str, ancho: int) -> str:
    return texto.center(ancho)


def alinear_dos_columnas(izq: str, der: str, ancho: int) -> str:
    espacios = ancho - len(izq) - len(der)
    if espacios < 1:
        espacios = 1
    return izq + " " * espacios + der


def separador(char: str = "-", ancho: int = 48) -> str:
    return char * ancho


def formatear_moneda(valor: float) -> str:
    return f"${valor:,.0f}"
