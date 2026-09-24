# 🚀 ACTUALIZACIÓN AUTOMÁTICA — GUÍA COMPLETA

> **Un documento con TODO lo que necesitas saber** para actualizar la app, compilarla, subirla a GitHub y que los usuarios reciban la actualización automáticamente.

---

## 📋 TABLA DE CONTENIDOS

1. [Cómo Funciona](#cómo-funciona)
2. [Flujo Completo](#flujo-completo)
3. [Paso 1: Hacer Cambios](#paso-1-hacer-cambios-en-el-código)
4. [Paso 2: Compilar .exe](#paso-2-compilar-el-exe)
5. [Paso 3: Subir a GitHub](#paso-3-subir-a-github)
6. [Paso 4: Crear Release](#paso-4-crear-release-en-github)
7. [Paso 5: Actualizar version.json](#paso-5-actualizar-versionjson)
8. [Verificación](#verificación-de-que-todo-funcione)
9. [Configuración de la App](#configuración-de-la-app)
10. [Archivos y Ubicaciones](#archivos-y-ubicaciones)
11. [Solución de Problemas](#solución-de-problemas)
12. [Checklist](#checklist-completo)

---

## ✨ Cómo Funciona

### Para el usuario final:
```
Usuario abre la app
    ↓
App verifica: ¿Hay versión nueva en GitHub?
    ↓
Si hay actualización:
  - Diálogo: "Actualización disponible. ¿Instalar?"
  - Usuario hace clic: "Sí"
  - Descarga automáticamente
  - Se instala y reinicia
    ↓
¡Listo! Usuario tiene la nueva versión
```

### Para el desarrollador (TÚ):
```
Haces cambios en código
    ↓
Compilas: pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py
    ↓
Subes a GitHub (código + Release con .exe)
    ↓
Actualizas version.json en GitHub
    ↓
¡Listo! Los usuarios ven "Actualización disponible"
```

---

## 📊 FLUJO COMPLETO

```
PASO 1: Hacer cambios en el código
    ↓
PASO 2: Compilar el .exe
    ↓
PASO 3: Subir a GitHub
    ↓
PASO 4: Crear Release en GitHub con el .exe
    ↓
PASO 5: Actualizar version.json en GitHub
    ↓
PASO 6: ✅ Los usuarios reciben la actualización automáticamente
```

---

## PASO 1: Hacer Cambios en el Código

### Editar archivos normalmente:

```
Modifica cualquier archivo .py en:
- app/ui/screens/           → Interfaz gráfica
- app/services/             → Lógica de negocio
- app/models/               → Modelos de datos
- app/database/             → Base de datos
- etc...
```

### Actualizar dependencias:

Si añades librerías, agrega a `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### Probar localmente:

```bash
python main.py
```

---

## PASO 2: Compilar el .exe

### Prerequisito (si no lo tienes):

```bash
pip install pyinstaller
```

### Compilar ejecutable:

```bash
pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py
```

**Esto genera:** `dist/main.exe`

### Renombrar a nombre oficial:

**En PowerShell:**
```powershell
Move-Item -Path "dist/main.exe" -Destination "dist/TECHCRM-POS.exe" -Force
```

**En Command Prompt:**
```cmd
move dist\main.exe dist\TECHCRM-POS.exe
```

### Verificar que funciona:

1. Haz **doble clic** en `dist/TECHCRM-POS.exe`
2. La app debe abrir correctamente
3. Prueba las funciones principales
4. Cierra la app

---

## PASO 3: Subir a GitHub

### Ver cambios:

```bash
git status
```

### Agregar todos los cambios:

```bash
git add .
```

### Hacer commit (describe bien el cambio):

```bash
git commit -m "v1.1 - Descripción de lo que hiciste"
```

**Ejemplos buenos:**
```bash
git commit -m "v1.1 - Nuevo sistema de reportes"
git commit -m "v1.2 - Corrección en cálculo de totales"
git commit -m "v1.3 - Mejorada impresora térmica"
```

### Subir a GitHub:

```bash
git push origin main
```

---

## PASO 4: Crear Release en GitHub

### En GitHub.com:

1. Ve a tu repositorio
2. Haz clic en **"Releases"** (lado derecho)
3. Haz clic en **"Create a new release"**

### Llena los datos:

**Tag version:** 
```
v1.1
```

**Release title:** 
```
TECHCRM-POS v1.1
```

**Description:** 
```
Cambios en esta versión:
- ✅ Mejora en pantalla de productos
- ✅ Corrección en reportes
- ✅ Soporte para impresoras nuevas
```

### Sube el .exe:

1. Haz clic en **"Attach binaries"** (o similar)
2. Selecciona: `dist/TECHCRM-POS.exe` de tu computadora
3. Haz clic en **"Publish release"**

### Copia la URL de descarga:

GitHub te genera una URL como:
```
https://github.com/TU_USUARIO/TU_REPO/releases/download/v1.1/TECHCRM-POS.exe
```

**Guarda esta URL, la necesitas en el siguiente paso.**

---

## PASO 5: Actualizar version.json

### Archivo version.json debe estar EN LA RAÍZ de tu repositorio:

```json
{
  "version": "1.1",
  "download_url": "https://github.com/TU_USUARIO/TU_REPO/releases/download/v1.1/TECHCRM-POS.exe",
  "release_date": "2026-09-23",
  "description": "Nuevas características y mejoras"
}
```

### Campos obligatorios:

| Campo | Ejemplo | Descripción |
|-------|---------|-------------|
| `version` | `"1.1"` | Número de versión |
| `download_url` | `https://github.com/.../TECHCRM-POS.exe` | URL de descarga del .exe |
| `release_date` | `"2026-09-23"` | Fecha de release |
| `description` | `"Nuevas características"` | Cambios realizados |

### Actualizar localmente:

1. Abre `version.json` en tu proyecto
2. Cambia `version` al nuevo número
3. Cambia `download_url` a la URL que copiaste en el Paso 4
4. Cambia `release_date` a la fecha de hoy

### Subir a GitHub:

```bash
git add version.json
git commit -m "Update version to 1.1"
git push origin main
```

---

## Verificación de que Todo Funcione

### 1. Verificar que version.json existe en GitHub:

En navegador, abre:
```
https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json
```

Debe mostrar el contenido JSON (no error 404).

### 2. Verificar que el .exe está en Releases:

En navegador, abre:
```
https://github.com/TU_USUARIO/TU_REPO/releases
```

Debe aparecer tu Release con el .exe.

### 3. Verificar que la URL de descarga funciona:

Prueba la URL en navegador:
```
https://github.com/TU_USUARIO/TU_REPO/releases/download/vX.X/TECHCRM-POS.exe
```

Debe descargar el archivo (no error).

### 4. Los usuarios verán la actualización:

Cuando abran la app y hay versión nueva:
- Diálogo: **"Actualización disponible. Versión X.X disponible. ¿Descargar e instalar?"**
- El usuario hace clic: **"Sí"**
- Se descarga automáticamente
- Se instala y reinicia

---

## Configuración de la App

### Cómo la app sabe dónde buscar actualizaciones:

La app lee la configuración guardada en:
```
%LOCALAPPDATA%\TECHCRM\config.json
```

Busca la clave:
```json
{
  "github": {
    "version_check_url": "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json"
  }
}
```

### Configurar esto (Una sola vez):

**Opción A: Desde la app (interfaz gráfica)**

1. Abre la app con usuario **TECNICO**
2. Ve a: **Configuración** → **Sección Admin**
3. Ingresa la URL:
   ```
   https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json
   ```
4. Haz clic en **"Guardar"**
5. Se guarda automáticamente en `config.json`

**Opción B: Editar manualmente**

Edita `%LOCALAPPDATA%\TECHCRM\config.json`:

```json
{
  "github": {
    "version_check_url": "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json",
    "download_url": ""
  }
}
```

---

## Archivos y Ubicaciones

### En tu computadora (desarrollo):

```
CRM/
├── main.py                  ← Punto de entrada
├── requirements.txt         ← Dependencias
├── version.json            ← Archivo de versión (IMPORTANTE)
├── app/                    ← Código fuente
├── dist/
│   └── TECHCRM-POS.exe    ← Compilado (NO subir a rama main)
├── build/                  ← Temporal (NO subir)
├── README.md
└── ACTUALIZACION.md        ← Este documento
```

### En GitHub:

```
TU_REPO/
├── main.py
├── requirements.txt
├── version.json            ← En la RAÍZ (muy importante)
├── app/
└── Releases/
    └── v1.1/
        └── TECHCRM-POS.exe ← Solo aquí, no en rama main
```

### En la computadora del usuario:

```
%LOCALAPPDATA%\TECHCRM\
├── config.json             ← Contiene URL de version.json
├── crm_system.db          ← Base de datos
├── logs/                  ← Archivos de log
├── backups/               ← Copias de seguridad
└── comprobantes/          ← Documentos generados
```

---

## Solución de Problemas

### "PyInstaller no encontrado"

```bash
pip install pyinstaller
```

### "El .exe no se compila"

1. Asegúrate de que Python 3.12+ está instalado
2. Reinstala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Intenta nuevamente

### "El .exe falla al iniciar"

1. Prueba en modo desarrollo: `python main.py`
2. Si funciona localmente pero falla el .exe:
   - Asegúrate que `requirements.txt` esté actualizado
   - Vuelve a compilar
3. Ver logs: `logs/app.log`

### "Los usuarios no ven la actualización"

1. Verifica que `version.json` está en la **raíz** de GitHub
2. Verifica la URL en navegador:
   ```
   https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json
   ```
3. Espera 5-10 minutos (caché de GitHub)
4. En la app, verifica Configuración → Admin que tenga la URL correcta

### "La URL de descarga no funciona"

1. Verifica que el Release está **publicado** (no borrador)
2. Verifica que el .exe está attached al Release
3. Copia la URL exacta desde GitHub
4. La URL debe ser: `https://github.com/.../download/vX.X/TECHCRM-POS.exe`

### "El .exe descarga pero no se instala"

- Asegúrate que `requirements.txt` está correcto
- Vuelve a compilar con PyInstaller
- Prueba manualmente: haz doble clic en el .exe

---

## CHECKLIST Completo (Para cada actualización)

Antes de considerar que está listo:

```
DESARROLLO:
☐ Edité los archivos necesarios en app/
☐ Probé localmente: python main.py
☐ Actualicé requirements.txt si cambié librerías

COMPILACIÓN:
☐ Compilé: pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py
☐ Renombré: dist/main.exe → dist/TECHCRM-POS.exe
☐ Probé el .exe (doble clic y funcionó correctamente)

GITHUB - CÓDIGO:
☐ git status (verifiqué cambios)
☐ git add .
☐ git commit -m "v1.X - Descripción"
☐ git push origin main

GITHUB - RELEASE:
☐ Creé Release en GitHub
☐ Tagueé como: v1.X
☐ Subí dist/TECHCRM-POS.exe al Release
☐ Publiqué Release
☐ Copié URL de descarga del .exe

GITHUB - VERSION:
☐ Actualicé version.json localmente:
   - version: "1.X"
   - download_url: URL copiada
   - release_date: hoy
☐ git add version.json
☐ git commit -m "Update version to 1.X"
☐ git push origin main

VERIFICACIÓN:
☐ Verifiqué que version.json se ve en:
   https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json
☐ Verifiqué que el Release está en GitHub
☐ Verifiqué que la URL de descarga funciona

RESULTADO FINAL:
☐ ✅ Los usuarios recibirán la actualización automáticamente
```

---

## 📚 Referencias Rápidas

### Comando: Compilar

```bash
pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py
```

### Comando: Renombrar (PowerShell)

```powershell
Move-Item -Path "dist/main.exe" -Destination "dist/TECHCRM-POS.exe" -Force
```

### Comando: Git completo

```bash
git add .
git commit -m "v1.X - Cambios"
git push origin main
```

### URL: version.json en GitHub

```
https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json
```

### Ubicación: Configuración del usuario

```
%LOCALAPPDATA%\TECHCRM\config.json
```

---

## 🎯 Flujo Típico (Ejemplo Real)

### **Día 1: Versión 1.0**

```bash
# 1. Código listo, compilas
pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py

# 2. Renombras
Move-Item -Path "dist/main.exe" -Destination "dist/TECHCRM-POS.exe" -Force

# 3. Subes a GitHub
git add .
git commit -m "v1.0 - Release inicial"
git push origin main

# 4. En GitHub: Creas Release v1.0
#    - Subes dist/TECHCRM-POS.exe
#    - Copias URL: https://github.com/.../download/v1.0/TECHCRM-POS.exe

# 5. Actualizas version.json:
{
  "version": "1.0",
  "download_url": "https://github.com/.../download/v1.0/TECHCRM-POS.exe",
  "release_date": "2026-09-23",
  "description": "Release inicial"
}

# 6. Subes version.json
git add version.json
git commit -m "Update version to 1.0"
git push origin main

# 7. ✅ Los usuarios tienen v1.0
```

### **Una semana después: Versión 1.1**

```bash
# 1. Hiciste cambios en app/services/venta_service.py (ejemplo)

# 2. Compilas
pyinstaller --onefile --windowed --icon app/assets/icon.ico main.py
Move-Item -Path "dist/main.exe" -Destination "dist/TECHCRM-POS.exe" -Force

# 3. Subes a GitHub
git add .
git commit -m "v1.1 - Mejoras en ventas"
git push origin main

# 4. Creas Release v1.1 en GitHub con el nuevo .exe
#    Copias: https://github.com/.../download/v1.1/TECHCRM-POS.exe

# 5. Actualizas version.json
{
  "version": "1.1",
  "download_url": "https://github.com/.../download/v1.1/TECHCRM-POS.exe",
  "release_date": "2026-09-30",
  "description": "Mejoras en sistema de ventas"
}

# 6. Subes version.json
git add version.json
git commit -m "Update version to 1.1"
git push origin main

# 7. ✅ Los usuarios ven "Actualización disponible"
#    Hacen clic "Sí" → Descargan v1.1 automáticamente
```

---

## ✅ ¡LISTO!

Cuando sigas estos pasos **exactamente**:

✅ Tu código está limpio en GitHub  
✅ El `.exe` compilado está en Releases  
✅ Los usuarios reciben updates automáticas  
✅ No necesitas hacer nada más  

**El sistema de actualización automática está 100% operativo.**

---

**Versión del documento:** 1.0  
**Fecha:** 23/09/2026  
**Estado:** ✅ LISTO PARA PRODUCCIÓN
