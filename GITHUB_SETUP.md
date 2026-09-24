# 🚀 GUÍA DE SETUP EN GITHUB — SISTEMA DE ACTUALIZACIONES

> Esta guía te explica cómo configurar GitHub para que las actualizaciones funcionen automáticamente.

---

## 📋 PASO 1: Crear repositorio en GitHub

### A. Crear cuenta (si no tienes)
1. Ve a https://github.com
2. Click en "Sign up"
3. Completa el formulario
4. Verifica tu email

### B. Crear repositorio
1. Click en tu avatar (arriba a la derecha) → "Your repositories"
2. Click en "New" (botón verde)
3. Nombre: `CRM` (o el que prefieras)
4. Descripción: "Sistema POS para comidas rápidas"
5. **Tipo: PUBLIC** (importante para que se descargue)
6. Deja otras opciones por defecto
7. Click en "Create repository"

---

## 📌 PASO 2: Configurar Git en tu PC

### A. Instalar Git
1. Descarga de https://git-scm.com
2. Instala con opciones por defecto

### B. Configurar tu identidad
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tuemail@gmail.com"
```

### C. Generar SSH key (opcional pero recomendado)
```bash
ssh-keygen -t rsa -b 4096 -C "tuemail@gmail.com"
# Presiona Enter 3 veces
# Luego copia la key:
cat ~/.ssh/id_rsa.pub
```

Ve a GitHub → Settings → SSH Keys → New SSH Key → Pega la clave

---

## 🔧 PASO 3: Subir tu código a GitHub

### En tu carpeta del proyecto:

```bash
# Navega a la carpeta del proyecto
cd c:\Users\duvan\OneDrive\Desktop\sergio\CRM

# Inicializa git (si es la primera vez)
git init

# Agregar todos los archivos
git add .

# Crear primer commit
git commit -m "CRM v1.0 - Versión inicial"

# Conectar a tu repositorio remoto
# Copia la URL de tu repositorio de GitHub y reemplaza aquí:
git remote add origin https://github.com/TUUSUARIO/CRM.git

# Subir los cambios
git branch -M main
git push -u origin main
```

✅ **Listo**. Tu código está en GitHub.

---

## 📝 PASO 4: Configurar versioninfo.json

### A. Editar archivo local
Abre `versioninfo.json` en tu proyecto:

```json
{
  "version": "1.0",
  "download_url": "https://github.com/TUUSUARIO/CRM/releases/download/v1.0/CRM.exe",
  "changelog": "Versión inicial - Sistema POS",
  "release_date": "2026-09-19",
  "required_update": false,
  "notes": "Primera versión estable"
}
```

**CAMBIA:**
- `TUUSUARIO` → Tu usuario de GitHub
- `version` → La versión actual
- `download_url` → URL donde estará tu .exe

### B. Subir los cambios
```bash
git add versioninfo.json
git commit -m "Update versioninfo to v1.0"
git push
```

---

## 📦 PASO 5: Crear Release con el .exe

### A. Generar el .exe con PyInstaller

```bash
# Instalar PyInstaller
pip install pyinstaller

# Compilar
pyinstaller --onefile --windowed --icon=app/assets/icon.ico main.py

# El .exe estará en: dist/main.exe
```

### B. Crear Release en GitHub
1. Ve a tu repositorio → "Releases" (a la derecha)
2. Click en "Create a new release"
3. **Tag name**: `v1.0` (debe coincidir con versión en versioninfo.json)
4. **Release title**: `CRM v1.0 - Sistema POS`
5. **Description**: 
```
- Sistema POS completo
- Optimizado para bajo-resource
- Soporte para impresora térmica
```
6. **Upload files**: Arrastra `dist/main.exe` aquí
7. Click en "Publish release"

✅ **Listo**. Tu .exe está disponible para descargar.

---

## 🔄 PASO 6: Para futuras actualizaciones

### Cuando quieras actualizar:

**1. Haz cambios en tu código**
```bash
# ... edita archivos ...

# Compila el .exe de nuevo
pyinstaller --onefile --windowed --icon=app/assets/icon.ico main.py
```

**2. Actualiza versión**
Edita `versioninfo.json`:
```json
{
  "version": "1.1",
  "download_url": "https://github.com/TUUSUARIO/CRM/releases/download/v1.1/CRM.exe",
  ...
}
```

**3. Sube cambios a GitHub**
```bash
git add .
git commit -m "CRM v1.1 - Fix bugs"
git push
```

**4. Crea nueva Release**
- Repeat pasos del PASO 5
- Tag: `v1.1`
- Upload nuevo .exe

**5. Listo**
Los clientes verán el update automáticamente la próxima vez que abran la app.

---

## ✅ VERIFICACIÓN

Para verificar que todo está correcto:

1. **Abre tu repositorio en GitHub**
   - ¿Ves todos tus archivos? ✓

2. **Ve a Releases**
   - ¿Ves tu versión con el .exe? ✓

3. **Abre versioninfo.json en GitHub**
   - ¿El URL es correcto? ✓

4. **Prueba descargando el .exe desde Release**
   - ¿Se descarga correctamente? ✓

5. **En tu app, edita app/updater.py**
   - Línea 13: Cambia `VERSION_CHECK_URL`
   - Debe apuntar a: `https://raw.githubusercontent.com/TUUSUARIO/CRM/main/versioninfo.json`

---

## 🐛 TROUBLESHOOTING

**"Error: fatal: 'origin' does not appear to be a 'git' repository"**
```bash
# Solución:
git remote add origin https://github.com/TUUSUARIO/CRM.git
```

**"Permission denied (publickey)"**
```bash
# Solución: Agregar SSH key a GitHub
# Ver paso 2C
```

**"El update no descarga"**
- Verifica que `VERSION_CHECK_URL` sea correcto
- Verifica que el repo sea **PUBLIC** (no private)
- Verifica la conexión a internet

**"El .exe no se actualiza en el cliente"**
- Cierra la app completamente
- Abre de nuevo
- Debería preguntar por actualización

---

## 📊 RESUMEN

```
Tú haces cambios
    ↓
Compilas con PyInstaller (main.exe)
    ↓
Subes a GitHub con git push
    ↓
Creas Release con el .exe
    ↓
Actualizas versioninfo.json
    ↓
Cliente abre la app
    ↓
App verifica versioninfo.json
    ↓
Ve que hay nueva versión
    ↓
Pregunta: "¿Actualizar?"
    ↓
Cliente dice "Sí"
    ↓
Descarga nuevo .exe
    ↓
Se reinicia automáticamente
    ↓
Listo con nueva versión ✓
```

---

## 🎯 CHEAT SHEET (Comandos rápidos)

```bash
# Después de hacer cambios:
git add .
git commit -m "CRM v1.X - Descripción del cambio"
git push

# Ver status
git status

# Ver histórico
git log --oneline

# Deshacer último commit (si metiste la pata)
git reset --soft HEAD~1
```

---

**Listo. Ya puedes actualizar tu app automáticamente desde GitHub.** 🚀
