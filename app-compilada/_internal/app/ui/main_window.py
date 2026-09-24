# ============================================================
#  app/ui/main_window.py
#  Ventana principal - SIN BLOQUEOS DE PERMISOS
# ============================================================
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.database.connection import DatabaseConnection
from app.services.auth_service import AuthService
from app.services.permisos import Permisos


class MainWindow(QMainWindow):
    def __init__(self, db: DatabaseConnection, auth: AuthService):
        super().__init__()
        self._db = db
        self._auth = auth
        self._usuario = auth.usuario_actual
        self._setup_ui()
        self._cargar_pantallas()

    def _setup_ui(self):
        self.setWindowTitle(f"POS Comidas Rapidas — {self._usuario.nombre} ({self._usuario.rol})")
        self.setMinimumSize(1100, 700)
        self.showMaximized()
        self.setStyleSheet(self._stylesheet())

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Barra lateral
        self._sidebar = self._crear_sidebar()
        root_layout.addWidget(self._sidebar)

        # Area de contenido
        self._stack = QStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root_layout.addWidget(self._stack, 1)

    def _crear_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        lbl = QLabel("🍔 POS")
        lbl.setObjectName("sidebar_logo")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFixedHeight(70)
        layout.addWidget(lbl)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("sidebar_sep")
        layout.addWidget(sep)

        # Botones de navegacion
        self._nav_botones = {}
        nav_items = self._items_navegacion()
        for key, label, icono in nav_items:
            btn = QPushButton(f"  {icono}  {label}")
            btn.setObjectName("nav_btn")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked=False, k=key: self._navegar(k))
            layout.addWidget(btn)
            self._nav_botones[key] = btn

        layout.addStretch()

        # Info usuario
        lbl_user = QLabel(f"👤 {self._usuario.nombre}\n{self._usuario.rol}")
        lbl_user.setObjectName("sidebar_user")
        lbl_user.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_user)

        # Cambiar contraseña
        btn_pwd = QPushButton("  🔑  Cambiar contraseña")
        btn_pwd.setObjectName("btn_action")
        btn_pwd.clicked.connect(self._cambiar_mi_password)
        layout.addWidget(btn_pwd)

        # Cerrar sesion
        btn_logout = QPushButton("  🚪  Cerrar sesión")
        btn_logout.setObjectName("btn_logout")
        btn_logout.clicked.connect(self._cerrar_sesion)
        layout.addWidget(btn_logout)

        return sidebar

    def _items_navegacion(self) -> list:
        """Retorna items de menu segun permisos del usuario"""
        items = []
        
        # Mesas: todos pueden (excepto si no tienen USAR_MESAS)
        if self._auth.puede(Permisos.USAR_MESAS):
            items.append(("mesas", "Mesas", "🪑"))
        
        # Productos: todos pueden ver
        if self._auth.puede(Permisos.VER_PRODUCTOS):
            items.append(("productos", "Productos", "🍟"))
        
        # Usuarios: solo ADMIN
        if self._auth.puede(Permisos.ADMINISTRAR_USUARIOS):
            items.append(("usuarios", "Usuarios", "👥"))
        
        # Caja: ADMIN + CAJERO puede ver
        items.append(("caja", "Caja", "💰"))
        
        # Historial: TODOS SIEMPRE (intacto)
        items.append(("historial", "Historial", "📋"))
        
        # Inventario: solo ADMIN
        if self._auth.puede(Permisos.ADMINISTRAR_PRODUCTOS):
            items.append(("inventario", "Inventario", "📦"))
        
        # Reportes: quienes tengan permiso
        if self._auth.puede(Permisos.CONSULTAR_REPORTES):
            items.append(("reportes", "Reportes", "📊"))
        
        # Configuracion: solo ADMIN
        if self._auth.puede(Permisos.MODIFICAR_CONFIGURACION):
            items.append(("configuracion", "Configuracion", "⚙️"))
        
        # GitHub Config: solo para TECNICO (ADMINISTRAR_SISTEMA)
        if self._auth.puede(Permisos.ADMINISTRAR_SISTEMA):
            items.append(("github_config", "GitHub Config", "🔧"))
        
        return items

    def _cargar_pantallas(self):
        """Carga pantallas con lazy loading"""
        self._fabrica_pantallas = {
            "mesas":         lambda: self._import_screen("mesas_screen", "MesasScreen"),
            "productos":     lambda: self._import_screen("productos_screen", "ProductosScreen"),
            "usuarios":      lambda: self._import_screen("usuarios_screen", "UsuariosScreen"),
            "caja":          lambda: self._import_screen("caja_screen", "CajaScreen"),
            "historial":     lambda: self._import_screen("historial_screen", "HistorialScreen"),
            "inventario":    lambda: self._import_screen("inventario_screen", "InventarioScreen"),
            "reportes":      lambda: self._import_screen("reportes_screen", "ReportesScreen"),
            "configuracion": lambda: self._import_screen("configuracion_screen", "ConfiguracionScreen"),
            "github_config": lambda: self._import_screen("github_config_screen", "GithubConfigScreen"),
        }

        self._pantallas = {}
        
        # Widget vacío inicial
        widget_vacio = QWidget()
        self._stack.addWidget(widget_vacio)
        
        # Cargar primera pantalla
        items = self._items_navegacion()
        if items:
            self._navegar(items[0][0])
    
    def _import_screen(self, module_name: str, class_name: str):
        """Importa pantalla de forma lazy"""
        module = __import__(f"app.ui.screens.{module_name}", fromlist=[class_name])
        screen_class = getattr(module, class_name)
        return screen_class(self._db, self._auth)

    def _navegar(self, key: str):
        """Navega a una pantalla SIN VALIDACIÓN DE PERMISOS"""
        print(f"Navegando a: {key}")
        
        # Cargar pantalla si no existe
        if key not in self._pantallas:
            if key in self._fabrica_pantallas:
                try:
                    print(f"  Cargando {key}...")
                    pantalla = self._fabrica_pantallas[key]()
                    self._pantallas[key] = pantalla
                    self._stack.addWidget(pantalla)
                    print(f"  ✓ {key} cargado")
                except Exception as e:
                    print(f"  ✗ Error cargando {key}: {e}")
                    import traceback
                    traceback.print_exc()
                    return
        
        # Desmarcar todos los botones
        for btn in self._nav_botones.values():
            btn.setChecked(False)
        
        # Marcar botón actual
        if key in self._nav_botones:
            self._nav_botones[key].setChecked(True)
        
        # Mostrar pantalla
        if key in self._pantallas:
            print(f"  Mostrando {key}")
            self._stack.setCurrentWidget(self._pantallas[key])
            pantalla = self._pantallas[key]
            if hasattr(pantalla, "refrescar"):
                pantalla.refrescar()

    def _cambiar_mi_password(self):
        from app.ui.widgets.dialogo_password import DialogoPassword
        dialogo = DialogoPassword(self._db, self._auth,
                                  id_usuario=None, parent=self)
        dialogo.exec()

    def _cerrar_sesion(self):
        self._auth.logout()
        from app.ui.login_window import LoginWindow
        self._login = LoginWindow(self._db)
        self._login.show()
        self.close()

    def _stylesheet(self) -> str:
        return """
        QMainWindow, QWidget {
            background: #0f172a;
            color: #e2e8f0;
            font-family: 'Segoe UI', 'Inter', sans-serif;
        }
        
        QFrame#sidebar {
            background: #1e293b;
            border-right: 2px solid #334155;
        }
        
        QLabel#sidebar_logo {
            font-size: 26px;
            font-weight: 700;
            color: #06b6d4;
            letter-spacing: 1px;
        }
        
        QFrame#sidebar_sep {
            color: #334155;
        }
        
        QPushButton#nav_btn {
            background: transparent;
            color: #cbd5e1;
            border: none;
            text-align: left;
            padding: 12px 16px;
            font-size: 13px;
            font-weight: 500;
            border-radius: 4px;
            margin: 2px 8px;
        }
        
        QPushButton#nav_btn:hover {
            background: #334155;
            color: #f1f5f9;
            border-left: 3px solid #06b6d4;
        }
        
        QPushButton#nav_btn:checked {
            background: #06b6d4;
            color: #0f172a;
            font-weight: 700;
            border-left: 3px solid #0891b2;
        }
        
        QLabel#sidebar_user {
            color: #94a3b8;
            font-size: 11px;
            padding: 12px;
        }
        
        QPushButton#btn_action {
            background: #3b82f6;
            color: #fff;
            border: none;
            padding: 8px;
            border-radius: 4px;
            margin: 4px 8px;
        }
        
        QPushButton#btn_action:hover {
            background: #2563eb;
        }
        
        QPushButton#btn_logout {
            background: #ef4444;
            color: #fff;
            border: none;
            padding: 8px;
            border-radius: 4px;
            margin: 4px 8px;
            font-weight: 600;
        }
        
        QPushButton#btn_logout:hover {
            background: #dc2626;
        }
        """
