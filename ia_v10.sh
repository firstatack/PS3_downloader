#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# Configuramos los colores (ANSI)
rojo='\e[1;31m'
sincolor='\e[0m'
cyan='\e[1;36m'
verde='\e[1;32m'

printf "\n"
printf "${rojo}====================================================\n"
printf "  ${cyan}👾 Descargador y Procesador en Cola de PS3 👾${sincolor}\n"
printf "${rojo}====================================================\n"
printf "\n"
printf "  ${verde}➜ ¡Bienvenido! Este script te ayudará a descargar${sincolor}\n"
printf "  ${verde}  y desencriptar juegos de PS3 de Archive.org.${sincolor}\n"
printf "\n"
printf "${cyan}====================================================\n"
printf "${rojo}		De firstatack para gamers con problemas ${sincolor}\n"
printf "${cyan}====================================================\n${sincolor}"

# Directorios para cache y logs
IA_PS3_DIR="$HOME/.iaPS3"
LOGS_DIR="$IA_PS3_DIR/logs"
mkdir -p "$IA_PS3_DIR" "$LOGS_DIR"

CACHE_FILE="$IA_PS3_DIR/ps3_items_cache.txt"

#Comprobamos si tiene las dependencias
for cmd in ia fzf jq libray; do
    command -v "$cmd" >/dev/null || {
        printf "${rojo}❌ El comando '$cmd' no está instalado. Abortando.${sincolor}\n"
        printf "${cyan} Usa el script que acompaña para instalar las dependencias..${sincolor}\n"
        exit 1
    }
done

hora() {
    date +%H:%M:%S
}

finalizar() {
    printf "${rojo} \n\n Finalizando el script${sincolor}\n"
    exit
}

trap finalizar SIGINT

actualizar_cache_items() {
    printf "${rojo}[$(hora)]${cyan} 🔄 Actualizando lista de ítems desde archive.org...${sincolor}\n"
    if ia search sony_playstation3 2>/dev/null | grep "sony_playstation3_" | sort -u | jq -r '.identifier' > "$CACHE_FILE"; then
        printf "${rojo}[$(hora)]${verde}✅ Lista actualizada y guardada en $CACHE_FILE${sincolor}\n"
    else
        printf "${rojo}[$(hora)]❌ Error: no se pudo actualizar la lista o está vacía.${sincolor}\n"
        return 1
    fi
}

if [[ -f "$CACHE_FILE" ]]; then
    read -rp "¿Usar lista de ítems almacenada? (s/n): " RESP_ITEMS
    [[ "$RESP_ITEMS" =~ ^[Nn]$ ]] && actualizar_cache_items || printf "Usando lista almacenada en $CACHE_FILE\n"
else
    actualizar_cache_items
fi

readarray -t ITEM_LIST < "$CACHE_FILE"

