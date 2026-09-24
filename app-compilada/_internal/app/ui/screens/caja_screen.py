# -*- coding: utf-8 -*-
#  app/ui/screens/caja_screen.py
#  Caja: apertura, cierre, totales en vivo e historicos (Punto 9)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
    QInputDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PySide6.QtGui import QColor
from app.ui.screens._base_screen import BaseScreen
from app.services.caja_service import CajaService
from app.services.permisos import Permisos
from app.utils.helpers import formato_moneda


class CajaScreen(BaseScreen):
    """
    Jornada de caja: apertura con efectivo inicial, totales en vivo
    (efectivo/transferencias aparte), cierre con diferencia clara
    (faltante/sobrante/cuadra) e historicos de cierres para el ADMIN.
    """

    TITULO = "Caja"

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._cajas = CajaService(db, auth)
        self._last_cierres_hash = None  # OPTIMIZED (Task 7): Cache for diffing
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        layout = self._main_layout
        layout.addWidget(self._header("💰  Caja de la jornada"))

        self._lbl_estado = QLabel("")
        self._lbl_estado.setStyleSheet(
            "font-size:15px; font-weight:bold; color:#f5a623;"
        )
        layout.addWidget(self._lbl_estado)

        self._detalles = QLabel("")
        self._detalles.setStyleSheet("color:#ccc; font-size:13px;")
        self._detalles.setWordWrap(True)
        layout.addWidget(self._detalles)

        botones = QHBoxLayout()
        self._btn_abrir = QPushButton("Abrir caja")
        self._btn_abrir.clicked.connect(self._abrir)
        self._btn_cerrar = QPushButton("Cerrar caja")
        self._btn_cerrar.clicked.connect(self._cerrar)
        self._btn_refrescar = QPushButton("Refrescar")
        self._btn_refrescar.clicked.connect(self.refrescar)
        for boton in (self._btn_abrir, self._btn_cerrar, self._btn_refrescar):
            botones.addWidget(boton)
        botones.addStretch()
        layout.addLayout(botones)

        self._lbl_aviso = QLabel("")
        self._lbl_aviso.setStyleSheet("color:#888; font-size:12px;")
        layout.addWidget(self._lbl_aviso)

        self._lbl_historial = QLabel("HISTÓRICOS DE CIERRES DE CAJA")
        self._lbl_historial.setStyleSheet(
            "color:#f5a623; font-weight:bold; font-size:12px;"
        )
        layout.addWidget(self._lbl_historial)

        self._tabla_cierres = QTableWidget(0, 8)
        self._tabla_cierres.setHorizontalHeaderLabels([
            "Apertura", "Cierre", "Responsable", "Inicial",
            "Efectivo", "Transfer.", "Total", "Diferencia",
        ])
        self._tabla_cierres.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_cierres.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        layout.addWidget(self._tabla_cierres)

    # ------------------------------------------------------
    def refrescar(self):
        """Estado de la jornada + historicos de cierres."""
        puede = self._auth.puede(Permisos.ABRIR_CERRAR_CAJA)
        caja = self._cajas.caja_abierta()
        if caja is None:
            self._lbl_estado.setText("NO HAY CAJA ABIERTA")
            self._detalles.setText(
                "Un ADMIN debe abrir la caja para que el sistema permita cobrar.\n"
                "Las ventas cobradas solo se registran dentro de una jornada de caja."
            )
            self._btn_abrir.setEnabled(puede)
            self._btn_cerrar.setEnabled(False)
        else:
            resumen = self._cajas.actualizar_totales(caja["id"])
            self._lbl_estado.setText("CAJA ABIERTA")
            self._detalles.setText(
                f"Responsable: {caja.get('usuario_nombre', '-')}\n"
                f"Apertura: {caja.get('fecha_apertura', '-')}\n"
                f"Efectivo inicial: {formato_moneda(resumen['monto_inicial'])}\n"
                f"Ventas en efectivo: {formato_moneda(resumen['total_efectivo'])}\n"
                f"Ventas por transferencia (aparte): "
                f"{formato_moneda(resumen['total_transferencia'])}\n"
                f"Total vendido: {formato_moneda(resumen['total_general'])}\n"
                f"EFECTIVO ESPERADO EN CAJA: "
                f"{formato_moneda(resumen['efectivo_esperado'])}"
            )
            self._btn_abrir.setEnabled(False)
            self._btn_cerrar.setEnabled(puede)

        self._lbl_aviso.setText(
            "" if puede else "Solo el ADMIN puede abrir o cerrar la caja."
        )
        self._cargar_historial()

    def _cargar_historial(self):
        """OPTIMIZED (Task 7): Only rebuild table if data changed."""
        try:
            cierres = self._cajas.historial()
        except PermissionError:
            self._lbl_historial.setVisible(False)
            self._tabla_cierres.setVisible(False)
            return
        self._lbl_historial.setVisible(True)
        self._tabla_cierres.setVisible(True)
        
        # OPTIMIZED: Hash cierres to skip re-render if unchanged
        import hashlib
        cierres_str = str(sorted((c["id"], c.get("fecha_cierre")) for c in cierres if "id" in c))
        current_hash = hashlib.md5(cierres_str.encode()).hexdigest()
        
        if current_hash == self._last_cierres_hash:
            # Data unchanged; skip table rebuild
            return
        
        self._last_cierres_hash = current_hash
        
        self._tabla_cierres.setRowCount(len(cierres))
        for fila, c in enumerate(cierres):
            apertura = (c.get("fecha_apertura") or "-").split(" ")[0]
            cierre = (
                c.get("fecha_cierre").split(" ")[0]
                if c.get("fecha_cierre")
                else "en curso"
            )
            valores = [
                apertura,
                cierre,
                c.get("usuario_nombre", "-"),
                formato_moneda(c.get("monto_inicial", 0)),
                formato_moneda(c.get("total_efectivo", 0)),
                formato_moneda(c.get("total_transferencia", 0)),
                formato_moneda(c.get("total_general", 0)),
                formato_moneda(c.get("diferencia") or 0),
            ]
            for columna, texto in enumerate(valores):
                item = QTableWidgetItem(texto)
                if columna == 7:
                    diferencia = float(c.get("diferencia") or 0)
                    if diferencia > 0:
                        item.setForeground(QColor("#e74c3c"))   # faltante
                        item.setText(f"{texto} (FALTANTE)")
                    elif diferencia < 0:
                        item.setForeground(QColor("#2ecc71"))   # sobrante
                        item.setText(f"{texto} (SOBRANTE)")
                    else:
                        item.setForeground(QColor("#ccc"))
                        item.setText(f"{texto} (CUADRA)")
                self._tabla_cierres.setItem(fila, columna, item)

    # ------------------------------------------------------
    # Apertura / cierre
    # ------------------------------------------------------
    def _abrir(self):
        monto, ok = QInputDialog.getDouble(
            self, "Abrir caja", "Efectivo inicial en caja:",
            0, 0, 99999999, 0
        )
        if not ok:
            return
        try:
            self._cajas.abrir(self._usuario.id, monto)
        except PermissionError as e:
            QMessageBox.warning(self, "Permiso denegado", str(e))
            return
        except Exception as e:
            QMessageBox.warning(self, "No se pudo abrir la caja", str(e))
            return
        self.refrescar()

    def _cerrar(self):
        caja = self._cajas.caja_abierta()
        if not caja:
            return
        resumen = self._cajas.actualizar_totales(caja["id"])
        contado, ok = QInputDialog.getDouble(
            self, "Cerrar caja",
            f"Efectivo esperado: {formato_moneda(resumen['efectivo_esperado'])}\n\n"
            "Efectivo contado:",
            resumen["efectivo_esperado"], 0, 99999999, 0
        )
        if not ok:
            return
        
        # Diálogo para materias primas
        materias_primas, ok_mp = QInputDialog.getMultiLineText(
            self, "Materias Primas",
            "Registre el estado de materias primas al cierre:"
        )
        if not ok_mp:
            return
        
        # Diálogo para observaciones
        observaciones, ok_obs = QInputDialog.getMultiLineText(
            self, "Observaciones",
            "Notas del cierre (opcional):"
        )
        if not ok_obs:
            return
        
        # Combinar materias primas y observaciones
        nota_completa = f"Materias Primas:\n{materias_primas}\n\nObservaciones:\n{observaciones}"
        
        try:
            resultado = self._cajas.cerrar(caja["id"], contado, nota_completa)
        except PermissionError as e:
            QMessageBox.warning(self, "Permiso denegado", str(e))
            return
        except Exception as e:
            QMessageBox.warning(self, "No se pudo cerrar la caja", str(e))
            return

        diferencia = resultado["diferencia"]
        if diferencia > 0:
            estado = "FALTANTE"
        elif diferencia < 0:
            estado = "SOBRANTE"
        else:
            estado = "CUADRA"
        QMessageBox.information(
            self, "Cierre de caja",
            f"Efectivo esperado: {formato_moneda(resultado['efectivo_esperado'])}\n"
            f"Efectivo contado: {formato_moneda(contado)}\n"
            f"Diferencia: {formato_moneda(abs(diferencia))} ({estado})\n\n"
            "✓ Inventario guardado."
        )
        self.refrescar()

