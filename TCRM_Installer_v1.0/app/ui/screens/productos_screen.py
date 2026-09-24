# -*- coding: utf-8 -*-
# ============================================================
#  app/ui/screens/productos_screen.py
#  Administracion de productos (Punto 2/3)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QComboBox,
    QLineEdit, QSpinBox, QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt
from app.ui.screens._base_screen import BaseScreen
from app.ui.themes.colors import Colors
from app.services.producto_service import ProductoService
from app.services.permisos import Permisos
from app.utils.helpers import formato_moneda


class ProductosScreen(BaseScreen):
    """Gestión completa de productos: crear, editar, eliminar, activar/desactivar."""
    TITULO = "Productos"

    def __init__(self, db, auth, parent=None):
        super().__init__(db, auth, parent)
        self._ps = ProductoService(db, auth)
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()
        self.refrescar()

    def _setup_ui(self):
        layout = self._main_layout
        layout.addWidget(self._header("🍟  Gestión de Productos"))

        # Barra de acciones
        barra = QHBoxLayout()
        barra.setSpacing(8)
        
        self._btn_nuevo = QPushButton("➕ Nuevo Producto")
        self._btn_nuevo.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_nuevo.clicked.connect(self._crear_producto)
        barra.addWidget(self._btn_nuevo)
        
        self._btn_editar = QPushButton("✏️ Editar")
        self._btn_editar.clicked.connect(self._editar_producto)
        barra.addWidget(self._btn_editar)
        
        self._btn_eliminar = QPushButton("❌ Eliminar")
        self._btn_eliminar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_DANGER, Colors.COLOR_DANGER_HOVER
        ))
        self._btn_eliminar.clicked.connect(self._desactivar_producto)
        barra.addWidget(self._btn_eliminar)
        
        self._btn_inactivos = QPushButton("📋 Ver Inactivos")
        self._btn_inactivos.clicked.connect(self._mostrar_inactivos)
        barra.addWidget(self._btn_inactivos)
        
        self._btn_categorias = QPushButton("🏷️ Categorías")
        self._btn_categorias.setStyleSheet(Colors.get_button_style(
            "#8b5cf6", "#7c3aed"
        ))
        self._btn_categorias.clicked.connect(self._gestionar_categorias)
        barra.addWidget(self._btn_categorias)
        
        barra.addStretch()
        layout.addLayout(barra)

        # Tabla de productos
        self._tabla = QTableWidget(0, 4)
        self._tabla.setHorizontalHeaderLabels([
            "Producto", "Categoría", "Precio", "Descripción"
        ])
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self._tabla)

    def refrescar(self):
        """Recarga la lista de productos ACTIVOS solamente."""
        try:
            productos = self._ps.listar_activos()  # Solo activos
            self._tabla.setRowCount(len(productos))
            
            for fila, prod in enumerate(productos):
                # Nombre
                item_nombre = QTableWidgetItem(prod["nombre"])
                item_nombre.setData(Qt.UserRole, prod["id"])
                self._tabla.setItem(fila, 0, item_nombre)
                
                # Categoría
                cat = prod.get("categoria_nombre", "Sin categoría")
                self._tabla.setItem(fila, 1, QTableWidgetItem(cat))
                
                # Precio
                precio_item = QTableWidgetItem(formato_moneda(prod["precio"]))
                precio_item.setTextAlignment(Qt.AlignRight)
                self._tabla.setItem(fila, 2, precio_item)
                
                # Descripción
                desc = prod.get("descripcion", "")
                self._tabla.setItem(fila, 3, QTableWidgetItem(desc))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar productos: {e}")

    def _crear_producto(self):
        """Abre diálogo para crear un nuevo producto."""
        dialogo = DialogoProducto(self._db, parent=self)
        if dialogo.exec() == QDialog.Accepted and dialogo.datos:
            try:
                self._ps.crear(
                    nombre=dialogo.datos["nombre"],
                    descripcion=dialogo.datos["descripcion"],
                    categoria_id=dialogo.datos["categoria_id"],
                    precio=dialogo.datos["precio"]
                )
                QMessageBox.information(self, "✓ Éxito", "Producto creado correctamente.")
                self.refrescar()
                # Forzar invalidación del caché para que el catálogo se actualice
                from app.utils.cache import obtener_cache
                obtener_cache().invalidar("productos:activos")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el producto: {e}")

    def _editar_producto(self):
        """Abre diálogo para editar el producto seleccionado."""
        fila = self._tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un producto para editar.")
            return
        
        prod_id = self._tabla.item(fila, 0).data(Qt.UserRole)
        prod = self._ps.obtener_por_id(prod_id)
        
        dialogo = DialogoProducto(self._db, producto=prod, parent=self)
        if dialogo.exec() == QDialog.Accepted and dialogo.datos:
            try:
                self._ps.actualizar(
                    prod_id,
                    nombre=dialogo.datos["nombre"],
                    descripcion=dialogo.datos["descripcion"],
                    categoria_id=dialogo.datos["categoria_id"],
                    precio=dialogo.datos["precio"]
                )
                QMessageBox.information(self, "✓ Éxito", "Producto actualizado correctamente.")
                self.refrescar()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el producto: {e}")

    def _desactivar_producto(self):
        """Desactiva el producto seleccionado."""
        fila = self._tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un producto para desactivar.")
            return
        
        prod_id = self._tabla.item(fila, 0).data(Qt.UserRole)
        prod_nombre = self._tabla.item(fila, 0).text()
        
        respuesta = QMessageBox.question(
            self, "🚫 Desactivar",
            f"¿Desea desactivar el producto '{prod_nombre}'?\n\n"
            "El producto no aparecerá en el catálogo, pero su historial se conserva.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            try:
                self._ps.eliminar(prod_id)
                QMessageBox.information(self, "✓ Éxito", "Producto desactivado correctamente.")
                self.refrescar()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo desactivar el producto: {e}")

    def _mostrar_inactivos(self):
        """Muestra los productos desactivados en un diálogo con opción de reactivar."""
        try:
            productos_inactivos = self._ps.listar_inactivos()
            if not productos_inactivos:
                QMessageBox.information(self, "Sin inactivos", "No hay productos desactivados.")
                return
            
            dialogo = DialogoInactivos(self._ps, productos_inactivos, parent=self)
            if dialogo.exec() == QDialog.Accepted:
                self.refrescar()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los inactivos: {e}")

    def _gestionar_categorias(self):
        """Abre diálogo para crear/eliminar categorías."""
        dialogo = DialogoCategorias(self._db, self._ps, parent=self)
        if dialogo.exec() == QDialog.Accepted:
            # Invalidar caché y refrescar para que aparezcan las nuevas categorías
            from app.utils.cache import obtener_cache
            obtener_cache().invalidar("categorias:todas")
            self.refrescar()


class DialogoProducto(QDialog):
    """Diálogo para crear/editar un producto."""

    def __init__(self, db, producto=None, parent=None):
        super().__init__(parent)
        self._db = db
        self.datos = None
        self.setWindowTitle("Nuevo Producto" if not producto else "Editar Producto")
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setStyleSheet(self._stylesheet())
        
        self._ps = ProductoService(db)
        self._setup_ui()
        
        # IMPORTANTE: Cargar categorías DESPUÉS de crear el combobox
        # Esto garantiza que siempre tenga las categorías más recientes
        self._cargar_categorias()
        
        if producto:
            self._cargar_datos(producto)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Nombre
        lbl_nombre = QLabel("📝 Nombre del producto:")
        lbl_nombre.setStyleSheet(f"color:#fff; font-weight:bold;")
        layout.addWidget(lbl_nombre)
        
        self._txt_nombre = QLineEdit()
        self._txt_nombre.setPlaceholderText("Ej: Hamburguesa Especial")
        layout.addWidget(self._txt_nombre)

        # Categoría
        lbl_cat = QLabel("🏷️ Categoría:")
        lbl_cat.setStyleSheet(f"color:#fff; font-weight:bold;")
        layout.addWidget(lbl_cat)
        
        self._cmb_categoria = QComboBox()
        layout.addWidget(self._cmb_categoria)

        # Precio
        lbl_precio = QLabel("💰 Precio (COP):")
        lbl_precio.setStyleSheet(f"color:#fff; font-weight:bold;")
        layout.addWidget(lbl_precio)
        
        self._spin_precio = QSpinBox()
        self._spin_precio.setMinimum(0)
        self._spin_precio.setMaximum(9999999)
        self._spin_precio.setSingleStep(1000)
        layout.addWidget(self._spin_precio)

        # Descripción
        lbl_desc = QLabel("📄 Descripción:")
        lbl_desc.setStyleSheet(f"color:#fff; font-weight:bold;")
        layout.addWidget(lbl_desc)
        
        self._txt_desc = QLineEdit()
        self._txt_desc.setPlaceholderText("Ej: Con queso, lechuga y tomate")
        layout.addWidget(self._txt_desc)

        # Botones
        layout.addSpacing(12)
        botones = QHBoxLayout()
        
        self._btn_guardar = QPushButton("✓ GUARDAR")
        self._btn_guardar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_guardar.clicked.connect(self._guardar)
        
        self._btn_cancelar = QPushButton("✕ Cancelar")
        self._btn_cancelar.clicked.connect(self.reject)
        
        botones.addWidget(self._btn_guardar, 2)
        botones.addWidget(self._btn_cancelar, 1)
        layout.addLayout(botones)

    def _cargar_categorias(self):
        """Carga las categorías disponibles."""
        try:
            from app.services.producto_service import ProductoService
            ps = ProductoService(self._db)
            categorias = ps.listar_categorias()
            self._cmb_categoria.clear()
            for cat in categorias:
                self._cmb_categoria.addItem(cat["nombre"], cat["id"])
        except Exception:
            pass

    def _cargar_datos(self, producto):
        """Carga los datos del producto en los campos."""
        self._txt_nombre.setText(producto.get("nombre", ""))
        self._txt_desc.setText(producto.get("descripcion", ""))
        self._spin_precio.setValue(int(producto.get("precio", 0)))
        
        # Seleccionar categoría
        cat_id = producto.get("categoria_id")
        for i in range(self._cmb_categoria.count()):
            if self._cmb_categoria.itemData(i) == cat_id:
                self._cmb_categoria.setCurrentIndex(i)
                break

    def _guardar(self):
        """Valida y guarda los datos."""
        nombre = self._txt_nombre.text().strip()
        descripcion = self._txt_desc.text().strip()
        precio = self._spin_precio.value()
        categoria_id = self._cmb_categoria.currentData()

        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio.")
            return

        if precio <= 0:
            QMessageBox.warning(self, "Error", "El precio debe ser mayor a 0.")
            return

        self.datos = {
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio,
            "categoria_id": categoria_id
        }
        self.accept()

    def _stylesheet(self):
        return f"""
        QDialog {{
            background: #0f172a;
            color: #fff;
        }}
        QLabel {{
            color: #cbd5e1;
        }}
        QLineEdit, QSpinBox, QComboBox {{
            background: #1e293b;
            color: #fff;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
        }}
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
            border: 2px solid #06b6d4;
        }}
        """

class DialogoInactivos(QDialog):
    """Diálogo para ver y reactivar productos desactivados."""

    def __init__(self, producto_service, inactivos, parent=None):
        super().__init__(parent)
        self._ps = producto_service
        self._inactivos = inactivos
        self.setWindowTitle("Productos Desactivados")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setStyleSheet(self._stylesheet())
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl_titulo = QLabel("📋 Productos Desactivados")
        lbl_titulo.setStyleSheet(f"color:#06b6d4; font-weight:bold; font-size:14px;")
        layout.addWidget(lbl_titulo)

        # Tabla de inactivos
        self._tabla = QTableWidget(0, 4)
        self._tabla.setHorizontalHeaderLabels([
            "Producto", "Categoría", "Precio", "Descripción"
        ])
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self._tabla)

        # Cargar datos
        self._tabla.setRowCount(len(self._inactivos))
        for fila, prod in enumerate(self._inactivos):
            from app.utils.helpers import formato_moneda
            
            item_nombre = QTableWidgetItem(prod["nombre"])
            item_nombre.setData(Qt.UserRole, prod["id"])
            self._tabla.setItem(fila, 0, item_nombre)
            
            cat = prod.get("categoria_nombre", "Sin categoría")
            self._tabla.setItem(fila, 1, QTableWidgetItem(cat))
            
            precio_item = QTableWidgetItem(formato_moneda(prod["precio"]))
            precio_item.setTextAlignment(Qt.AlignRight)
            self._tabla.setItem(fila, 2, precio_item)
            
            desc = prod.get("descripcion", "")
            self._tabla.setItem(fila, 3, QTableWidgetItem(desc))

        # Botones
        botones = QHBoxLayout()
        
        self._btn_reactivar = QPushButton("♻️ Reactivar")
        self._btn_reactivar.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_reactivar.clicked.connect(self._reactivar_seleccionado)
        botones.addWidget(self._btn_reactivar)
        
        self._btn_cerrar = QPushButton("✕ Cerrar")
        self._btn_cerrar.clicked.connect(self.accept)
        botones.addWidget(self._btn_cerrar)
        
        layout.addLayout(botones)

    def _reactivar_seleccionado(self):
        fila = self._tabla.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione un producto para reactivar.")
            return
        
        prod_id = self._tabla.item(fila, 0).data(Qt.UserRole)
        prod_nombre = self._tabla.item(fila, 0).text()
        
        respuesta = QMessageBox.question(
            self, "♻️ Reactivar",
            f"¿Desea reactivar '{prod_nombre}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if respuesta == QMessageBox.Yes:
            try:
                self._ps.reactivar(prod_id)
                QMessageBox.information(self, "✓ Éxito", "Producto reactivado correctamente.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo reactivar: {e}")

    def _stylesheet(self):
        return f"""
        QDialog {{
            background: #0f172a;
            color: #fff;
        }}
        QTableWidget {{
            background: #1e293b;
            color: #e2e8f0;
            gridline-color: #334155;
            border: 1px solid #334155;
        }}
        QTableWidget::item:selected {{
            background: #06b6d4;
            color: #0f172a;
        }}
        QHeaderView::section {{
            background: #0f172a;
            color: #06b6d4;
            padding: 8px;
            font-weight: bold;
            border: none;
            border-bottom: 2px solid #06b6d4;
        }}
        """


class DialogoCategorias(QDialog):
    """Diálogo para crear y eliminar categorías."""

    def __init__(self, db, producto_service, parent=None):
        super().__init__(parent)
        self._db = db
        self._ps = producto_service
        self.setWindowTitle("Gestionar Categorías")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.setStyleSheet(self._stylesheet())
        self._setup_ui()
        self._cargar_categorias()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl_titulo = QLabel("🏷️ Gestión de Categorías")
        lbl_titulo.setStyleSheet(f"color:#8b5cf6; font-weight:bold; font-size:14px;")
        layout.addWidget(lbl_titulo)

        # Crear nueva categoría
        fila_nueva = QHBoxLayout()
        self._txt_nueva_cat = QLineEdit()
        self._txt_nueva_cat.setPlaceholderText("Nombre de la nueva categoría...")
        fila_nueva.addWidget(self._txt_nueva_cat)

        self._btn_agregar_cat = QPushButton("➕ Agregar")
        self._btn_agregar_cat.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_SUCCESS, Colors.COLOR_SUCCESS_HOVER, Colors.COLOR_SUCCESS_PRESS
        ))
        self._btn_agregar_cat.clicked.connect(self._agregar_categoria)
        fila_nueva.addWidget(self._btn_agregar_cat)
        layout.addLayout(fila_nueva)

        # Separador
        sep = QLabel("")
        sep.setStyleSheet("border-top:1px solid #334155; margin:10px 0;")
        layout.addWidget(sep)

        lbl_lista = QLabel("📋 Categorías Existentes:")
        lbl_lista.setStyleSheet(f"color:#cbd5e1; font-weight:bold;")
        layout.addWidget(lbl_lista)

        # Tabla de categorías
        self._tabla_cats = QTableWidget(0, 2)
        self._tabla_cats.setHorizontalHeaderLabels(["Categoría", "Productos"])
        self._tabla_cats.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tabla_cats.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tabla_cats.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._tabla_cats.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self._tabla_cats)

        # Botones inferiores
        botones = QHBoxLayout()

        self._btn_eliminar_cat = QPushButton("🗑️ Eliminar Categoría")
        self._btn_eliminar_cat.setStyleSheet(Colors.get_button_style(
            Colors.COLOR_DANGER, Colors.COLOR_DANGER_HOVER
        ))
        self._btn_eliminar_cat.clicked.connect(self._eliminar_categoria)
        botones.addWidget(self._btn_eliminar_cat)

        botones.addStretch()

        self._btn_cerrar = QPushButton("✕ Cerrar")
        self._btn_cerrar.clicked.connect(self.accept)
        botones.addWidget(self._btn_cerrar)

        layout.addLayout(botones)

    def _cargar_categorias(self):
        """Carga la lista de categorías con conteo de productos."""
        try:
            categorias = self._ps.listar_categorias()
            self._tabla_cats.setRowCount(len(categorias))

            for fila, cat in enumerate(categorias):
                cat_id = cat["id"]
                cat_nombre = cat["nombre"]

                # Contar productos en esta categoría (activos E inactivos)
                productos = self._db.fetchall(
                    "SELECT COUNT(*) as n FROM productos WHERE categoria_id=?;",
                    (cat_id,)
                )
                count = productos[0]["n"] if productos else 0

                # Nombre de categoría
                item_nombre = QTableWidgetItem(cat_nombre)
                item_nombre.setData(Qt.UserRole, cat_id)
                self._tabla_cats.setItem(fila, 0, item_nombre)

                # Conteo
                item_count = QTableWidgetItem(str(count))
                item_count.setTextAlignment(Qt.AlignCenter)
                self._tabla_cats.setItem(fila, 1, item_count)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las categorías: {e}")

    def _agregar_categoria(self):
        """Agrega una nueva categoría."""
        nombre = self._txt_nueva_cat.text().strip()

        if not nombre:
            QMessageBox.warning(self, "Error", "Ingrese el nombre de la categoría.")
            return

        try:
            self._db.execute(
                "INSERT INTO categorias (nombre) VALUES (?);",
                (nombre,)
            )
            self._db.commit()
            
            # IMPORTANTE: Invalidar el cache de categorías para que se refleje en DialogoProducto
            from app.utils.cache import obtener_cache
            cache = obtener_cache()
            cache.invalidar("categorias:all")
            
            QMessageBox.information(self, "✓ Éxito", f"Categoría '{nombre}' creada correctamente.")
            self._txt_nueva_cat.clear()
            self._cargar_categorias()
        except Exception as e:
            if "UNIQUE" in str(e):
                QMessageBox.warning(self, "Error", f"La categoría '{nombre}' ya existe.")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo crear la categoría: {e}")

    def _eliminar_categoria(self):
        """Elimina la categoría seleccionada."""
        fila = self._tabla_cats.currentRow()
        if fila < 0:
            QMessageBox.information(self, "Seleccione", "Seleccione una categoría para eliminar.")
            return

        cat_id = self._tabla_cats.item(fila, 0).data(Qt.UserRole)
        cat_nombre = self._tabla_cats.item(fila, 0).text()
        count_str = self._tabla_cats.item(fila, 1).text()
        count = int(count_str)

        if count > 0:
            QMessageBox.warning(
                self, "No se puede eliminar",
                f"La categoría '{cat_nombre}' tiene {count} producto(s).\n\n"
                "Desactive todos los productos primero."
            )
            return

        respuesta = QMessageBox.question(
            self, "🗑️ Eliminar Categoría",
            f"¿Desea eliminar la categoría '{cat_nombre}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:
            try:
                # Desasociar productos inactivos que usen esta categoría
                self._db.execute(
                    "UPDATE productos SET categoria_id=NULL WHERE categoria_id=?;",
                    (cat_id,)
                )
                # Eliminar la categoría
                self._db.execute("DELETE FROM categorias WHERE id=?;", (cat_id,))
                self._db.commit()
                
                # IMPORTANTE: Invalidar el cache de categorías
                from app.utils.cache import obtener_cache
                cache = obtener_cache()
                cache.invalidar("categorias:all")
                
                QMessageBox.information(self, "✓ Éxito", "Categoría eliminada correctamente.")
                self._cargar_categorias()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la categoría: {e}")

    def _stylesheet(self):
        return f"""
        QDialog {{
            background: #0f172a;
            color: #fff;
        }}
        QLabel {{
            color: #cbd5e1;
        }}
        QLineEdit {{
            background: #1e293b;
            color: #fff;
            border: 1px solid #334155;
            border-radius: 4px;
            padding: 8px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 2px solid #8b5cf6;
        }}
        QTableWidget {{
            background: #1e293b;
            color: #e2e8f0;
            gridline-color: #334155;
            border: 1px solid #334155;
        }}
        QTableWidget::item:selected {{
            background: #8b5cf6;
            color: #fff;
        }}
        QHeaderView::section {{
            background: #0f172a;
            color: #8b5cf6;
            padding: 8px;
            font-weight: bold;
            border: none;
            border-bottom: 2px solid #8b5cf6;
        }}
        """
