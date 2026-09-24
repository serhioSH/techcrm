# -*- coding: utf-8 -*-
#  app/printing/escpos.py
#  Utilidades ESC/POS: logo rasterizado y ticket crudo (Punto 6)
#  OPTIMIZADO: Caché de logos para bajo consumo de recursos
# ============================================================
import os
from typing import Optional

ESC = b"\x1b"
GS = b"\x1d"

INICIO = ESC + b"@"                      # reinicializar impresora
CORTE = GS + b"V" + b"A" + b"\x10"       # corte parcial de papel
AVANCE = b"\n\n\n"                       # avance antes del corte

# Ancho maximo de imagen segun el papel (puntos de impresion)
ANCHO_PIXELES = {"58": 384, "80": 576}

# Caché de logos procesados (ruta -> bytes ESC/POS)
# Evita recargar y reprocesar el logo en cada impresión
_cache_logos = {}


def _cargar_logo_monocromo(ruta, ancho_max):
    """
    Carga el logo, lo reduce al ancho maximo y lo vuelve monocromo.
    OPTIMIZADO: PIL se importa solo cuando se necesita.
    """
    if not ruta or not os.path.exists(ruta):
        return None
    try:
        # Importación lazy de PIL (solo cuando hay logo)
        from PIL import Image
        
        # Abrir con context manager para liberar memoria inmediatamente
        with Image.open(ruta) as img:
            imagen = img.convert("L")
            
            # Reducir tamaño si excede el máximo
            if imagen.width > ancho_max:
                alto = max(1, round(imagen.height * ancho_max / imagen.width))
                imagen = imagen.resize((ancho_max, alto), Image.Resampling.LANCZOS)
            
            # 0 = negro (se imprime), 255 = blanco
            # Usar umbral para convertir a monocromo
            return imagen.point(lambda valor: 0 if valor < 128 else 255).convert("1")
    except Exception:
        return None


def logo_escpos(ruta_logo, ancho_max=576) -> bytes:
    """
    Convierte el logo a raster ESC/POS (comando GS v 0).
    Bit 1 = punto impreso. Retorna b'' si no se puede usar el logo.
    OPTIMIZADO: Usa caché para evitar reprocesar el logo.
    """
    # Clave de caché: ruta + ancho
    cache_key = f"{ruta_logo}:{ancho_max}"
    
    # Verificar caché primero
    if cache_key in _cache_logos:
        return _cache_logos[cache_key]
    
    # Cargar y procesar logo
    imagen = _cargar_logo_monocromo(ruta_logo, ancho_max)
    if imagen is None:
        _cache_logos[cache_key] = b""
        return b""
    
    ancho, alto = imagen.size
    bytes_por_fila = (ancho + 7) // 8
    pixeles = list(imagen.getdata())
    
    # Generar datos ESC/POS
    datos = bytearray()
    for y in range(alto):
        fila = bytearray(bytes_por_fila)
        for x in range(ancho):
            if pixeles[y * ancho + x] == 0:      # negro -> imprimir
                fila[x // 8] |= 0x80 >> (x % 8)
        datos += fila
    
    x_l = bytes_por_fila % 256
    x_h = bytes_por_fila // 256
    y_l = alto % 256
    y_h = alto // 256
    
    resultado = GS + b"v0" + bytes([0, x_l, x_h, y_l, y_h]) + bytes(datos)
    
    # Guardar en caché
    _cache_logos[cache_key] = resultado
    
    return resultado


def limpiar_cache_logos():
    """Limpia el caché de logos (útil si se cambia el logo en configuración)."""
    global _cache_logos
    _cache_logos.clear()


def construir_ticket(texto: str, ruta_logo: Optional[str] = None,
                     ancho_mm: str = "80") -> bytes:
    """
    Arma los bytes crudos del comprobante:
    reinicio + logo (si esta configurado) + texto + avance + corte.
    OPTIMIZADO: Usa caché de logos.
    """
    ancho_max = ANCHO_PIXELES.get(str(ancho_mm), 576)
    salida = bytearray(INICIO)
    
    if ruta_logo and os.path.exists(ruta_logo):
        salida += logo_escpos(ruta_logo, ancho_max)
    
    salida += texto.encode("cp850", errors="replace")
    salida += AVANCE
    salida += CORTE
    
    return bytes(salida)

