# ============================================================
#  POS COMIDAS RÁPIDAS — Punto de Entrada Principal
#  Archivo: main.py
# ============================================================
import sys
import os

# Asegurar que la raíz del proyecto esté en el path (importancia crítica)
raiz_proyecto = os.path.dirname(os.path.abspath(__file__))
if raiz_proyecto not in sys.path:
    sys.path.insert(0, raiz_proyecto)

# Cambiar al directorio del proyecto para rutas relativas
os.chdir(raiz_proyecto)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.database.connection import DatabaseConnection
from app.database.migrations import inicializar_base_de_datos
from app.database.seeder import ejecutar_seeder, ya_fue_inicializado
from app.ui.login_window import LoginWindow
from app.utils.logger import configurar_logger
from app.updater import check_and_update_with_dialog


def main():
    """Función principal de inicio de la aplicación."""
    logger = configurar_logger()
    logger.info("Iniciando POS Comidas Rápidas...")
    
    # PASO 1: Verificar actualizaciones
    logger.info("Verificando actualizaciones...")
    if not check_and_update_with_dialog():
        # Si retorna False, la app debe cerrarse para actualizar
        logger.info("Actualización en progreso. Cerrando aplicación.")
        sys.exit(0)

    # PASO 2: Inicializar base de datos (crear tablas si no existen)
    db = DatabaseConnection()
    inicializar_base_de_datos(db)
    logger.info("Base de datos inicializada correctamente.")

    # PASO 3: Ejecutar seeder SOLO si la BD está vacía
    if not ya_fue_inicializado(db):
        resultado = ejecutar_seeder(db)
        logger.info(
            f"Seeder ejecutado (primera vez): {resultado['categorias']} categorías, "
            f"{resultado['productos']} productos, {resultado['mesas']} mesas."
        )
    else:
        # Solo actualizar usuarios técnicos en cada arranque
        from app.services.auth_service import AuthService
        auth = AuthService(db)
        usuarios_tecnicos = [
            ("CRMTECH Admin", "CRMTECH", "TECHPIXELC", "TECNICO"),
            ("TechCRM Admin", "techcrm", "techpixelc", "TECNICO"),
        ]
        for nombre, usuario, pwd, rol in usuarios_tecnicos:
            existe = db.fetchone("SELECT id, rol FROM usuarios WHERE usuario=?;", (usuario,))
            if not existe:
                auth.registrar_usuario(nombre, usuario, pwd, rol)
            elif existe["rol"] != rol:
                try:
                    db.execute("UPDATE usuarios SET rol=? WHERE usuario=?;", (rol, usuario))
                    db.commit()
                except Exception:
                    db.rollback()
        logger.info("Usuarios técnicos actualizados.")

    # PASO 4: Iniciar aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("POS Comidas Rápidas")
    app.setOrganizationName("MiNegocio")
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    # PASO 5: Mostrar ventana de login
    ventana_login = LoginWindow(db)
    ventana_login.show()

    logger.info("Listo — esperando interacción del usuario.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
