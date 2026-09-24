#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ============================================================
# TECHCRM POS - DIAGNÓSTICO DE SISTEMA
# ============================================================
# Este script verifica que todos los componentes necesarios
# estén disponibles para que TECHCRM POS funcione correctamente.
#
# Uso:
#   python diagnostico.py
#   o (después de compilar)
#   TECHCRM-POS-Diagnostico.exe
# ============================================================

import sys
import os
import platform
import importlib
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================
# ESTILOS Y COLORES PARA CONSOLA
# ============================================================
class Colores:
    """Códigos ANSI para colorear salida en terminal."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def desactivar_si_windows():
        """Windows CMD no soporta ANSI por defecto."""
        if platform.system() == 'Windows':
            # Intentar usar VT100 de Windows 10+
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                STD_OUTPUT_HANDLE = -11
                handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(handle, ctypes.byref(mode))
                mode.value |= 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(handle, mode)
            except:
                # Si falla, desactivar colores
                Colores.HEADER = ''
                Colores.BLUE = ''
                Colores.CYAN = ''
                Colores.GREEN = ''
                Colores.YELLOW = ''
                Colores.RED = ''
                Colores.RESET = ''
                Colores.BOLD = ''

Colores.desactivar_si_windows()

# ============================================================
# FUNCIONES DE LOGGING
# ============================================================
def info(mensaje: str):
    """Imprimir mensaje informativo."""
    print(f"{Colores.BLUE}[INFO]{Colores.RESET} {mensaje}")

def ok(mensaje: str):
    """Imprimir mensaje de éxito."""
    print(f"{Colores.GREEN}[OK]{Colores.RESET} {mensaje}")

def aviso(mensaje: str):
    """Imprimir mensaje de aviso."""
    print(f"{Colores.YELLOW}[AVISO]{Colores.RESET} {mensaje}")

def error(mensaje: str):
    """Imprimir mensaje de error."""
    print(f"{Colores.RED}[ERROR]{Colores.RESET} {mensaje}")

def titulo(texto: str):
    """Imprimir título centrado."""
    ancho = 60
    print(f"\n{Colores.BOLD}{Colores.CYAN}{'=' * ancho}{Colores.RESET}")
    print(f"{Colores.BOLD}{Colores.CYAN}{texto.center(ancho)}{Colores.RESET}")
    print(f"{Colores.BOLD}{Colores.CYAN}{'=' * ancho}{Colores.RESET}\n")

def seccion(texto: str):
    """Imprimir encabezado de sección."""
    print(f"\n{Colores.BOLD}{Colores.CYAN}{texto}{Colores.RESET}")
    print(f"{Colores.CYAN}{'─' * 50}{Colores.RESET}")

# ============================================================
# VERIFICACIONES
# ============================================================
class Diagnostico:
    """Ejecutor de diagnósticos del sistema."""
    
    def __init__(self):
        self.errores: List[str] = []
        self.avisos: List[str] = []
        self.ok_items: List[str] = []
    
    def verificar_python(self) -> bool:
        """Verificar versión de Python."""
        info(f"Versión de Python: {sys.version}")
        
        version_requerida = (3, 10)
        version_actual = sys.version_info[:2]
        
        if version_actual >= version_requerida:
            ok(f"Python {version_actual[0]}.{version_actual[1]} compatible")
            self.ok_items.append(f"Python {version_actual[0]}.{version_actual[1]}")
            return True
        else:
            error(f"Python {version_requerida[0]}.{version_requerida[1]} o superior requerido")
            self.errores.append(f"Python {version_requerida[0]}.{version_requerida[1]} no encontrado")
            return False
    
    def verificar_so(self) -> bool:
        """Verificar sistema operativo."""
        so = platform.system()
        info(f"Sistema Operativo: {so} {platform.release()}")
        
        if so == 'Windows':
            arquitectura = platform.architecture()[0]
            info(f"Arquitectura: {arquitectura}")
            
            if '64bit' in arquitectura:
                ok("Windows x64 detectado")
                self.ok_items.append(f"Windows {platform.release()} (64-bit)")
                return True
            else:
                aviso("Sistema de 32 bits detectado (no recomendado)")
                self.avisos.append("TECHCRM POS funciona mejor en Windows 64-bit")
                return True
        else:
            aviso(f"Sistema operativo: {so} (no completamente soportado)")
            self.avisos.append(f"TECHCRM POS fue diseñado para Windows")
            return False
    
    def verificar_modulo(self, nombre: str, importar_como: str = None) -> bool:
        """Verificar si un módulo está instalado."""
        if importar_como is None:
            importar_como = nombre
        
        try:
            modulo = importlib.import_module(importar_como)
            
            # Intentar obtener versión
            version = getattr(modulo, '__version__', 'desconocida')
            ok(f"{nombre}: {version}")
            self.ok_items.append(nombre)
            return True
        except ImportError:
            error(f"{nombre} no encontrado")
            self.errores.append(f"Módulo '{nombre}' no instalado")
            return False
        except Exception as e:
            error(f"{nombre}: Error - {str(e)}")
            self.errores.append(f"Error al verificar {nombre}: {str(e)}")
            return False
    
    def verificar_modulos(self):
        """Verificar todos los módulos requeridos."""
        seccion("Verificando Dependencias de Python")
        
        modulos_requeridos = [
            ('PySide6', 'PySide6'),
            ('SQLite3', 'sqlite3'),
            ('bcrypt', 'bcrypt'),
            ('requests', 'requests'),
            ('Pillow', 'PIL'),
            ('openpyxl', 'openpyxl'),
        ]
        
        for nombre, importar_como in modulos_requeridos:
            self.verificar_modulo(nombre, importar_como)
    
    def verificar_estructura_carpetas(self):
        """Verificar que la estructura de carpetas sea correcta."""
        seccion("Verificando Estructura de Carpetas")
        
        carpetas_requeridas = [
            'app/database',
            'app/models',
            'app/services',
            'app/ui',
            'app/ui/screens',
            'app/ui/widgets',
            'app/ui/themes',
            'app/printing',
            'app/utils',
            'data',
            'comprobantes',
        ]
        
        dir_proyecto = os.path.dirname(os.path.abspath(__file__))
        
        for carpeta in carpetas_requeridas:
            ruta_carpeta = os.path.join(dir_proyecto, carpeta)
            if os.path.isdir(ruta_carpeta):
                ok(f"app/{carpeta.split('/', 1)[1] if '/' in carpeta else carpeta}")
                self.ok_items.append(f"Carpeta: {carpeta}")
            else:
                aviso(f"Carpeta no encontrada: {carpeta}")
                self.avisos.append(f"Carpeta {carpeta} no existe (puede ser normal en distribución)")
    
    def verificar_base_datos(self):
        """Verificar base de datos SQLite."""
        seccion("Verificando Base de Datos")
        
        dir_proyecto = os.path.dirname(os.path.abspath(__file__))
        ruta_db = os.path.join(dir_proyecto, 'data', 'pos.db')
        
        if os.path.isfile(ruta_db):
            try:
                # Intentar conectar a la BD
                conexion = sqlite3.connect(ruta_db)
                cursor = conexion.cursor()
                
                # Verificar tablas críticas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tablas = cursor.fetchall()
                
                if len(tablas) > 0:
                    ok(f"Base de datos encontrada ({len(tablas)} tablas)")
                    self.ok_items.append("Base de datos SQLite")
                    
                    # Listar tablas
                    info("Tablas detectadas:")
                    for tabla in tablas:
                        print(f"  ├─ {tabla[0]}")
                else:
                    aviso("Base de datos existe pero está vacía")
                    self.avisos.append("BD vacía - se inicializará al ejecutar")
                
                conexion.close()
            except Exception as e:
                error(f"Error al conectar a BD: {str(e)}")
                self.errores.append(f"No se pudo conectar a la BD: {str(e)}")
        else:
            aviso(f"Base de datos no encontrada en {ruta_db}")
            aviso("Se creará automáticamente al ejecutar TECHCRM POS")
            self.avisos.append("BD será creada al iniciar la aplicación")
    
    def verificar_comprobantes(self):
        """Verificar carpeta de comprobantes."""
        seccion("Verificando Comprobantes")
        
        dir_proyecto = os.path.dirname(os.path.abspath(__file__))
        ruta_comprobantes = os.path.join(dir_proyecto, 'comprobantes')
        
        if os.path.isdir(ruta_comprobantes):
            archivos = os.listdir(ruta_comprobantes)
            
            if len(archivos) > 0:
                ok(f"Carpeta de comprobantes encontrada ({len(archivos)} archivo(s))")
                self.ok_items.append("Carpeta de comprobantes")
            else:
                ok("Carpeta de comprobantes lista (vacía)")
                self.ok_items.append("Carpeta de comprobantes")
        else:
            aviso("Carpeta de comprobantes no encontrada")
            aviso("Se creará al ejecutar TECHCRM POS")
            self.avisos.append("Carpeta de comprobantes será creada automáticamente")
    
    def verificar_impresora(self):
        """Verificar disponibilidad de impresoras."""
        seccion("Verificando Sistema de Impresión")
        
        try:
            if platform.system() == 'Windows':
                import win32print
                impresoras = win32print.EnumPrinters(2)
                
                if len(impresoras) > 0:
                    ok(f"Sistema de impresión disponible ({len(impresoras)} impresora(s))")
                    info("Impresoras detectadas:")
                    for impresora in impresoras:
                        print(f"  ├─ {impresora[2]}")
                    self.ok_items.append("Sistema de impresión")
                else:
                    aviso("No se detectaron impresoras")
                    self.avisos.append("TECHCRM POS puede funcionar sin impresora (modo software)")
            else:
                aviso("Verificación de impresoras no disponible en este SO")
                self.avisos.append("Impresora no verificada en este SO")
        except ImportError:
            aviso("Módulo win32print no disponible")
            aviso("Se usará API genérica de impresión")
            self.avisos.append("Impresora será detectada al ejecutar")
        except Exception as e:
            aviso(f"No se pudieron detectar impresoras: {str(e)}")
            self.avisos.append(f"Impresora será detectada al ejecutar")
    
    def ejecutar_diagnostico_completo(self):
        """Ejecutar todos los diagnósticos."""
        titulo("TECHCRM POS - DIAGNÓSTICO DEL SISTEMA")
        
        info(f"Iniciando diagnóstico...\n")
        
        # Verificaciones principales
        self.verificar_python()
        print()
        self.verificar_so()
        print()
        self.verificar_modulos()
        print()
        self.verificar_estructura_carpetas()
        print()
        self.verificar_base_datos()
        print()
        self.verificar_comprobantes()
        print()
        self.verificar_impresora()
        
        # Resumen final
        self.mostrar_resumen()
    
    def mostrar_resumen(self):
        """Mostrar resumen de diagnóstico."""
        seccion("RESUMEN DEL DIAGNÓSTICO")
        
        print(f"{Colores.GREEN}✓ Verificaciones exitosas:{Colores.RESET} {len(self.ok_items)}")
        for item in self.ok_items[:5]:  # Mostrar primeros 5
            print(f"  ├─ {item}")
        if len(self.ok_items) > 5:
            print(f"  └─ ... y {len(self.ok_items) - 5} más")
        
        if self.avisos:
            print(f"\n{Colores.YELLOW}⚠ Avisos:{Colores.RESET} {len(self.avisos)}")
            for aviso_item in self.avisos[:3]:
                print(f"  ├─ {aviso_item}")
            if len(self.avisos) > 3:
                print(f"  └─ ... y {len(self.avisos) - 3} más")
        
        if self.errores:
            print(f"\n{Colores.RED}✗ Errores:{Colores.RESET} {len(self.errores)}")
            for error_item in self.errores:
                print(f"  ├─ {error_item}")
        
        # Veredicto final
        print(f"\n{Colores.BOLD}{'─' * 50}{Colores.RESET}")
        
        if not self.errores:
            print(f"{Colores.GREEN}{Colores.BOLD}✓ DIAGNÓSTICO EXITOSO{Colores.RESET}")
            print(f"{Colores.GREEN}TECHCRM POS está listo para ejecutarse.{Colores.RESET}")
            return 0
        else:
            print(f"{Colores.RED}{Colores.BOLD}✗ DIAGNÓSTICO COMPLETADO CON ERRORES{Colores.RESET}")
            print(f"{Colores.RED}Por favor, revisa los errores anteriores.{Colores.RESET}")
            return 1


# ============================================================
# PUNTO DE ENTRADA
# ============================================================
def main():
    """Función principal."""
    diagnostico = Diagnostico()
    codigo_salida = diagnostico.ejecutar_diagnostico_completo()
    
    print(f"\n{Colores.CYAN}Presiona ENTER para finalizar...{Colores.RESET}")
    input()
    
    return codigo_salida


if __name__ == '__main__':
    sys.exit(main())