if [[ ${#ITEM_LIST[@]} -eq 0 ]]; then
    printf "${rojo}[$(hora)]❌ No se encontraron ítems.${sincolor}\n"
    exit 1
fi

SELECTED_ITEM=$(printf '%s\n' "${ITEM_LIST[@]}" | fzf --prompt="Selecciona un ítem: ")
if [[ -z "$SELECTED_ITEM" ]]; then
    printf "${rojo}[$(hora)]❌ No se seleccionó ningún ítem. Saliendo.${sincolor}\n"
    exit 1
fi
printf "${rojo}[$(hora)] ${cyan}✅ Ítem seleccionado:${sincolor} $SELECTED_ITEM\n"

ITEM_FILES_CACHE="$IA_PS3_DIR/${SELECTED_ITEM}_files_cache.txt"

actualizar_cache_files() {
    printf "${rojo}[$(hora)] ${cyan}🔄 Actualizando lista de archivos para${sincolor} '$SELECTED_ITEM'...\n"
    if ia list "$SELECTED_ITEM" | sed '/^\s*$/d' > "$ITEM_FILES_CACHE"; then
        printf "${rojo}[$(hora)] ${verde}✅ Lista de archivos actualizada y guardada en${sincolor} $ITEM_FILES_CACHE\n"
    else
        printf "${rojo}[$(hora)]❌ Error: no se pudo actualizar la lista de archivos o está vacía.${sincolor}\n"
        exit 1
    fi
}

if [[ -f "$ITEM_FILES_CACHE" ]]; then
    read -rp "¿Usar lista de archivos almacenada para '$SELECTED_ITEM'? (s/n): " RESP_FILES
    [[ "$RESP_FILES" =~ ^[Nn]$ ]] && actualizar_cache_files || printf "Usando lista almacenada en $ITEM_FILES_CACHE\n"
else
    actualizar_cache_files
fi

mapfile -t FILE_LIST < "$ITEM_FILES_CACHE"

if [[ ${#FILE_LIST[@]} -eq 0 ]]; then
    printf "${rojo}[$(hora)]❌ No se encontraron archivos.${sincolor}\n"
    exit 1
fi

mapfile -t SELECTED_FILES < <(printf '%s\n' "${FILE_LIST[@]}" | fzf --multi --prompt="Selecciona archivos a descargar: ")

if [[ ${#SELECTED_FILES[@]} -eq 0 ]]; then
    printf "${rojo}[$(hora)] ❌ No se seleccionaron archivos válidos.${sincolor}\n"
    exit 1
fi

printf "\n${rojo}[$(hora)] ${cyan}📂 Archivos seleccionados para descarga:${sincolor}\n"
printf '  - %s\n' "${SELECTED_FILES[@]}"
printf "\n"

read -rp "Introduce la carpeta de destino para las descargas (temporal): " DEST_PATH
mkdir -p "$DEST_PATH"

FINAL_DEST_PATH="/home/firstatack/games" #Modificar a la ruta deseada
mkdir -p "$FINAL_DEST_PATH"

printf "\n🔁 Iniciando proceso encadenado (Descarga y Procesamiento)...\n"

descargar_archivo() {
    local item="$1"
    local file="$2"
    local dest="$3"
    local log_file="$LOGS_DIR/download_${file//[^a-zA-Z0-9]/_}.log"
    printf "${rojo}[$(hora)] ${cyan}📥 Descargando: ${sincolor} $file...\n"
    if ia download "$item" --glob "$file" --destdir "$dest" > "$log_file" 2>&1; then
        printf "${rojo}[$(hora)] ${verde}✅ Descarga completa:${sincolor} $file\n"
        return 0
    else
        printf "${rojo}[$(hora)] ❌ Error descargando $file. Revisa '$log_file'.${sincolor}\n"
        return 1
    fi
}

procesar_archivo() {
    local input_file="$1"
    local output_file="$2"
    local log_file="$LOGS_DIR/libray_$(basename "${input_file//[^a-zA-Z0-9]/_}").log"
    local item_dir
    item_dir=$(dirname "$input_file")
    
    while pgrep -x "libray" > /dev/null; do
        printf "${rojo}[$(hora)] ⏳ Esperando a que termine un proceso de 'libray' antes de iniciar el siguiente...${sincolor}\n"
        sleep 300
    done

    printf "${rojo}[$(hora)] ${cyan}🔐 Procesando:${sincolor} $input_file\n"
    if libray -i "$input_file" -o "$output_file" > "$log_file" 2>&1; then
        printf "${rojo}[$(hora)] ${verde}✅ Procesado correctamente: $output_file ${sincolor}\n"
        printf "${rojo}[$(hora)] ${cyan}🗑️ Eliminando archivo original:${sincolor} $input_file\n"
        rm -f "$input_file"
        printf "${rojo}[$(hora)] ${cyan}🧹 Eliminando log: $log_file ${sincolor}\n"
        rm -f "$log_file"
        [[ -d "$item_dir" && -z "$(ls -A "$item_dir")" ]] && rmdir "$item_dir" && printf "🧼 Carpeta vacía detectada, eliminando: $item_dir\n"
    else
        printf "${rojo}[$(hora)] ❌ Error procesando $input_file. Revisa '$log_file'.${sincolor}\n"
    fi
}

for FILE_NAME in "${SELECTED_FILES[@]}"; do
    printf "${rojo}[$(hora)] ${cyan}📥 Iniciando descarga de: ${sincolor} $FILE_NAME\n"
    descargar_archivo "$SELECTED_ITEM" "$FILE_NAME" "$DEST_PATH"

    PENDING_INPUT_FILE="$DEST_PATH/$(basename "$SELECTED_ITEM")/$FILE_NAME"
    PENDING_OUTPUT_FILE="$FINAL_DEST_PATH/$(echo "$FILE_NAME" | sed 's/[[:space:]]/_/g' | sed "s/'//g" | sed 's/\"//g' | sed 's/[^a-zA-Z0-9._-]//g').decrypted.iso"

    if [[ -n "$PENDING_INPUT_FILE" ]]; then
        procesar_archivo "$PENDING_INPUT_FILE" "$PENDING_OUTPUT_FILE" &
    fi
done

printf "${rojo}[$(hora)] ${verde}📥 Iniciando descarga del siguiente archivo... ${sincolor}\n"
wait

printf "${verde}[$(hora)] ✅ Todos los archivos han sido descargados y procesados con éxito. ${sincolor}\n"
