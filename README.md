# 👾 Descargador y Procesador de Juegos de PS3 desde Archive.org

Este script en Bash automatiza la búsqueda, descarga y desencriptado de juegos de PlayStation 3 alojados en [Archive.org](https://archive.org).  
Ideal para usuarios que quieren montar su propia biblioteca de backups en formato `.ISO` desencriptado.

> ⚠️ **Uso educativo / backup legal únicamente. No fomentes la piratería.**

---

## 📌 ¿Qué hace?

1. Busca automáticamente juegos de PS3 disponibles en Archive.org.
2. Permite seleccionar los juegos y archivos específicos mediante un menú interactivo.
3. Descarga los archivos seleccionados.
4. Usa `libray` para desencriptar automáticamente los juegos.
5. Mueve los archivos procesados a un directorio final listo para su uso.

---

## ⚙️ ¿Cómo funciona?

1. **Consulta inicial:**  
   Se descarga una lista de juegos disponibles usando el CLI de `ia`.

2. **Interfaz de selección:**  
   Usa `fzf` para que el usuario elija juegos y archivos específicos a descargar.

3. **Descarga + desencriptado:**  
   Cada archivo se descarga y se procesa uno a uno (o en paralelo moderado) usando `libray`.

4. **Logs y limpieza:**  
   Se crean logs de cada operación y se eliminan archivos temporales/librerías vacías al finalizar.

---

## 📦 Dependencias necesarias

Este script requiere los siguientes programas instalados en tu sistema:

- [`ia`](https://pypi.org/project/internetarchive/) – para interactuar con Archive.org
- [`fzf`](https://github.com/junegunn/fzf) – selector interactivo en terminal
- [`jq`](https://stedolan.github.io/jq/) – parser JSON para línea de comandos
- [`libray`](https://github.com/firstatack/libray) – herramienta para desencriptar backups de PS3 (debes compilarla o usar binario disponible)

Puedes instalar todo ejecutando el script `install_deps.sh` incluido en este repositorio.

**Nota**, puede ocurrir que en alguna distribucion como ubuntu corriendo en docker la instalacion de libray de haga en un carpeta fuera del **PATH** y eso haga que falle el script , solo añadid la nueva ruta al path. 

Ejemplo :

```bash
'export PATH="$HOME/.local/share/pipx/venvs/libray/bin:$PATH"
```

---

## 🚀 ¿Cómo usarlo?

Una vez tengamos la herramienta de python de ia nos tocara configurarla para ello ejeuctamos:

```bash
ia configure # esto nos da un promt para introducir el usario y la contraseña de internet archive
```
Con todo instalado solo que modificar alrededor de la linea 121 el parametro donde quieras que se guarden los ficheros procesados de libray.

```bash
FINAL_DEST_PATH="/you/path/here" #Modificar a la ruta deseada
```

```bash
chmod +x descargar_ps3.sh
./descargar_ps3.sh
```

## Resumen de instalacion

1. -Ejecutar install_deps.sh
2. -Ejecutar **ia configure**
3. -Comprobar si libray esta en el PATH (si esta ejecutar ps3_downloader.sh y si no agregalo al PATH)

## 🙏 Créditos

Script creado por firstatack.

Inspirado en la necesidad de que los originales se rallan y no andan.

## ⚠️ Aviso legal
Este script está destinado únicamente para propósitos educativos o de respaldo personal. No fomenta el uso ilegal de software.
Asegúrate de tener los derechos sobre los juegos que descargues o uses.
