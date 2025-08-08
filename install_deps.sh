#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "🔍 Detectando distribución de Linux..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=${ID,,}
    # Normalizar distros derivadas
    case "$DISTRO" in
        pop|popos)
            DISTRO="ubuntu"
            ;;
        rocky|almalinux)
            DISTRO="fedora"
            ;;
    esac
else
    echo "❌ No se detectó la distro."
    exit 1
fi

echo "✅ Distro detectada: $DISTRO"

# Dependencias del sistema
DEPS=(fzf jq internetarchive pipx)
MISSING=()

for pkg in "${DEPS[@]}"; do
    if ! command -v "$pkg" &>/dev/null; then
        MISSING+=( "$pkg" )
    else
        echo "✅ Instalado: $pkg"
    fi
done

install_pkgs(){
    case "$DISTRO" in
        debian|ubuntu)
            sudo apt update
            sudo apt install -y python3-pip python3-venv "${@}"
            ;;
        fedora)
            sudo dnf install -y python3-pip python3-virtualenv "${@}"
            ;;
        arch|manjaro)
            sudo pacman -Sy --noconfirm "${@}"
            ;;
        *)
            echo "❌ No se soporta la instalación automática para esta distro: $DISTRO"
            echo "➡️ Instala manualmente los paquetes: ${*}"
            exit 1
            ;;
    esac
}

if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "🚀 Instalando paquete(s) faltantes: ${MISSING[*]}"
    install_pkgs "${MISSING[@]}"
fi

# Añadir ~/.local/bin al PATH temporal si es necesario
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚙️ Añadiendo ~/.local/bin a PATH para esta sesión..."
    export PATH="$HOME/.local/bin:$PATH"
    echo "ℹ️ Recuerda añadir esto a tu ~/.bashrc o ~/.zshrc si deseas que sea permanente:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "📦 Comprobando libray..."

if ! command -v libray &>/dev/null; then
    case "$DISTRO" in
        debian|ubuntu|fedora)
            echo "🚀 Instalando libray con pipx..."
            pipx install libray || pipx upgrade libray
            ;;
        arch|manjaro)
            if command -v yay &>/dev/null; then
                echo "🛠 Instalando libray desde AUR con yay..."
                yay -S --noconfirm libray
            else
                echo "⚠️ Necesitas yay para instalar libray desde AUR."
                echo "➡️ Puedes instalar yay siguiendo esta guía: https://wiki.archlinux.org/title/AUR_helpers"
                exit 1
            fi
            ;;
        *)
            echo "❌ Libray no soportado automáticamente en esta distro."
            echo "➡️ Puedes intentar instalarlo manualmente con pipx:"
            echo "pipx install libray"
            ;;
    esac
else
    echo "✅ libray ya está instalado"
fi

echo ""
echo "🎉 Todas las dependencias han sido instaladas o verificadas correctamente."
