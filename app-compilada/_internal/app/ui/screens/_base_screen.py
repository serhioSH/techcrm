# ============================================================
#  app/ui/screens/_base_screen.py
#  Clase base para todas las pantallas
# ============================================================
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class BaseScreen(QWidget):
    """
    Pantalla base con estilos comunes y metodo refrescar() a sobreescribir.
    """
    TITULO = "Pantalla"

    def __init__(self, db, auth, parent=None):
        super().__init__(parent)
        self._db   = db
        self._auth = auth
        self._usuario = auth.usuario_actual
        
        # CORRECCIÓN CRÍTICA: Crear Y establecer el layout explícitamente
        self._main_layout = QVBoxLayout()
        self.setLayout(self._main_layout)  # ← ESTO ES CRÍTICO

    def refrescar(self):
        """Llamado cada vez que se navega a esta pantalla."""
        pass

    def _header(self, titulo: str, color: str = "#06b6d4") -> QLabel:
        """Header mejorado con diseño moderno."""
        lbl = QLabel(titulo)
        lbl.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {color};
            padding: 16px 0;
            letter-spacing: 0.5px;
        """)
        return lbl

    def _base_stylesheet(self) -> str:
        """Stylesheet base OPTIMIZADO: sin gradientes complejos para bajo consumo."""
        return """
        /* Fondos y texto */
        QWidget {
            background: #0f172a;
            color: #e2e8f0;
            font-family: 'Segoe UI', 'Inter', sans-serif;
            font-size: 13px;
        }
        
        /* Botones: colores sólidos, sin gradientes */
        QPushButton {
            background: #3b82f6;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        QPushButton:hover {
            background: #60a5fa;
        }
        QPushButton:pressed {
            background: #1e40af;
        }
        
        /* Campos de entrada */
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
            background: #1e293b;
            color: #f1f5f9;
            border: 2px solid #334155;
            border-radius: 6px;
            padding: 8px 10px;
            font-size: 13px;
            selection-background-color: #06b6d4;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
            border: 2px solid #06b6d4;
            background: #0f172a;
        }
        QComboBox::drop-down {
            border: none;
            padding-right: 8px;
        }
        QComboBox::down-arrow {
            image: none;
            color: #06b6d4;
        }
        
        /* Tablas */
        QTableWidget {
            background: #1e293b;
            color: #e2e8f0;
            gridline-color: #334155;
            border: 1px solid #334155;
            border-radius: 4px;
            font-size: 13px;
        }
        QTableWidget::item {
            padding: 6px;
            border: none;
        }
        QTableWidget::item:selected {
            background: #06b6d4;
            color: #0f172a;
            font-weight: 600;
        }
        QTableWidget::item:hover {
            background: #334155;
        }
        QHeaderView::section {
            background: #0f172a;
            color: #06b6d4;
            padding: 10px;
            font-weight: 700;
            border: none;
            border-bottom: 2px solid #06b6d4;
        }
        
        /* CheckBox y RadioButton */
        QCheckBox, QRadioButton {
            color: #e2e8f0;
            spacing: 6px;
        }
        QCheckBox::indicator:unchecked,
        QRadioButton::indicator:unchecked {
            background: #1e293b;
            border: 2px solid #334155;
            border-radius: 3px;
        }
        QCheckBox::indicator:checked,
        QRadioButton::indicator:checked {
            background: #06b6d4;
            border: 2px solid #06b6d4;
        }
        
        /* Etiquetas */
        QLabel {
            color: #e2e8f0;
        }
        
        /* ScrollBar simplificado */
        QScrollBar:vertical {
            background: #1e293b;
            width: 10px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background: #334155;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover {
            background: #475569;
        }
        QScrollBar:horizontal {
            background: #1e293b;
            height: 10px;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background: #334155;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #475569;
        }
        
        /* Dialogo */
        QDialog {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
        }
        """
