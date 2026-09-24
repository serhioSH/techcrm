# -*- coding: utf-8 -*-
#  app/ui/themes/colors.py
#  Paleta de colores centralizada para la aplicación
# ============================================================

class Colors:
    """Colores centralizados para toda la UI."""
    
    # Colores de fondo
    BG_PRIMARY = "#0f172a"      # Fondo principal oscuro
    BG_SECONDARY = "#1e293b"    # Fondo secundario (campos, tablas)
    BG_TERTIARY = "#16213e"     # Fondo terciario (deprecated, usar BG_SECONDARY)
    
    # Colores de texto
    TEXT_PRIMARY = "#e2e8f0"    # Texto principal (alto contraste)
    TEXT_SECONDARY = "#ccc"     # Texto secundario
    TEXT_MUTED = "#999"         # Texto mutedo (placeholder)
    TEXT_BRIGHT = "#fff"        # Texto blanco puro
    
    # Colores de acentos principales
    ACCENT_PRIMARY = "#06b6d4"  # Cyan (focus, headers)
    ACCENT_BLUE = "#3b82f6"     # Azul (botones primarios)
    
    # Colores para acciones
    COLOR_SUCCESS = "#27ae60"    # Verde (guardar, crear, positivo)
    COLOR_SUCCESS_HOVER = "#229954"
    COLOR_SUCCESS_PRESS = "#1e8449"
    
    COLOR_DANGER = "#e74c3c"     # Rojo (eliminar, error)
    COLOR_DANGER_HOVER = "#c0392b"
    
    COLOR_WARNING = "#f39c12"    # Naranja/Amarillo (advertencia)
    COLOR_WARNING_HOVER = "#e67e22"
    
    COLOR_INFO = "#3498db"       # Azul claro (información)
    
    # Colores para bordes
    BORDER_LIGHT = "#334155"     # Borde claro
    BORDER_DARK = "#0f172a"      # Borde oscuro
    
    # Deprecated: Colores antiguos (mantener para compatibilidad temporalmente)
    ORANGE_OLD = "#f5a623"       # DEPRECATED - usar COLOR_WARNING
    GREEN_OLD = "#2ecc71"        # DEPRECATED - usar COLOR_SUCCESS
    
    @staticmethod
    def get_button_style(color_bg: str, color_hover: str = None, color_press: str = None) -> str:
        """Genera estilo de botón genérico."""
        if color_hover is None:
            color_hover = color_bg
        if color_press is None:
            color_press = color_bg
        
        return f"""
            QPushButton {{
                background: {color_bg};
                color: #fff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background: {color_hover};
            }}
            QPushButton:pressed {{
                background: {color_press};
            }}
        """
    
    @staticmethod
    def get_input_style(bg: str = None) -> str:
        """Genera estilo de campo de entrada."""
        bg = bg or Colors.BG_SECONDARY
        return f"""
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
                background: {bg};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 2px solid {Colors.ACCENT_PRIMARY};
                background: {Colors.BG_PRIMARY};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
        """
