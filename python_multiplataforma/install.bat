@echo off
setlocal enabledelayedexpansion

set logFile=%USERPROFILE%\install_log.txt
echo Iniciando instalación de Python 3... > "%logFile%"
echo ====================================== >> "%logFile%"

echo Verificando la instalación de Python 3... >> "%logFile%"

set pythonPath=null
set foundNonWindowsApps=0

:: Buscar rutas con where python
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo Ruta encontrada: %%i >> "%logFile%"
    echo %%i | findstr /i "WindowsApps" >nul
    if !errorlevel! equ 0 (
        echo Ignorando ruta en WindowsApps: %%i >> "%logFile%"
    ) else (
        set pythonPath=%%i
        set foundNonWindowsApps=1
        echo Ruta válida de Python encontrada: %%i >> "%logFile%"
    )
)

if !foundNonWindowsApps! equ 0 (
    echo No se encontró Python válido fuera de WindowsApps. Procediendo a instalar Python... >> "%logFile%"
    echo No se encontró Python válido fuera de WindowsApps. Procediendo a instalar Python...
    goto :InstallPython
) else (
    echo Python válido encontrado en !pythonPath!. No se instalará Python. >> "%logFile%"
    echo Python válido encontrado en !pythonPath!. No se instalará Python.
    goto :InstallDeps
)

:InstallPython
:: Verificar arquitectura
set arch=64
if /i not "%PROCESSOR_ARCHITECTURE%"=="AMD64" set arch=32

if "%arch%"=="64" (
    set pythonInstallerUrl=https://www.python.org/ftp/python/3.13.0/python-3.13.0-amd64.exe
) else (
    set pythonInstallerUrl=https://www.python.org/ftp/python/3.13.0/python-3.13.0.exe
)

set installerPath=%TEMP%\python-installer.exe

echo Descargando Python desde %pythonInstallerUrl%... >> "%logFile%"
powershell -Command "try { Invoke-WebRequest -Uri '%pythonInstallerUrl%' -OutFile '%installerPath%' -UseBasicParsing } catch { exit 1 }" >> "%logFile%" 2>&1

if not exist "%installerPath%" (
    echo Error: No se pudo descargar el instalador de Python. >> "%logFile%"
    echo Error: No se pudo descargar el instalador de Python.
    exit /b 1
) else (
    echo Descarga completada exitosamente. >> "%logFile%"
)

echo Instalando Python... >> "%logFile%"
start /wait "" "%installerPath%" /quiet InstallAllUsers=1 PrependPath=1

:: Verificar si Python está correctamente instalado
where python >nul 2>nul
if errorlevel 1 (
    echo Error: No se pudo instalar Python. >> "%logFile%"
    echo Error: No se pudo instalar Python.
    exit /b 1
) else (
    echo Python instalado correctamente. >> "%logFile%"
    echo Python instalado correctamente.
)

:: Verificar si pip está instalado
echo Verificando pip... >> "%logFile%"
python -m ensurepip --upgrade >> "%logFile%" 2>&1

python -m pip --version >> "%logFile%" 2>&1
if errorlevel 1 (
    echo Error: pip no está disponible. >> "%logFile%"
    echo Error: pip no está disponible.
    exit /b 1
) else (
    echo pip instalado correctamente. >> "%logFile%"
    echo pip instalado correctamente.
)

:InstallDeps
echo Instalando dependencias con pip... >> "%logFile%"
if not exist "requirements.txt" (
    echo Error: No se encontró requirements.txt >> "%logFile%"
    echo Error: No se encontró requirements.txt
    exit /b 1
)

python -m pip install -r requirements.txt >> "%logFile%" 2>&1
if errorlevel 1 (
    echo Error: No se pudieron instalar las dependencias. >> "%logFile%"
    echo Error: No se pudieron instalar las dependencias.
    exit /b 1
) else (
    echo Dependencias instaladas correctamente. >> "%logFile%"
    echo Dependencias instaladas correctamente.
)

:: Copiar archivos a carpeta destino
echo Copiando archivos a la carpeta destino... >> "%logFile%"
set sourcePkgDir=C:\Users\firstatack\Desktop\python_multiplataforma\pkg
set destinationDir=%USERPROFILE%\.iaPS3\pkg

if exist "%sourcePkgDir%" (
    xcopy /E /I /H /Y "%sourcePkgDir%\*" "%destinationDir%\" >> "%logFile%"
    echo Archivos copiados a %destinationDir%. >> "%logFile%"
    echo Archivos copiados a %destinationDir%.
) else (
    echo Carpeta origen no encontrada: %sourcePkgDir% >> "%logFile%"
    echo Carpeta origen no encontrada: %sourcePkgDir%.
)

:: Copiar scripts
echo Copiando scripts al directorio PS3_Downloader... >> "%logFile%"
set ps3DownloaderDir=%USERPROFILE%\PS3_Downloader
if not exist "%ps3DownloaderDir%" mkdir "%ps3DownloaderDir%"

copy /Y "ps3IAPKGv1_gui.py" "%ps3DownloaderDir%\" >> "%logFile%"
copy /Y "ps3IAPKGv1.py" "%ps3DownloaderDir%\" >> "%logFile%"

:: Crear acceso directo en el escritorio
echo Creando acceso directo en el escritorio...

set desktopPath=%USERPROFILE%\Desktop
set shortcutPath=%desktopPath%\PS3 IAPKG Shortcut.lnk
set scriptPath=%ps3DownloaderDir%\ps3IAPKGv1_gui.py

echo Set owshell = CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo Set shortcut = owshell.CreateShortcut("%shortcutPath%") >> "%TEMP%\create_shortcut.vbs"
echo shortcut.TargetPath = "python.exe" >> "%TEMP%\create_shortcut.vbs"
echo shortcut.Arguments = """%scriptPath%""" >> "%TEMP%\create_shortcut.vbs"
echo shortcut.Save >> "%TEMP%\create_shortcut.vbs"

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

echo Acceso directo creado en el escritorio.
echo ¡Instalación y configuración completadas con éxito!

endlocal
exit /b 0

