# ============================================================
# TECHCRM POS - Instalador v4.0 FLAT (Todo en Misma Carpeta)
# Compatible con Windows 10 y 11
# ============================================================

param(
    [switch]$Uninstall
)

# Configuración
$AppName = "TECHCRM POS"
$InstallPath = "$env:ProgramFiles\TECHCRM POS"
$DesktopShortcut = "$env:Public\Desktop\TECHCRM POS.lnk"
$StartMenuFolder = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\TECHCRM POS"

# Verificar permisos de administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: Se requieren permisos de administrador." -ForegroundColor Red
    Write-Host "Haz click derecho en el instalador y selecciona 'Ejecutar como administrador'" -ForegroundColor Yellow
    Read-Host "Presiona ENTER para salir"
    exit 1
}

# Función para crear acceso directo
function Create-Shortcut {
    param($Path, $TargetPath, $IconLocation)
    
    $WScriptShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WScriptShell.CreateShortcut($Path)
    $Shortcut.TargetPath = $TargetPath
    $Shortcut.IconLocation = $IconLocation
    $Shortcut.WorkingDirectory = Split-Path $TargetPath
    $Shortcut.Save()
}

# DESINSTALACIÓN
if ($Uninstall) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " DESINSTALANDO $AppName" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    # Eliminar archivos
    if (Test-Path $InstallPath) {
        Write-Host "Eliminando archivos de programa..." -ForegroundColor Yellow
        Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✓ Archivos eliminados" -ForegroundColor Green
    }
    
    # Eliminar accesos directos
    if (Test-Path $DesktopShortcut) {
        Remove-Item -Path $DesktopShortcut -Force
        Write-Host "✓ Acceso directo del escritorio eliminado" -ForegroundColor Green
    }
    
    if (Test-Path $StartMenuFolder) {
        Remove-Item -Path $StartMenuFolder -Recurse -Force
        Write-Host "✓ Accesos del menú inicio eliminados" -ForegroundColor Green
    }
    
    # Eliminar entrada del registro
    $UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
    if (Test-Path $UninstallKey) {
        Remove-Item -Path $UninstallKey -Force
        Write-Host "✓ Registro limpio" -ForegroundColor Green
    }
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " DESINSTALACIÓN COMPLETADA" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Read-Host "Presiona ENTER para salir"
    exit 0
}

# INSTALACIÓN
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " INSTALADOR DE $AppName v4.0" -ForegroundColor Cyan
Write-Host " (Estructura FLAT - Todo en Misma Carpeta)" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verificar archivos fuente
$SourcePath = Split-Path $PSCommandPath
$ExePath = Join-Path $SourcePath "TECHCRM-POS.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "ERROR: No se encontró TECHCRM-POS.exe en:" -ForegroundColor Red
    Write-Host $SourcePath -ForegroundColor Yellow
    Read-Host "Presiona ENTER para salir"
    exit 1
}

Write-Host "✓ Archivos de instalación verificados" -ForegroundColor Green

# Crear directorio de instalación
Write-Host "`nCreando directorio de instalación..." -ForegroundColor Yellow
if (Test-Path $InstallPath) {
    Write-Host "  Eliminando instalación anterior..." -ForegroundColor Yellow
    Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
}

New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
Write-Host "✓ Directorio creado: $InstallPath" -ForegroundColor Green

# Copiar TODOS los archivos de la carpeta fuente
Write-Host "`nCopiando archivos (ESTRUCTURA FLAT - todo en misma carpeta)..." -ForegroundColor Yellow
Get-ChildItem -Path $SourcePath -Recurse | Where-Object { -not $_.PSIsContainer } | ForEach-Object {
    $RelativePath = $_.FullName.Substring($SourcePath.Length + 1)
    $DestPath = Join-Path $InstallPath $RelativePath
    $DestDir = Split-Path $DestPath
    
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }
    
    Copy-Item -Path $_.FullName -Destination $DestPath -Force
}
Write-Host "✓ Archivos copiados exitosamente" -ForegroundColor Green

# Crear acceso directo en escritorio
Write-Host "`nCreando acceso directo en escritorio..." -ForegroundColor Yellow
$ExeInstalled = Join-Path $InstallPath "TECHCRM-POS.exe"
Create-Shortcut -Path $DesktopShortcut -TargetPath $ExeInstalled -IconLocation $ExeInstalled
Write-Host "✓ Acceso directo creado" -ForegroundColor Green

