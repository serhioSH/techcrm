# 🍔 CRM POS — Sistema de Punto de Venta para Comidas Rápidas

> **Aplicación de escritorio 100% local** para Windows. Optimizada para bajo-resource. **Con actualizaciones automáticas desde GitHub.**

---

## ✨ CARACTERÍSTICAS

- ✅ **Gestión de mesas y pedidos** en tiempo real
- ✅ **Sistema de caja** con apertura/cierre automático
- ✅ **Impresión térmica** en 58mm y 80mm
- ✅ **Reportes y exportación a Excel**
- ✅ **Control de usuarios** con permisos (ADMIN/CAJERO)
- ✅ **Historial completo** de ventas
- ✅ **Optimizado para bajo-resource** (2GB RAM mínimo)
- ✅ **Actualizaciones automáticas** desde GitHub
- ✅ **100% local** — No requiere internet para funcionar

---

## 🚀 INICIO RÁPIDO

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar en desarrollo
```bash
python main.py
```

### 3. Generar .exe para distribución
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py
```

El `.exe` estará en `dist/CRM.exe`

---

## 📚 DOCUMENTACIÓN

| Documento | Descripción |
|-----------|------------|
| **DOCUMENTACION.md** | 📖 Documentación técnica completa |
| **GITHUB_SETUP.md** | 🔧 Guía paso a paso para GitHub y actualizaciones |
| **PROYECTO.md** | 📋 Requerimientos originales del proyecto |

---

## 🔄 SISTEMA DE ACTUALIZACIONES

La app **verifica automáticamente** si hay nuevas versiones cada vez que se abre.

### Para actualizar tu código:

```bash
# 1. Haz cambios locales
# 2. Compila nuevo .exe
pyinstaller --onefile --windowed main.py

# 3. Actualiza versioninfo.json
{
  "version": "1.1",
  "download_url": "https://github.com/TUUSUARIO/CRM/releases/download/v1.1/CRM.exe"
}

# 4. Sube a GitHub
git add .
git commit -m "CRM v1.1 - New features"
git push

# 5. Crea Release en GitHub con el nuevo .exe
# Los clientes lo descargarán automáticamente
```

📖 **Ver GITHUB_SETUP.md para guía completa**

---

## 📁 ESTRUCTURA

```
CRM/
├── main.py              # Punto de entrada
├── app/                 # Código principal
│   ├── database/        # Base de datos
│   ├── models/          # Modelos de datos
│   ├── services/        # Lógica de negocio
│   ├── ui/              # Interfaz gráfica
│   ├── printing/        # Impresión térmica
│   ├── utils/           # Utilidades
│   └── updater.py       # ✨ Sistema de actualizaciones
├── DOCUMENTACION.md     # Documentación técnica
└── GITHUB_SETUP.md      # Guía de GitHub
```

---

## 🛠️ REQUERIMIENTOS

- **Windows** 7+
- **Python** 3.12+ (solo en desarrollo)
- **2GB RAM** mínimo
- **SQLite** (incluido)
- **Impresora térmica** (opcional)

---

## 👥 USUARIOS DE PRUEBA

Después de la primera ejecución (seeder):

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| `admin` | `admin123` | ADMIN |
| `cajero1` | `cajero123` | CAJERO |

---

## 🔐 SEGURIDAD

- ✅ Contraseñas hasheadas (SHA256)
- ✅ Permisos por rol
- ✅ Validación de entrada
- ✅ Transacciones SQLite
- ✅ Gestión de sesiones

---

## 📊 TECNOLOGÍAS

- **Backend**: Python 3.12, SQLite
- **Frontend**: PySide6 (Qt)
- **Reportes**: ReportLab, openpyxl
- **Distribución**: PyInstaller
- **Actualizaciones**: GitHub

---

## 🐛 TROUBLESHOOTING

**¿La app no actualiza?**
- Verifica conexión a internet
- Ver GITHUB_SETUP.md

**¿Errores de base de datos?**
- Ver DOCUMENTACION.md → Troubleshooting

**¿Impresora no funciona?**
- Ir a Configuración → Seleccionar impresora correcta

---

## 📝 NOTAS

- **Primera ejecución**: Se crea BD automáticamente (seeder)
- **Actualización**: Automática al abrir la app (si hay versión nueva)
- **Backup**: Se puede hacer desde Configuración → Backup
- **Logs**: Ver en `logs/app.log` para debugging

---

## 🎯 PRÓXIMOS PASOS

1. Leer **DOCUMENTACION.md** para entender la estructura
2. Leer **GITHUB_SETUP.md** para configurar actualizaciones
3. Ejecutar `python main.py` para probar
4. Generar `.exe` con PyInstaller
5. Subir a GitHub y crear Release

---

## ✅ VERSIÓN ACTUAL

**v1.0** - 19/09/2026  
Production Ready ✓

---

## 📞 SOPORTE

- Ver logs en `logs/app.log`
- Consultar DOCUMENTACION.md
- Contactar al desarrollador si es necesario

---

**Hecho con ❤️ para comidas rápidas** 🍔
