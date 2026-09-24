# ============================================================
#  app/ui/screens/usuarios_screen.py
#  Administracion de usuarios — acceso solo para ADMIN (Punto 3)
# ============================================================
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QLabel
)
from app.ui.screens._base_screen import BaseScreen
from app.ui.widgets.dialogo_usuario import DialogoUsuario
from app.ui.widgets.dialogo_password import DialogoPassword
from app.services.usuario_service import UsuarioService


class UsuariosScreen(BaseScreen):
    TITULO = "Usuarios"

    def __init__(self, db, auth, parent=None):
        self._service = UsuarioService(db, auth)
        super().__init__(db, auth, parent)
        self.setStyleSheet(self._base_stylesheet())
        self._setup_ui()

    def _setup_ui(self):
        layout = self._main_layout
        layout.addWidget(self._header("👥  Gestión de Usuarios"))

        botones = QHBoxLayout()
        self._btn_nuevo = QPushButton("➕ Nuevo usuario")
        self._btn_nuevo.clicked.connect(self._nuevo)
        self._btn_editar = QPushButton("✏️ Editar")
        self._btn_editar.clicked.connect(self._editar)
        self._btn_password = QPushButton("🔑 Cambiar contraseña")
        self._btn_password.clicked.connect(self._cambiar_password)
        self._btn_estado = QPushButton("🚫 Activar/Desactivar")
        self._btn_estado.clicked.connect(self._cambiar_estado)
        for b in (self._btn_nuevo, self._btn_editar, self._btn_password,
                  self._btn_estado):
            botones.addWidget(b)
        botones.addStretch()
        layout.addLayout(botones)

        self._tabla = QTableWidget()
        self._tabla.setColumnCount(5)
        self._tabla.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Usuario", "Rol", "Estado"]
        )
        self._tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self._tabla.setSelectionMode(QTableWidget.SingleSelection)
        self._tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tabla.doubleClicked.connect(lambda _: self._editar())
        header = self._tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self._tabla)

        self._lbl_info = QLabel("")
        self._lbl_info.setStyleSheet("color:#888; font-size:12px;")
        layout.addWidget(self._lbl_info)

    def refrescar(self):
        """Carga la tabla de usuarios (solo ADMIN)."""
        try:
            usuarios = self._service.listar()
        except PermissionError as e:
            self._tabla.setRowCount(0)
            self._lbl_info.setText(f"⛔ {e}")
            return

        self._tabla.setRowCount(len(usuarios))
        for i, u in enumerate(usuarios):
            self._tabla.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self._tabla.setItem(i, 1, QTableWidgetItem(u["nombre"]))
            self._tabla.setItem(i, 2, QTableWidgetItem(u["usuario"]))
            self._tabla.setItem(i, 3, QTableWidgetItem(u["rol"]))
            estado = "Activo" if u["activo"] == 1 else "Inactivo"
            self._tabla.setItem(i, 4, QTableWidgetItem(estado))
        self._lbl_info.setText(
            "Doble clic para editar. El sistema nunca se queda sin un ADMIN activo."
        )

    def _usuario_seleccionado(self):
        fila = self._tabla.currentRow()
        if fila < 0:
            QMessageBox.information(
                self, "Seleccione", "Seleccione un usuario de la tabla."
            )
            return None
        return self._service.obtener_por_id(
            int(self._tabla.item(fila, 0).text())
        )

    def _nuevo(self):
        if DialogoUsuario(self._db, self._auth, parent=self).exec():
            self.refrescar()

    def _editar(self):
        usuario = self._usuario_seleccionado()
        if not usuario:
            return
        if DialogoUsuario(self._db, self._auth, fila=usuario, parent=self).exec():
            self.refrescar()

    def _cambiar_password(self):
        usuario = self._usuario_seleccionado()
        if not usuario:
            return
        DialogoPassword(
            self._db, self._auth, id_usuario=usuario["id"], parent=self
        ).exec()

    def _cambiar_estado(self):
        usuario = self._usuario_seleccionado()
        if not usuario:
            return
        if usuario["id"] == self._usuario.id:
            QMessageBox.warning(
                self, "Operacion no permitida",
                "No puede cambiar su propio estado desde aqui."
            )
            return
        try:
            self._service.cambiar_estado(usuario["id"], usuario["activo"] != 1)
        except (PermissionError, ValueError) as e:
            QMessageBox.warning(self, "Operacion no permitida", str(e))
        self.refrescar()