# Crear carpeta en menú inicio
Write-Host "`nCreando accesos en menú inicio..." -ForegroundColor Yellow
if (-not (Test-Path $StartMenuFolder)) {
    New-Item -ItemType Directory -Path $StartMenuFolder -Force | Out-Null
}

$StartMenuShortcut = Join-Path $StartMenuFolder "TECHCRM POS.lnk"
Create-Shortcut -Path $StartMenuShortcut -TargetPath $ExeInstalled -IconLocation $ExeInstalled

# Crear acceso directo para desinstalar
$UninstallScript = Join-Path $InstallPath "Desinstalar.ps1"
Copy-Item -Path $PSCommandPath -Destination $UninstallScript -Force

$UninstallBat = Join-Path $InstallPath "Desinstalar.bat"
@"
@echo off
PowerShell.exe -ExecutionPolicy Bypass -File "%~dp0Desinstalar.ps1" -Uninstall
"@ | Out-File -FilePath $UninstallBat -Encoding ASCII

$UninstallShortcut = Join-Path $StartMenuFolder "Desinstalar TECHCRM POS.lnk"
Create-Shortcut -Path $UninstallShortcut -TargetPath $UninstallBat -IconLocation "shell32.dll,131"

Write-Host "✓ Accesos del menú inicio creados" -ForegroundColor Green

# Agregar al registro (Programas y Características)
Write-Host "`nRegistrando aplicación en Windows..." -ForegroundColor Yellow
$UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
New-Item -Path $UninstallKey -Force | Out-Null

Set-ItemProperty -Path $UninstallKey -Name "DisplayName" -Value $AppName
Set-ItemProperty -Path $UninstallKey -Name "DisplayVersion" -Value "4.0.0"
Set-ItemProperty -Path $UninstallKey -Name "Publisher" -Value "TechPixel"
Set-ItemProperty -Path $UninstallKey -Name "InstallLocation" -Value $InstallPath
Set-ItemProperty -Path $UninstallKey -Name "UninstallString" -Value "`"$UninstallBat`""
Set-ItemProperty -Path $UninstallKey -Name "DisplayIcon" -Value $ExeInstalled
Set-ItemProperty -Path $UninstallKey -Name "EstimatedSize" -Value 200000
Set-ItemProperty -Path $UninstallKey -Name "NoModify" -Value 1
Set-ItemProperty -Path $UninstallKey -Name "NoRepair" -Value 1

Write-Host "✓ Aplicación registrada" -ForegroundColor Green

# Resumen
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nRuta de instalación:" -ForegroundColor White
Write-Host "  $InstallPath" -ForegroundColor Yellow
Write-Host "`nAccesos directos creados en:" -ForegroundColor White
Write-Host "  - Escritorio" -ForegroundColor Yellow
Write-Host "  - Menú Inicio" -ForegroundColor Yellow
Write-Host "`nEstructura:" -ForegroundColor White
Write-Host "  - FLAT (todo en misma carpeta)" -ForegroundColor Yellow
Write-Host "`nPara desinstalar:" -ForegroundColor White
Write-Host "  - Desde Panel de Control > Programas" -ForegroundColor Yellow
Write-Host "  - O desde Menú Inicio > TECHCRM POS > Desinstalar" -ForegroundColor Yellow
Write-Host "`n========================================`n" -ForegroundColor Cyan

Write-Host "¿Deseas ejecutar TECHCRM POS ahora? (S/N): " -ForegroundColor Green -NoNewline
$response = Read-Host

if ($response -eq "S" -or $response -eq "s") {
    Write-Host "`nIniciando TECHCRM POS..." -ForegroundColor Yellow
    Start-Process -FilePath $ExeInstalled
}

Write-Host "`nInstalación finalizada. Presiona ENTER para salir." -ForegroundColor Cyan
Read-Host

