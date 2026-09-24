# ============================================================
#  app/utils/validators.py
#  Validaciones de datos de entrada
# ============================================================


def validar_precio(valor: str) -> tuple[bool, str]:
    """Valida que el valor sea un precio válido (positivo, numérico)."""
    try:
        p = float(valor.replace(",", ".").replace("$", "").strip())
        if p < 0:
            return False, "El precio no puede ser negativo."
        return True, ""
    except ValueError:
        return False, "Ingrese un valor numérico válido."


def validar_campo_requerido(valor: str, nombre: str) -> tuple[bool, str]:
    """Valida que el campo no esté vacío."""
    if not valor or not valor.strip():
        return False, f"El campo '{nombre}' es obligatorio."
    return True, ""


def validar_usuario(usuario: str) -> tuple[bool, str]:
    """Valida formato de usuario (3+ caracteres, solo letras y números)."""
    if len(usuario) < 3:
        return False, "El usuario debe tener al menos 3 caracteres."
    if not usuario.isalnum():
        return False, "El usuario solo puede contener letras y números."
    return True, ""


def validar_password(password: str) -> tuple[bool, str]:
    """Valida contraseña (mínimo 8 caracteres para seguridad)."""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    return True, ""
