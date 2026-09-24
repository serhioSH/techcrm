# -*- coding: utf-8 -*-
#  app/printing/printer_manager.py
#  Gestion de impresoras termicas en Windows (Punto 6)
# ============================================================
import sys
from typing import List


class PrinterManager:
    """
    Deteccion e impresion directa en impresoras termicas de Windows.
    El envio es RAW/ESC-POS, compatible con impresoras de 58 mm y 80 mm.
    """

    @staticmethod
    def listar_impresoras() -> List[str]:
        """Retorna la lista de impresoras instaladas en el sistema."""
        if sys.platform != "win32":
            return []
        try:
            import win32print
            impresoras = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            return [imp[2] for imp in impresoras]
        except Exception:
            return []

    @staticmethod
    def impresora_defecto() -> str:
        """Retorna el nombre de la impresora por defecto del sistema."""
        if sys.platform != "win32":
            return ""
        try:
            import win32print
            return win32print.GetDefaultPrinter()
        except Exception:
            return ""

    @staticmethod
    def imprimir_bytes(datos: bytes, nombre_impresora: str) -> bool:
        """
        Envia bytes crudos (ESC/POS) directamente a la impresora termica.
        Retorna True si la impresion fue exitosa.
        """
        if sys.platform != "win32":
            print(datos.decode("cp850", errors="replace"))
            return True
        try:
            import win32print
            manejador = win32print.OpenPrinter(nombre_impresora)
            try:
                win32print.StartDocPrinter(
                    manejador, 1, ("Comprobante POS", None, "RAW")
                )
                try:
                    win32print.StartPagePrinter(manejador)
                    win32print.WritePrinter(manejador, datos)
                    win32print.EndPagePrinter(manejador)
                finally:
                    win32print.EndDocPrinter(manejador)
            finally:
                win32print.ClosePrinter(manejador)
            return True
        except Exception as e:
            print(f"Error al imprimir: {e}")
            return False

    @staticmethod
    def imprimir_texto(texto: str, nombre_impresora: str) -> bool:
        """Imprime texto plano en la impresora (con avance y corte)."""
        datos = (texto + "\n\n\n").encode("cp850", errors="replace")
        return PrinterManager.imprimir_bytes(datos, nombre_impresora)

    @staticmethod
    def prueba_impresion(nombre_impresora: str) -> bool:
        """Imprime un ticket corto de prueba."""
        texto = (
            "================================\n"
            "     PRUEBA DE IMPRESION\n"
            "================================\n"
            " POS Comidas Rapidas\n"
            " Sistema funcionando OK\n"
            "================================\n"
        )
        return PrinterManager.imprimir_texto(texto, nombre_impresora)
