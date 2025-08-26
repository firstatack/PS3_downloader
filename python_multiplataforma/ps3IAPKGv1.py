#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descargador y Procesador en Cola de PS3 (Python puro)

- Reemplaza fzf, jq y curl por Python.
- Funciona en Windows y Linux.
- Usa la librería oficial `internetarchive` en lugar del binario `ia`.
- Descarga de enlaces PKG con `requests`.
- Mantiene el flujo y funciones del script Bash original.

Requisitos (instalar con pip):
    pip install internetarchive requests colorama

Nota: El procesamiento con `libray` sigue invocando el ejecutable externo si está instalado
      (igual que el script original). Si no lo tienes, omite la parteb de procesamiento.
"""

from __future__ import annotations
import os
import re
import sys
import time
import json
import shutil
import signal
import getpass
from pathlib import Path
from typing import List, Tuple, Dict

# --- Dependencias de red ---
import requests
try:
    import internetarchive as ia
except ImportError:
    print("[ERROR] Falta la dependencia 'internetarchive'. Instala con: pip install internetarchive")
    sys.exit(1)

# Colores cross-platform
try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init()  # habilita ANSI en Windows
    rojo = Style.BRIGHT + Fore.RED
    cyan = Style.BRIGHT + Fore.CYAN
    verde = Style.BRIGHT + Fore.GREEN
    amarillo = Style.BRIGHT + Fore.YELLOW
    reset = Style.RESET_ALL
except Exception:
    # Fallback a códigos ANSI simples (en Windows antiguos puede no colorear)
    rojo = '\x1b[1;31m'
    cyan = '\x1b[1;36m'
    verde = '\x1b[1;32m'
    amarillo = '\x1b[1;33m'
    reset = '\x1b[0m'

# --- Rutas y carpetas ---
HOME = Path.home()
IA_PS3_DIR = HOME / ".iaPS3"
LOGS_DIR = IA_PS3_DIR / "logs"
PKG_DIR = IA_PS3_DIR / "pkg"
CACHE_FILE = IA_PS3_DIR / "ps3_items_cache.txt"
IA_PS3_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
PKG_DIR.mkdir(parents=True, exist_ok=True)

# --- Utilidades ---


def hora() -> str:
    return time.strftime("%H:%M:%S", time.localtime())


def printf(msg: str) -> None:
    sys.stdout.write(msg)
    sys.stdout.flush()


def press_enter() -> None:
    try:
        input("Presiona Enter para continuar...")
    except EOFError:
        pass


# Señales (Ctrl+C)
RUNNING = True


def finalizar(sig=None, frame=None):
    global RUNNING
    printf(f"{rojo}\n\n Finalizando el script{reset}\n")
    RUNNING = False
    sys.exit(0)


signal.signal(signal.SIGINT, finalizar)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, finalizar)

# --- Configuración de cuenta de Internet Archive ---
IA_CONFIG_PATH = HOME / ".config" / "internetarchive" / "config"


def leer_config_ia() -> str:
    if IA_CONFIG_PATH.exists():
        return IA_CONFIG_PATH.read_text(encoding="utf-8", errors="ignore")
    return ""


def escribir_config_ia(access: str, secret: str) -> None:
    IA_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    contenido = (
        "[s3]\n"
        f"access = {access}\n"
        f"secret = {secret}\n"
    )
    IA_CONFIG_PATH.write_text(contenido, encoding="utf-8")


def configurar_cuenta_ia() -> None:
    printf(f"\n{amarillo}🔐 Configuración de cuenta Internet Archive{reset}\n")
    printf(f"{cyan}Se necesitan credenciales para acceder a archive.org{reset}\n\n")

    if IA_CONFIG_PATH.exists():
        printf(f"{verde}✓ Configuración existente detectada{reset}\n")
        printf("Deseas:\n")
        printf("1. Ver configuración actual\n")
        printf("2. Configurar nuevas credenciales\n")
        printf("3. Volver al menú\n")
        opcion = input("Elige (1-3): ").strip()
        if opcion == "1":
            print(f"\n{cyan}Configuración actual:{reset}\n")
            print(leer_config_ia())
            print()
        elif opcion == "2":
            access = input("Introduce tu Access Key: ").strip()
            secret = getpass.getpass("Introduce tu Secret Key: ")
            escribir_config_ia(access, secret)
            print(f"{verde}✓ Credenciales guardadas.{reset}")
        elif opcion == "3":
            return
        else:
            print(f"{rojo}Opción no válida{reset}")
    else:
        printf(f"{amarillo}No se detectó configuración existente{reset}\n")
        access = input("Introduce tu Access Key: ").strip()
        secret = getpass.getpass("Introduce tu Secret Key: ")
        escribir_config_ia(access, secret)
        print(f"{verde}✓ Credenciales guardadas.{reset}")

    press_enter()

# --- Menú principal ---


def clear_screen() -> None:
    try:
        os.system("cls" if os.name == "nt" else "clear")
    except Exception:
        pass


def mostrar_menu_principal() -> None:
    clear_screen()
    print()
    print(f"{rojo}====================================================")
    print(f"  {cyan}👾 Descargador y Procesador en Cola de PS3 👾{reset}")
    print(f"{rojo}===================================================={reset}")
    print()
    print(f"  {verde}➜ ¡Bienvenido! Elige el origen de descarga:{reset}")
    print()
    print(f"  {amarillo}1.{reset} {cyan}Descargar desde Archive.org{reset}")
    print(f"  {amarillo}2.{reset} {cyan}Descargar desde enlaces PKG{reset}")
    print(f"  {amarillo}3.{reset} {cyan}Configurar cuenta Archive.org{reset}")
    print(f"  {amarillo}4.{reset} {rojo}Salir{reset}")
    print()
    print(f"{cyan}====================================================")
    print(f"{rojo}       De firstatack para gamers con problemas {reset}")
    print(f"{cyan}===================================================={reset}")


# --- Utilidades de selección ---

def elegir_uno(opciones: List[str], prompt: str) -> int:
    """Muestra opciones numeradas y devuelve el índice elegido (o -1 si none)."""
    if not opciones:
        return -1
    for i, op in enumerate(opciones, 1):
        print(f"  [{i}] {op}")
    while True:
        s = input(f"{prompt} (1-{len(opciones)}): ").strip()
        if not s:
            return -1
        if s.isdigit() and 1 <= int(s) <= len(opciones):
            return int(s) - 1
        print("Entrada no válida. Intenta de nuevo.")


def elegir_multi(opciones: List[str], prompt: str) -> List[int]:
    """Devuelve una lista de índices a partir de una entrada tipo 1,3,5-7."""
    if not opciones:
        return []
    for i, op in enumerate(opciones, 1):
        print(f"  [{i}] {op}")
    while True:
        s = input(f"{prompt} (ej: 1,3,5-7): ").strip()
        if not s:
            return []
        try:
            idxs: List[int] = []
            for part in s.split(','):
                part = part.strip()
                if '-' in part:
                    a, b = part.split('-', 1)
                    a, b = int(a), int(b)
                    idxs.extend(list(range(a, b + 1)))
                else:
                    idxs.append(int(part))
            # normaliza a 0-based y filtra
            idxs0 = sorted({i-1 for i in idxs if 1 <= i <= len(opciones)})
            return idxs0
        except Exception:
            print("Entrada no válida. Intenta de nuevo.")

# --- Lado Archive.org ---


SEARCH_QUERY = "sony_playstation3"  # similar a bash


def actualizar_cache_items() -> bool:
    print(
        f"{rojo}[{hora()}]{cyan} 🔄 Actualizando lista de ítems desde archive.org...{reset}")
    try:
        # Buscamos por colección/juegos PS3; filtramos identifiers que empiecen por sony_playstation3_
        results = ia.search_items(SEARCH_QUERY)
        identifiers = []
        for r in results:
            ident = r.get('identifier')
            if ident and ident.startswith('sony_playstation3_'):
                identifiers.append(ident)
        identifiers = sorted(set(identifiers))
        if identifiers:
            CACHE_FILE.write_text("\n".join(identifiers), encoding="utf-8")
            print(
                f"{rojo}[{hora()}]{verde}✅ Lista actualizada y guardada en {CACHE_FILE}{reset}")
            return True
        else:
            print(
                f"{rojo}[{hora()}]❌ Error: no se pudo actualizar la lista o está vacía.{reset}")
            return False
    except Exception as e:
        print(f"{rojo}[{hora()}]❌ Error de búsqueda: {e}{reset}")
        return False


def descargar_archivo(item_identifier: str, file_name: str, dest_dir: Path) -> bool:
    log_file = LOGS_DIR / \
        f"download_{re.sub(r'[^a-zA-Z0-9]', '_', file_name)}.log"
    print(f"{rojo}[{hora()}] {cyan}📥 Descargando: {reset}{file_name}...")
    try:
        item = ia.get_item(item_identifier)
        # internetarchive permite descargar un archivo concreto con patterns=False y archivos exactos
        # Descargamos dentro de dest_dir / item_identifier, tal como hacía 'ia download'
        dest = dest_dir / item_identifier
        dest.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as lf:
            # Descargar recorriendo los ficheros del item y buscando coincidencia exacta por nombre
            target = next(
                (f for f in item.files if f.get('name') == file_name), None)
            if not target:
                lf.write(
                    f"Archivo {file_name} no encontrado en {item_identifier}.\n")
                print(
                    f"{rojo}[{hora()}] ❌ No se encontró {file_name} en {item_identifier}.{reset}")
                return False
            url = target.get('url') or target.get('file_url')
            if not url:
                # Construcción manual
                # https://archive.org/download/<identifier>/<file_name>
                url = f"https://archive.org/download/{item_identifier}/{file_name}"
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            out_path = dest / file_name
            with open(out_path, 'wb') as f_out:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f_out.write(chunk)
            lf.write(f"Descargado: {out_path}\n")
        print(f"{rojo}[{hora()}]{verde}✅ Descarga completa:{reset} {file_name}")
        return True
    except Exception as e:
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write(f"Error: {e}\n")
        print(
            f"{rojo}[{hora()}] ❌ Error descargando {file_name}. Revisa '{log_file}'.{reset}")
        return False


def sanitize_filename(name: str) -> str:
    # Reemplaza espacios por _, quita comillas y caracteres extraños, deja a-zA-Z0-9._-
    x = name.replace(' ', '_').replace("'", '').replace('"', '')
    x = re.sub(r"[^a-zA-Z0-9._-]", '', x)
    return x


def procesar_archivo_con_libray(input_file: Path, output_file: Path) -> None:
    log_file = LOGS_DIR / \
        f"libray_{re.sub(r'[^a-zA-Z0-9]', '_', input_file.name)}.log"
    item_dir = input_file.parent

    print(f"{rojo}[{hora()}] {cyan}🔐 Procesando:{reset} {input_file}")

    # Paso 1: Intentar encontrar un ejecutable de 'libray' en el PATH.
    libray_command = shutil.which("libray")

    # Paso 2: Si no se encuentra el ejecutable, buscar y usar el script .py.
    if not libray_command:
        print(
            f"{rojo}[{hora()}] ❌ 'libray' no está en el PATH. Intentando usar el script 'libray.py'.{reset}")

        # Obtener la ruta del intérprete de Python.
        python_exe = sys.executable
        if not python_exe:
            print(
                f"{rojo}[{hora()}] ❌ No se pudo encontrar el intérprete de Python. Saltando procesamiento.{reset}")
            return

        # Ruta dinámica al script de libray.py
        appdata_path = Path.home() / "AppData"
        libray_script_path = None

        for site_package_dir in appdata_path.rglob("site-packages"):
            potential_script = site_package_dir / "libray" / "libray.py"
            if potential_script.exists():
                 libray_script_path = potential_script
                 break
             
        if not libray_script_path:
            print(f"{rojo}[{hora()}] ❌ No se encontró el script 'libray.py' en ninguna carpeta 'site-packages'.{reset}")
            return
        else:
            print(f"{verde}[{hora()}] ✅ Se encontró el script 'libray.py'. Iniciando procesamiento...{reset}")        
        
        # Construir el comando para llamar al script de Python directamente.
        libray_command = [python_exe, str(libray_script_path)]
    else:
        # Si se encontró el ejecutable, el comando es solo la ruta.
        libray_command = [libray_command]

    try:
        import subprocess
        with open(log_file, 'w', encoding='utf-8') as lf:
            proc = subprocess.run(
                libray_command + ['-i', str(input_file), '-o', str(output_file)],
                stdout=lf, stderr=subprocess.STDOUT, check=False
            )

        if proc.returncode == 0 and output_file.exists():
            print(f"{rojo}[{hora()}] {verde}✅ Procesado correctamente:{reset} {output_file}")
            print(f"{rojo}[{hora()}] {cyan}🗑️ Eliminando archivo original:{reset} {input_file}")
            try:
                input_file.unlink(missing_ok=True)
            except Exception:
                pass
            print(f"{rojo}[{hora()}] {cyan}🧹 Eliminando log:{reset} {log_file}")
            try:
                log_file.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                if item_dir.exists() and not any(item_dir.iterdir()):
                    item_dir.rmdir()
                    print(f"🧼 Carpeta vacía detectada, eliminando: {item_dir}")
            except Exception:
                pass
        else:
            print(f"{rojo}[{hora()}] ❌ Error procesando {input_file}. Revisa '{log_file}'.{reset}")
    except Exception as e:
        with open(log_file, 'a', encoding='utf-8') as lf:
            lf.write(f"Excepción: {e}\n")
        print(f"{rojo}[{hora()}] ❌ Error procesando {input_file}. Revisa '{log_file}'.{reset}")
        
def descargar_desde_ia() -> None:
    # Cache de items
    use_cache = False
    if CACHE_FILE.exists():
        resp = input("¿Usar lista de ítems almacenada? (s/n): ").strip().lower()
        use_cache = not (resp == 'n')
    if not use_cache:
        if not actualizar_cache_items():
            return
    # Carga lista de items
    item_list = [line.strip() for line in CACHE_FILE.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not item_list:
        print(f"{rojo}[{hora()}]❌ No se encontraron ítems.{reset}")
        return
    idx = elegir_uno(item_list, "Selecciona un ítem")
    if idx < 0:
        print(f"{rojo}[{hora()}]❌ No se seleccionó ningún ítem. Saliendo.{reset}")
        return
    selected_item = item_list[idx]
    print(f"{rojo}[{hora()}] {cyan}✅ Ítem seleccionado:{reset} {selected_item}")

    # Cache de archivos del item
    item_files_cache = IA_PS3_DIR / f"{selected_item}_files_cache.txt"

    def actualizar_cache_files() -> bool:
        print(f"{rojo}[{hora()}] {cyan}🔄 Actualizando lista de archivos para{reset} '{selected_item}'...")
        try:
            item = ia.get_item(selected_item)
            # Crear lista de nombres de archivo visibles
            names = [f.get('name') for f in item.files if f.get('name')]
            names = [n for n in names if n.strip()]
            if not names:
                print(f"{rojo}[{hora()}]❌ Error: no se pudo actualizar la lista de archivos o está vacía.{reset}")
                return False
            item_files_cache.write_text("\n".join(names), encoding='utf-8')
            print(f"{rojo}[{hora()}] {verde}✅ Lista de archivos actualizada y guardada en{reset} {item_files_cache}")
            return True
        except Exception as e:
            print(f"{rojo}[{hora()}]❌ Error listando archivos: {e}{reset}")
            return False

    use_files_cache = False
    if item_files_cache.exists():
        resp = input(f"¿Usar lista de archivos almacenada para '{selected_item}'? (s/n): ").strip().lower()
        use_files_cache = not (resp == 'n')
    if not use_files_cache:
        if not actualizar_cache_files():
            return

    file_list = [line.strip() for line in item_files_cache.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not file_list:
        print(f"{rojo}[{hora()}]❌ No se encontraron archivos.{reset}")
        return

    sel_idxs = elegir_multi(file_list, "Selecciona archivos a descargar")
    if not sel_idxs:
        print(f"{rojo}[{hora()}] ❌ No se seleccionaron archivos válidos.{reset}")
        return

    selected_files = [file_list[i] for i in sel_idxs]
    print(f"\n{rojo}[{hora()}] {cyan}📂 Archivos seleccionados para descarga:{reset}")
    for s in selected_files:
        print(f"  - {s}")
    print()

    dest_path = input("Introduce la carpeta de destino para las iso una vez procesadas se borran: ").strip()
    final_dest_path = input("Introduce la carpeta de destino final para iso desencriptadas: ").strip()
    dest_dir = Path(dest_path).expanduser().resolve()
    final_dir = Path(final_dest_path).expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    print("\n🔁 Iniciando proceso encadenado (Descarga y Procesamiento)...")

    for fname in selected_files:
        print(f"{rojo}[{hora()}] {cyan}📥 Iniciando descarga de: {reset}{fname}")
        ok = descargar_archivo(selected_item, fname, dest_dir)
        # Ruta esperada de descarga: dest_dir / selected_item / fname
        pending_input = dest_dir / selected_item / fname
        sanitized = sanitize_filename(fname)
        pending_output = final_dir / f"{sanitized}.decrypted.iso"
        if ok and pending_input.exists():
            # Procesamiento secuencial (una a la vez) para emular la cola del original
            procesar_archivo_con_libray(pending_input, pending_output)

    print(f"{verde}[{hora()}] ✅ Todos los archivos han sido descargados y procesados con éxito. {reset}")


# --- Lado PKG ---

def parse_pkg_txt(file_path: Path) -> List[Tuple[str, str]]:
    """Cada bloque está separado por una línea en blanco. 1ª línea = nombre, 2ª = URL.
       Se devuelve lista de pares (nombre_limpio, url)."""
    text = file_path.read_text(encoding='utf-8', errors='ignore')
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    entries: List[Tuple[str, str]] = []
    for block in raw_blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) >= 2:
            name, url = lines[0], lines[1]
            # Limpieza del nombre: elimina sufijos " - (BCES|BLES)xxxxx..."
            name_clean = re.sub(r" - (BCES|BLES)\d{5}.*", "", name)
            entries.append((name_clean, url))
    return entries


def seleccionar_pkg_desde_txt(files: List[Path]) -> List[Tuple[str, str]]:
    print(f"{cyan}🔍 Buscando ficheros .txt en {PKG_DIR}{reset}")
    if not files:
        print(f"{rojo}❌ No se encontraron ficheros .txt en {PKG_DIR}{reset}")
        return []
    print(f"\n{verde}📂 Ficheros encontrados:{reset}")
    for p in files:
        print(f"  - {p}")

    # Permitir seleccionar múltiples por índice
    opciones = [str(p) for p in files]
    sel = elegir_multi(opciones, "Selecciona uno o varios archivos PKG")
    if not sel:
        print(f"{rojo}❌ No seleccionaste ningún archivo.{reset}")
        return []

    temp_entries: List[Tuple[str, str]] = []
    for i in sel:
        temp_entries.extend(parse_pkg_txt(files[i]))

    if not temp_entries:
        print("No se encontraron entradas válidas en los ficheros seleccionados.")
        return []

    # Mapa nombre->url (puede haber duplicados)
    names = [e[0] for e in temp_entries]
    idxs = elegir_multi(names, "Selecciona juegos PKG")
    if not idxs:
        print("No se seleccionó ningún juego.")
        return []

    return [temp_entries[i] for i in idxs]


def descargar_pkg(url: str, destino: Path) -> bool:
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n{rojo}[{hora()}] {cyan}📥 Descargando:{reset} {destino.name}")
    print(f"{rojo}[{hora()}] {cyan}🔗 URL:{reset} {url}")
    print(f"{rojo}[{hora()}] {cyan}📁 Destino:{reset} {destino}\n")
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(destino, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        print(f"\n{verde}[{hora()}] ✅ Descarga completada: {destino}{reset}")
        return True
    except Exception as e:
        print(f"\n{rojo}[{hora()}] ❌ Error en la descarga: {e}{reset}")
        return False


def descargar_desde_pkg() -> None:
    # Buscar .txt en ~/.iaPS3/pkg
    txt_files = sorted([p for p in PKG_DIR.rglob('*.txt') if p.is_file()])
    seleccion = seleccionar_pkg_desde_txt(txt_files)
    if not seleccion:
        return

    dest_dir_in = input("Introduce el directorio de destino (deja vacío para el actual): ").strip()
    dest_dir = Path(dest_dir_in or ".").expanduser().resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    for name, url in seleccion:
        nombre_archivo = os.path.basename(url)
        destino = dest_dir / nombre_archivo
        descargar_pkg(url, destino)

# --- Main loop ---

def main() -> None:
    while RUNNING:
        mostrar_menu_principal()
        opcion = input("Elige una opción (1-4): ").strip()
        if opcion == '1':
            descargar_desde_ia()
        elif opcion == '2':
            descargar_desde_pkg()
        elif opcion == '3':
            configurar_cuenta_ia()
        elif opcion == '4':
            finalizar()
        else:
            print(f"{rojo}Opción no válida. Inténtalo de nuevo.{reset}")
            time.sleep(1)
        press_enter()

if __name__ == "__main__":
    main()
