# -*- coding: utf-8 -*-
#  app/ui/screens/mesas_screen.py
#  Tablero de mesas + pedido de la mesa seleccionada (Punto 4)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QGridLayout, QWidget, QLabel, QMessageBox, QStackedWidget,
    QDialog, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSpinBox
)
from PySide6.QtCore import Qt
from app.ui.screens._base_screen import BaseScreen
from app.ui.widgets.mesa_card import MesaCard
from app.ui.widgets.dialogo_domicilio import DialogoDomicilio
from app.ui.screens.pedido_screen import PedidoScreen
from app.services.pedido_service import PedidoService
from app.ui.themes.colors import Colors


class MesasScreen(BaseScreen):
    """Tablero visual de todas las mesas y acceso al pedido de cada una."""
    TITULO = "Mesas"
    COLUMNAS = 6

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._ps = PedidoService(db, auth)
        self._pedido = None
        self._tarjetas_cache = {}  # Caché de tarjetas por mesa_id
        self._last_mesas_hash = None  # OPTIMIZED (Task 7): Track if data changed
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        layout = self._main_layout
        self._lbl_titulo = self._header("🪑  Mesas")
        layout.addWidget(self._lbl_titulo)

        self._lbl_resumen = QLabel("")
        self._lbl_resumen.setStyleSheet("color:#888; font-size:12px; padding-left:8px;")
        layout.addWidget(self._lbl_resumen)

        # Barra de acciones
        from PySide6.QtWidgets import QHBoxLayout, QPushButton
        barra = QHBoxLayout()
        barra.setSpacing(8)
        
        self._btn_editar_mesas = QPushButton("✏️ Editar Mesas")
        from app.ui.themes.colors import Colors
        self._btn_editar_mesas.setStyleSheet(Colors.get_button_style(
            Colors.ACCENT_BLUE, "#1e40af"
        ))
        self._btn_editar_mesas.clicked.connect(self._abrir_editor_mesas)
        barra.addWidget(self._btn_editar_mesas)
        
        self._btn_actualizar = QPushButton("🔄 Actualizar")
        self._btn_actualizar.setStyleSheet(Colors.get_button_style(
            "#06b6d4", "#0891b2"
        ))
        self._btn_actualizar.clicked.connect(self.refrescar)
        barra.addWidget(self._btn_actualizar)
        
        barra.addStretch()
        layout.addLayout(barra)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._pagina_mesas = QWidget()
        pagina_layout = QVBoxLayout(self._pagina_mesas)
        self._grid = QGridLayout()
        self._grid.setSpacing(12)
        pagina_layout.addLayout(self._grid)
        pagina_layout.addStretch()
        self._stack.addWidget(self._pagina_mesas)

    # ------------------------------------------------------
    def refrescar(self):
        """Llamado al navegar a esta pantalla: vuelve al tablero."""
        self._mostrar_tablero()

    def _limpiar_grid(self):
        """OPTIMIZADO: No elimina las tarjetas, solo las oculta."""
        while self._grid.count():
            item = self._grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)  # Quitar del layout pero no eliminar

    def _mostrar_tablero(self):
        """OPTIMIZED (Task 7): Skip layout rebuild if mesas data unchanged; reuse tarjetas."""
        try:
            mesas = self._ps.listar_mesas()
            print(f"[DEBUG] mesas_screen: listar_mesas() retornó {len(mesas)} mesas")
        except Exception as e:
            print(f"[ERROR] mesas_screen: Exception en listar_mesas(): {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las mesas: {e}")
            return
        
        # OPTIMIZED: Hash mesas to skip re-render if unchanged
        import hashlib
        try:
            mesas_str = str(sorted((m["id"], m["estado"]) for m in mesas))
            current_hash = hashlib.md5(mesas_str.encode()).hexdigest()
            print(f"[DEBUG] mesas_screen: hash={current_hash[:8]}..., last_hash={self._last_mesas_hash[:8] if self._last_mesas_hash else 'None'}")
        except Exception as e:
            print(f"[ERROR] mesas_screen: Exception creando hash: {e}")
            import traceback
            traceback.print_exc()
            return
        
        if current_hash == self._last_mesas_hash:
            # Data unchanged; only update counts
            print(f"[DEBUG] mesas_screen: Mesas sin cambios, solo actualizando conteos")
            disponibles = sum(1 for m in mesas if m["estado"] == "DISPONIBLE")
            self._lbl_resumen.setText(
                f"{len(mesas)} mesas   |   {disponibles} disponibles   |   "
                f"{len(mesas) - disponibles} ocupadas"
            )
        else:
            print(f"[DEBUG] mesas_screen: Regenerando grid ({len(mesas)} mesas)")
            self._last_mesas_hash = current_hash
            
            self._limpiar_grid()
            
            # Reordenar: Domicilio PRIMERO, luego las demás por ID
            domicilios = [m for m in mesas if m.get("tipo") == "DOMICILIO"]
            normales = sorted([m for m in mesas if m.get("tipo") != "DOMICILIO"], key=lambda m: m["id"])
            mesas_ordenadas = domicilios + normales
            
            for i, mesa in enumerate(mesas_ordenadas):
                try:
                    mesa_id = mesa["id"]
                    
                    # Reutilizar tarjeta si existe en caché
                    if mesa_id in self._tarjetas_cache:
                        tarjeta = self._tarjetas_cache[mesa_id]
                        tarjeta.actualizar(mesa)
                        print(f"[DEBUG] mesas_screen: Mesa {mesa_id} actualizada (desde cache)")
                    else:
                        # Crear nueva tarjeta solo si no existe
                        tarjeta = MesaCard(mesa)
                        tarjeta.clicked.connect(self._seleccionar_mesa)
                        self._tarjetas_cache[mesa_id] = tarjeta
                        print(f"[DEBUG] mesas_screen: Mesa {mesa_id} creada (nueva)")
                    
                    self._grid.addWidget(tarjeta, i // self.COLUMNAS, i % self.COLUMNAS)
                except Exception as e:
                    print(f"[ERROR] mesas_screen: Exception procesando mesa {i}: {e}")
                    import traceback
                    traceback.print_exc()
            
            disponibles = sum(1 for m in mesas if m["estado"] == "DISPONIBLE")
            self._lbl_resumen.setText(
                f"{len(mesas)} mesas   |   {disponibles} disponibles   |   "
                f"{len(mesas) - disponibles} ocupadas"
            )
            print(f"[DEBUG] mesas_screen: Grid regenerado con {len(mesas)} tarjetas")
        
        self._lbl_titulo.setText("🪑  Mesas")
        self._stack.setCurrentWidget(self._pagina_mesas)
        print(f"[DEBUG] mesas_screen: Mostrando página de mesas")


    # ------------------------------------------------------
    def _seleccionar_mesa(self, mesa):
        """Abre la mesa (si esta disponible) y muestra su pedido."""
        try:
            if mesa["estado"] == "DISPONIBLE":
                cliente = None
                direccion = None
                if mesa.get("tipo") == "DOMICILIO":
                    dialogo = DialogoDomicilio(
                        mesa_nombre=mesa["nombre"], parent=self
                    )
                    if not dialogo.exec() or not dialogo.datos:
                        return
                    cliente = dialogo.datos["cliente"]
                    direccion = dialogo.datos["direccion"]
                venta_id = self._ps.acceder_mesa(
                    mesa["id"], cliente=cliente, direccion=direccion
                )
                mesa = self._ps.datos_mesa_activa(mesa["id"])
            else:
                # Migración V6: venta_activa_id no existe. Buscar venta ABIERTA por mesa_id
                venta = self._db.fetchone(
                    "SELECT id FROM ventas WHERE mesa_id=? AND estado='ABIERTA';",
                    (mesa["id"],)
                )
                venta_id = venta["id"] if venta else None
                if venta_id is None:
                    QMessageBox.warning(
                        self, "Mesa ocupada",
                        "La mesa figura ocupada pero no tiene venta activa."
                    )
                    return
            self._mostrar_pedido(mesa, venta_id)
        except PermissionError as e:
            QMessageBox.warning(self, "Permiso denegado", str(e))
        except Exception as e:
            QMessageBox.warning(self, "No se pudo abrir la mesa", str(e))

    def _mostrar_pedido(self, mesa, venta_id):
        if self._pedido is not None:
            self._stack.removeWidget(self._pedido)
            self._pedido.deleteLater()
        self._pedido = PedidoScreen(
            self._db, self._auth, mesa=mesa, venta_id=venta_id, parent=self
        )
        # Connect the volver signal to handle returning to mesa grid
        self._pedido.volver.connect(self._on_volver_pedido)
        self._stack.addWidget(self._pedido)
        self._lbl_titulo.setText(f"🪑  Pedido — {mesa.get('nombre', '')}")
        self._stack.setCurrentWidget(self._pedido)
    
    def _on_volver_pedido(self):
        """Slot called when Volver button is clicked in pedido_screen."""
        self._mostrar_tablero()


    def _abrir_editor_mesas(self):
        """Abre diálogo para cambiar cantidad de mesas."""
        dialogo = DialogoCantidadMesas(self._db, self._auth, parent=self)
        if dialogo.exec():
            self.refrescar()


class DialogoCantidadMesas(QDialog):
    """Diálogo simple para cambiar la cantidad de mesas del negocio."""

    def __init__(self, db, auth, parent=None):
        super().__init__(parent)
        self._db = db
        self._auth = auth
        self.setWindowTitle("Cambiar Numero de Mesas")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(self._stylesheet())
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Información actual
        from app.services.mesa_service import MesaService
        ms = MesaService(self._db, self._auth)
        mesas_actuales = ms.listar()
        cantidad_actual = len(mesas_actuales)
        
        lbl_info = QLabel(f"Mesas actuales en el sistema: {cantidad_actual}")
        lbl_info.setStyleSheet("font-size:14px; color:#06b6d4; font-weight:bold;")
        layout.addWidget(lbl_info)
        
        # Selector de cantidad
        fila_cantidad = QHBoxLayout()
        fila_cantidad.setSpacing(12)
        
        lbl_nueva = QLabel("Nueva cantidad de mesas:")
        lbl_nueva.setStyleSheet("font-size:13px; color:#e2e8f0;")
        fila_cantidad.addWidget(lbl_nueva)
        
        self._spin_cantidad = QSpinBox()
        self._spin_cantidad.setMinimum(1)
        self._spin_cantidad.setMaximum(100)
        self._spin_cantidad.setValue(cantidad_actual)
        self._spin_cantidad.setStyleSheet("""
            QSpinBox {
                background: #1e293b;
                color: #fff;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        self._spin_cantidad.setFixedWidth(80)
        fila_cantidad.addWidget(self._spin_cantidad)
        fila_cantidad.addStretch()
        layout.addLayout(fila_cantidad)
        
        # Explicación
        lbl_explicacion = QLabel(
            "Si aumentas: se crearán mesas nuevas\n"
            "Si disminuyes: se eliminarán las ULTIMAS mesas"
        )
        lbl_explicacion.setStyleSheet("font-size:11px; color:#999; line-height:1.6;")
        layout.addWidget(lbl_explicacion)
        
        # Separador
        sep = QLabel("")
        sep.setStyleSheet("border-top:1px solid #334155; margin:10px 0;")
        layout.addWidget(sep)
        
        # Botones
        botones = QHBoxLayout()
        
        self._btn_guardar = QPushButton("Aplicar Cambios")
        self._btn_guardar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_guardar.clicked.connect(self._aplicar_cambios)
        botones.addWidget(self._btn_guardar)
        
        self._btn_cancelar = QPushButton("Cancelar")
        self._btn_cancelar.setStyleSheet(Colors.get_button_style(
            "#64748b", "#475569"
        ))
        self._btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(self._btn_cancelar)
        
        layout.addLayout(botones)

    def _aplicar_cambios(self):
        """Aplica el cambio de cantidad de mesas."""
        nueva_cantidad = self._spin_cantidad.value()
        
        try:
            from app.services.mesa_service import MesaService
            ms = MesaService(self._db, self._auth)
            mesas_actuales = ms.listar()
            
            # Contar SOLO las mesas que NO son domicilio
            mesas_normales = [m for m in mesas_actuales if m.get("tipo") != "DOMICILIO"]
            cantidad_actual = len(mesas_normales)
            
            if nueva_cantidad == cantidad_actual:
                QMessageBox.information(
                    self, "Sin cambios",
                    f"Ya hay {cantidad_actual} mesas en el sistema."
                )
                return
            
            if nueva_cantidad > cantidad_actual:
                # AGREGAR mesas
                diferencia = nueva_cantidad - cantidad_actual
                
                # Obtener número máximo con manejo de errores
                try:
                    resultado = self._db.fetchone(
                        "SELECT MAX(CAST(SUBSTR(nombre, INSTR(nombre, ' ')+1) AS INTEGER)) AS max_num "
                        "FROM mesas WHERE nombre LIKE 'Mesa %';"
                    )
                    max_num = resultado["max_num"] if resultado and resultado["max_num"] else 0
                    if max_num is None:
                        max_num = 0
                    max_num = max(max_num, cantidad_actual)
                except (TypeError, ValueError):
                    # Si hay error en CAST (nombres malformados), simplemente usar cantidad_actual
                    max_num = cantidad_actual
                
                for i in range(diferencia):
                    nuevo_num = max_num + i + 1
                    self._db.execute(
                        "INSERT INTO mesas (nombre, estado, tipo) VALUES (?, 'DISPONIBLE', 'MESA');",
                        (f"Mesa {nuevo_num}",)
                    )
                
                self._db.commit()
                QMessageBox.information(
                    self, "Exito",
                    f"Se agregaron {diferencia} mesas.\n"
                    f"Total ahora: {nueva_cantidad} mesas (+ Domicilio)"
                )
                self.accept()
            else:
                # ELIMINAR mesas (las últimas) - PERO NO DOMICILIO
                diferencia = cantidad_actual - nueva_cantidad
                
                # Confirmar eliminación
                respuesta = QMessageBox.warning(
                    self, "Confirmar eliminacion",
                    f"Se eliminaran las ULTIMAS {diferencia} mesas.\n\n"
                    f"(La mesa de Domicilio se preservara siempre)\n\n"
                    f"Continuar?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if respuesta != QMessageBox.Yes:
                    return
                
                # Obtener SOLO las mesas normales (no domicilio), ordenadas por ID descendente
                mesas_para_eliminar = sorted(mesas_normales, key=lambda m: m["id"], reverse=True)
                
                # Solo eliminar las que se necesitan (hasta 'diferencia')
                a_eliminar = mesas_para_eliminar[:diferencia]
                
                if len(a_eliminar) == 0:
                    QMessageBox.warning(
                        self, "No se puede",
                        "No hay mesas para eliminar.\n"
                        "(Solo existe la mesa de Domicilio)"
                    )
                    return
                
                # Envolver en transacción explícita para garantizar atomicidad
                try:
                    with self._db.transaccion():
                        for mesa in a_eliminar:
                            mesa_id = mesa["id"]
                            
                            # Verificar si tiene venta ACTIVA (en proceso)
                            tiene_venta_activa = self._db.fetchone(
                                "SELECT COUNT(*) as n FROM ventas WHERE mesa_id=? AND estado='ABIERTA';",
                                (mesa_id,)
                            )["n"] > 0
                            
                            if tiene_venta_activa:
                                # Lanzar excepción para que se reverta toda la transacción
                                raise ValueError(
                                    f"La mesa '{mesa['nombre']}' tiene una venta ACTIVA en proceso.\n\n"
                                    f"Cierra la venta primero."
                                )
                            
                            # Nota: Después de la Migración V6, la FK entre ventas.mesa_id y mesas.id
                            # ha sido removida. Las ventas conservan su referencia pero es "huérfana"
                            # (puede no existir una mesa con ese ID). Esto es intencional.
                            self._db.execute("DELETE FROM mesas WHERE id=?;", (mesa_id,))
                    
                    # Si salimos del context manager sin excepción, transacción fue commitida
                    QMessageBox.information(
                        self, "Exito",
                        f"Se eliminaron {len(a_eliminar)} mesas.\n"
                        f"Total ahora: {nueva_cantidad} mesas (+ Domicilio)\n\n"
                        f"(Mesa de Domicilio preservada)"
                    )
                    self.accept()
                    
                except ValueError as e:
                    # Context manager ya ejecutó rollback automáticamente
                    QMessageBox.warning(self, "No se puede eliminar", str(e))
                    return
        except Exception as e:
            self._db.rollback()
            QMessageBox.critical(self, "Error", f"No se pudieron aplicar los cambios: {e}")
            import traceback
            traceback.print_exc()

    def _stylesheet(self):
        return """
        QDialog {
            background: #0f172a;
            color: #e2e8f0;
        }
        QLabel {
            color: #e2e8f0;
        }
        QPushButton {
            background: #3b82f6;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 13px;
        }
        QPushButton:hover {
            background: #60a5fa;
        }
        """