# SIG # Begin signature block
# MIIFYQYJKoZIhvcNAQcCoIIFUjCCBU4CAQExCzAJBgUrDgMCGgUAMGkGCisGAQQB
# gjcCAQSgWzBZMDQGCisGAQQBgjcCAR4wJgIDAQAABBAfzDtgWUsITrck0sYpfvNR
# AgEAAgEAAgEAAgEAAgEAMCEwCQYFKw4DAhoFAAQU3DTGKz8ZS7NkpDbHYDCxlzqq
# eP2gggMAMIIC/DCCAeSgAwIBAgIQckhS3YzLj7dI33GgvG3BkzANBgkqhkiG9w0B
# AQsFADAWMRQwEgYDVQQDDAtURUNIQ1JNIFBPUzAeFw0yNjA5MjIxNTE0NTlaFw0z
# NjA5MjIxNTI0NTlaMBYxFDASBgNVBAMMC1RFQ0hDUk0gUE9TMIIBIjANBgkqhkiG
# 9w0BAQEFAAOCAQ8AMIIBCgKCAQEAxaf72oaCclhR5RegD9MgrD3BO6HKn7O1HJHg
# t0iuFuOgq1NnlCJOdFXvfn6Cvoe9VGFIO6xkmYdhRsMOjnRpoL9yYnCvS9rhG+p3
# 2Wm14YmwvAeuqBXHXyyc9dYIg6Vneg2Av1QZjxQE7J6kZuY+V84aHWiLVSaA6Sl0
# i1ywSs4IJ+KU1VuyYsApi0NxTGkjW7n2E0nKQAdGpphVkt1nI7aTDZYhLIWvmJCt
# 08Fvf2L2k4uAz6l4UxOMyE25txETpu8KmlsUycC4pqkMg/zxNdmnptammJbcXP2G
# xZm80nFOAR8lFgovzwN6/nHjtG/loEOAqzHeeO7AJjVuTWJVyQIDAQABo0YwRDAO
# BgNVHQ8BAf8EBAMCB4AwEwYDVR0lBAwwCgYIKwYBBQUHAwMwHQYDVR0OBBYEFI/0
# C4PLaEuzVBzg8h2vs+OODXqxMA0GCSqGSIb3DQEBCwUAA4IBAQCcq9OW4afKPwaT
# OpkP+y4YYgHaSd5Q2vm+/faHjkvCu4sL3la/KFsw0vKkxcTbfSdgfiQgjsLlcLbc
# NT2V2Sq/Ve0vxwUrnR8pSEEpLLL3/goyEh6b/sK4qZYY85skPkHmE9UUsnbN7sIW
# phErqpAIYMHgmzR+QmcMkYhgJU7/ZiGQbTFPyD1ThXTQG2cBBFqVDhTTED82zL41
# OxcCaUUW6Gfr6kvzkjNOqZRo6ujl1Bw7qSBg4PZolEUx3PmkDCCEcBqL92wajBEK
# gSTHfm67bSvruEcGUE9efGAMY+3JBXSKdCK5mYUslvKkB5q34qBO4d1qqYyzdWAb
# nzBFA6XKMYIByzCCAccCAQEwKjAWMRQwEgYDVQQDDAtURUNIQ1JNIFBPUwIQckhS
# 3YzLj7dI33GgvG3BkzAJBgUrDgMCGgUAoHgwGAYKKwYBBAGCNwIBDDEKMAigAoAA
# oQKAADAZBgkqhkiG9w0BCQMxDAYKKwYBBAGCNwIBBDAcBgorBgEEAYI3AgELMQ4w
# DAYKKwYBBAGCNwIBFTAjBgkqhkiG9w0BCQQxFgQUXXgT75ZqI+MYoMaBZLmSO6mN
# cpIwDQYJKoZIhvcNAQEBBQAEggEAv4q998D8NBOKPP5Baj/KcWgW3H78MGvJ20yy
# +fgMHOejUhXmRaVBbjqmqvPq2+Z8SlursoIcaOODSFmv4oWUEabKlab6hsaD4pBN
# zYQEPizu01G23bZfGqeOW2496/7zgS6rb1UT4mY4RVW4/I9vdfOgch5Zs2PjHYsI
# O4drPZ5JALqU1dVKmoA1hGxBjgVVkEqrdiPkz5wnGRTW5rTUYkF7ag+6o3TAb5vh
# IkhjCIyQ7JCYhoDITz8IVSjOksAJFUolq+rjDuDZ8uPslrASA0DPC/qCVNqPNULl
# bYKbWr2abben8QIIfzUhgo6JKqcIyQjzXrUBsyTtDmxg8Suyfg==
# SIG # End signature block
