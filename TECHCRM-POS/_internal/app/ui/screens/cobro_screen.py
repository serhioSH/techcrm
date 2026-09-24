# -*- coding: utf-8 -*-
#  app/ui/screens/cobro_screen.py
#  Pantalla de cobro: efectivo (con cambio) / transferencia (Punto 5)
# ============================================================
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from app.services.cobro_service import CobroService
from app.utils.helpers import formato_moneda


class DialogoCobro(QDialog):
    """
    Pantalla de cobro:
        TOTAL A PAGAR
        [ EFECTIVO ]  [ TRANSFERENCIA ]
    En efectivo solicita el valor recibido y calcula el cambio.
    """

    def __init__(self, db, auth, venta_id, mesa_nombre="", parent=None):
        super().__init__(parent)
        self._cobro = CobroService(db, auth)
        self._venta_id = venta_id
        self.resultado = None
        self._resumen = None
        self._error_inicial = ""
        self._total = 0.0
        self._setup_ui(mesa_nombre)

    def _setup_ui(self, mesa_nombre):
        self.setWindowTitle("Cobrar")
        self.setModal(True)
        self.setMinimumWidth(430)
        self.setStyleSheet(self._stylesheet())

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        try:
            self._resumen = self._cobro.resumen_cobro(self._venta_id)
            self._total = self._resumen["total"]
        except ValueError as e:
            self._error_inicial = str(e)

        nombre_mesa = mesa_nombre or (
            self._resumen["mesa_nombre"] if self._resumen else "-"
        )
        consecutivo = self._resumen["consecutivo"] if self._resumen else "-"

        lbl_mesa = QLabel(f"Mesa: {nombre_mesa}     Comprobante #{consecutivo}")
        lbl_mesa.setStyleSheet("color:#aaa; font-size:13px;")
        layout.addWidget(lbl_mesa)

        lbl_pagar = QLabel("TOTAL A PAGAR")
        lbl_pagar.setAlignment(Qt.AlignCenter)
        lbl_pagar.setStyleSheet("color:#888; font-size:12px;")
        layout.addWidget(lbl_pagar)

        self._lbl_total = QLabel(formato_moneda(self._total))
        self._lbl_total.setAlignment(Qt.AlignCenter)
        self._lbl_total.setStyleSheet(
            "color:#2ecc71; font-size:30px; font-weight:bold;"
        )
        layout.addWidget(self._lbl_total)

        metodos = QHBoxLayout()
        self._btn_efectivo = QPushButton("EFECTIVO")
        self._btn_transferencia = QPushButton("TRANSFERENCIA")
        self._btn_mixto = QPushButton("EFECTIVO +\nTRANSFERENCIA")
        for boton in (self._btn_efectivo, self._btn_transferencia, self._btn_mixto):
            boton.setCheckable(True)
            boton.setMinimumHeight(44)
            metodos.addWidget(boton)
        self._btn_efectivo.clicked.connect(
            lambda: self._seleccionar_metodo("EFECTIVO")
        )
        self._btn_transferencia.clicked.connect(
            lambda: self._seleccionar_metodo("TRANSFERENCIA")
        )
        self._btn_mixto.clicked.connect(
            lambda: self._seleccionar_metodo("MIXTO")
        )
        layout.addLayout(metodos)

        self._panel_efectivo = QFrame()
        panel_layout = QVBoxLayout(self._panel_efectivo)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Para EFECTIVO simple
        panel_layout.addWidget(QLabel("Valor recibido:"))
        self._txt_recibido = QLineEdit()
        self._txt_recibido.setPlaceholderText("0")
        self._txt_recibido.textChanged.connect(self._actualizar_cambio)
        panel_layout.addWidget(self._txt_recibido)
        
        self._lbl_cambio = QLabel("Cambio: $0")
        self._lbl_cambio.setStyleSheet(
            "color:#f5a623; font-size:18px; font-weight:bold;"
        )
        panel_layout.addWidget(self._lbl_cambio)
        
        # Para PAGO MIXTO
        self._lbl_mixto_info = QLabel("Dividir pago entre efectivo y transferencia:")
        self._lbl_mixto_info.setStyleSheet("color:#f5a623; font-size:12px; font-weight:bold;")
        panel_layout.addWidget(self._lbl_mixto_info)
        
        fila_mixto = QHBoxLayout()
        fila_mixto.addWidget(QLabel("Efectivo:"))
        self._txt_efectivo = QLineEdit()
        self._txt_efectivo.setPlaceholderText("0")
        self._txt_efectivo.textChanged.connect(self._actualizar_mixto)
        fila_mixto.addWidget(self._txt_efectivo)
        
        fila_mixto.addWidget(QLabel("Transferencia:"))
        self._txt_transferencia = QLineEdit()
        self._txt_transferencia.setPlaceholderText("0")
        self._txt_transferencia.textChanged.connect(self._actualizar_mixto)
        fila_mixto.addWidget(self._txt_transferencia)
        panel_layout.addLayout(fila_mixto)
        
        self._lbl_mixto_total = QLabel("Total: $0")
        self._lbl_mixto_total.setStyleSheet("color:#2ecc71; font-size:14px; font-weight:bold;")
        panel_layout.addWidget(self._lbl_mixto_total)
        
        layout.addWidget(self._panel_efectivo)

        self._lbl_error = QLabel("")
        self._lbl_error.setStyleSheet("color:#e74c3c; font-size:12px;")
        self._lbl_error.setWordWrap(True)
        layout.addWidget(self._lbl_error)

        acciones = QHBoxLayout()
        self._btn_cobrar = QPushButton("CONFIRMAR COBRO")
        self._btn_cobrar.setStyleSheet(
            "background:#27ae60; color:#fff; font-weight:bold; padding:12px;"
            " border-radius:6px; font-size:15px;"
        )
        self._btn_cobrar.clicked.connect(self._confirmar)
        self._btn_cancelar = QPushButton("Cancelar")
        self._btn_cancelar.setStyleSheet(
            "background:#16213e; color:#ccc; padding:12px; border-radius:6px;"
        )
        self._btn_cancelar.clicked.connect(self.reject)
        acciones.addWidget(self._btn_cobrar, 2)
        acciones.addWidget(self._btn_cancelar, 1)
        layout.addLayout(acciones)

        self._btn_efectivo.setChecked(True)
        self._seleccionar_metodo("EFECTIVO")

        if self._resumen is None:
            self._lbl_error.setText(self._error_inicial or "No se puede cobrar.")
            self._btn_cobrar.setEnabled(False)
        elif self._cobro.caja_abierta() is None:
            self._lbl_error.setText(
                "No hay caja abierta: un ADMIN debe abrir la caja antes de cobrar."
            )
            self._btn_cobrar.setEnabled(False)

    # ------------------------------------------------------
    # Metodo de pago y cambio
    # ------------------------------------------------------
    def _seleccionar_metodo(self, metodo):
        self._btn_efectivo.setChecked(metodo == "EFECTIVO")
        self._btn_transferencia.setChecked(metodo == "TRANSFERENCIA")
        self._btn_mixto.setChecked(metodo == "MIXTO")
        self._lbl_error.setText("")
        
        # Mostrar/ocultar paneles según el método
        self._txt_recibido.setVisible(metodo == "EFECTIVO")
        self._lbl_cambio.setVisible(metodo == "EFECTIVO")
        self._lbl_mixto_info.setVisible(metodo == "MIXTO")
        self._txt_efectivo.setVisible(metodo == "MIXTO")
        self._txt_transferencia.setVisible(metodo == "MIXTO")
        self._lbl_mixto_total.setVisible(metodo == "MIXTO")
        
        self._actualizar_cambio()

    def metodo(self) -> str:
        if self._btn_efectivo.isChecked():
            return "EFECTIVO"
        elif self._btn_transferencia.isChecked():
            return "TRANSFERENCIA"
        else:
            return "MIXTO"

    def _recibido(self):
        """Lee el valor recibido aceptando formatos como 50.000 o 50000."""
        texto = (
            self._txt_recibido.text().strip()
            .replace("$", "").replace(" ", "")
        )
        if not texto:
            return None
        if "." in texto and "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        elif "." in texto:
            partes = texto.split(".")
            if len(partes[-1]) == 3:
                texto = texto.replace(".", "")
        elif "," in texto:
            texto = texto.replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return None

    def _actualizar_cambio(self):
        if self.metodo() != "EFECTIVO":
            self._lbl_cambio.setText("")
            return
        recibido = self._recibido()
        if recibido is None:
            self._lbl_cambio.setText("Cambio: $0")
            return
        cambio = self._cobro.calcular_cambio(self._total, recibido)
        if cambio >= 0:
            self._lbl_cambio.setText(f"Cambio: {formato_moneda(cambio)}")
        else:
            self._lbl_cambio.setText(f"Faltan: {formato_moneda(abs(cambio))}")

    def _actualizar_mixto(self):
        """Valida que efectivo + transferencia = total."""
        if self.metodo() != "MIXTO":
            return
        
        try:
            efectivo = float(self._txt_efectivo.text().replace("$", "").replace(" ", "").replace(".", "").replace(",", ".") or 0)
            transferencia = float(self._txt_transferencia.text().replace("$", "").replace(" ", "").replace(".", "").replace(",", ".") or 0)
        except ValueError:
            self._lbl_mixto_total.setText("Total: Error")
            return
        
        total_ingresado = efectivo + transferencia
        self._lbl_mixto_total.setText(f"Total: {formato_moneda(total_ingresado)}")
        
        if abs(total_ingresado - self._total) < 0.01:
            self._lbl_mixto_total.setStyleSheet("color:#2ecc71; font-size:14px; font-weight:bold;")
        else:
            self._lbl_mixto_total.setStyleSheet("color:#e74c3c; font-size:14px; font-weight:bold;")


    # ------------------------------------------------------
    # Cobro
    # ------------------------------------------------------
    def cobrar(self):
        """Ejecuta el cobro sin dialogos (para pruebas). Retorna dict o None."""
        try:
            if self.metodo() == "MIXTO":
                # Pago mixto: efectivo + transferencia
                try:
                    efectivo_txt = self._txt_efectivo.text().replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    transferencia_txt = self._txt_transferencia.text().replace("$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    efectivo = float(efectivo_txt or 0)
                    transferencia = float(transferencia_txt or 0)
                except ValueError:
                    self._lbl_error.setText("Valores inválidos en efectivo o transferencia")
                    return None
                
                if abs(efectivo + transferencia - self._total) > 0.01:
                    self._lbl_error.setText(f"El total debe ser {formato_moneda(self._total)}")
                    return None
                
                # Para pago mixto, registrar con ambos montos
                datos = self._cobro.cobrar_mixto(self._venta_id, efectivo, transferencia)
                return datos
            
            elif self.metodo() == "TRANSFERENCIA":
                # TRANSFERENCIA: no recibe valor
                datos = self._cobro.cobrar(self._venta_id, "TRANSFERENCIA", None)
                return datos
            
            else:
                # EFECTIVO: requiere valor recibido
                recibido = self._recibido()
                if recibido is None:
                    self._lbl_error.setText("Ingrese el valor recibido")
                    return None
                datos = self._cobro.cobrar(self._venta_id, "EFECTIVO", recibido)
                return datos
        except (ValueError, PermissionError) as e:
            self._lbl_error.setText(str(e))
            return None

    def _confirmar(self):
        """Ejecuta el cobro con validaciones robustas."""
        try:
            datos = self.cobrar()
            if datos is None:
                # El error ya está en _lbl_error por el método cobrar()
                return
            
            mensaje = f"Cobro registrado.\nTotal: {formato_moneda(datos['total'])}"
            if "MIXTO" in datos.get("metodo_pago", ""):
                mensaje += f"\n{datos['metodo_pago']}"
            elif datos.get("metodo_pago") == "EFECTIVO":
                mensaje += f"\nRecibido: {formato_moneda(datos.get('recibido', 0))}"
                mensaje += f"\nCAMBIO: {formato_moneda(datos.get('cambio', 0))}"
            else:
                mensaje += "\nPago por TRANSFERENCIA (no suma al efectivo de caja)"
            
            consecutivo = datos.get('consecutivo', 0)
            if consecutivo:
                mensaje += f"\nComprobante #{consecutivo:06d} guardado."
            
            if QMessageBox.question(
                self, "Cobro registrado", mensaje + "\n\n¿Imprimir el comprobante?"
            ) == QMessageBox.StandardButton.Yes:
                self.imprimir()
            self.accept()
        except Exception as e:
            self._lbl_error.setText(f"Error en cobro: {str(e)}")
            import traceback
            traceback.print_exc()

    def imprimir(self) -> bool:
        ok, mensaje = self._cobro.imprimir_comprobante(self._venta_id)
        if not ok:
            QMessageBox.information(self, "Impresion", mensaje)
        return ok

    def _stylesheet(self) -> str:
        return """
        QDialog { background:#0f0f23; color:#e0e0e0; }
        QLabel { color:#ccc; }
        QLineEdit {
            background:#16213e; color:#fff; border:1px solid #333;
            border-radius:6px; padding:10px; font-size:16px;
        }
        QPushButton[checkable="true"] {
            background:#16213e; color:#ccc; border:1px solid #333;
            border-radius:6px; font-weight:bold;
        }
        QPushButton[checkable="true"]:checked {
            background:#0d3b66; color:#f5a623; border:2px solid #f5a623;
        }
        """

