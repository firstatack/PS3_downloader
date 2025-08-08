#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

echo "🔍 Detectando distribución de Linux..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=${ID,,}
else
    echo "❌ No se detectó la distro."
    exit 1
fi

echo "✅ Distro: $DISTRO"

DEPS=(fzf jq internetarchive)
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
            sudo apt install -y "$@"
            ;;
        fedora)
            sudo dnf install -y "$@"
            ;;
        arch|manjaro)
            sudo pacman -Sy --noconfirm "$@"
            ;;
        *)
            echo "❌ No automáticamente soportado: $DISTRO"
            echo "➡️ Instalar manual: $*"
            exit 1
            ;;
    esac
}

if [ "${#MISSING[@]}" -gt 0 ]; then
    echo "🚀 Instalando paquete(s): ${MISSING[*]}"
    install_pkgs "${MISSING[@]}"
fi

echo ""
echo "📦 Comprobando libray..."

if ! command -v libray &>/dev/null; then
    case "$DISTRO" in
        debian|ubuntu)
            echo "🚀 Instalando pipx y libray con pipx..."
            sudo apt update
            sudo apt install -y pipx python3-venv
            # Añadir ~/.local/bin al PATH temporalmente si no está
            if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
                echo "⚙️ Añadiendo ~/.local/bin a PATH temporalmente para esta sesión..."
                export PATH="$HOME/.local/bin:$PATH"
            fi

            echo "🛠 Instalando libray con pipx..."
            pipx install libray || pipx upgrade libray

            echo "✅ libray instalado con pipx. Recuerda que ~/.local/bin debe estar en tu PATH."
            ;;
        fedora)
            echo "🚀 Instalando pipx y libray con pipx..."
            sudo dnf install -y python3-pip python3-virtualenv
            if ! command -v pipx &>/dev/null; then
                echo "⚙️ Instalando pipx con pip..."
                python3 -m pip install --user pipx
                python3 -m pipx ensurepath
            fi
            if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
                echo "⚙️ Añadiendo ~/.local/bin a PATH temporalmente para esta sesión..."
                export PATH="$HOME/.local/bin:$PATH"
            fi

            echo "🛠 Instalando libray con pipx..."
            pipx install libray || pipx upgrade libray

            echo "✅ libray instalado con pipx. Recuerda que ~/.local/bin debe estar en tu PATH."
            ;;
        arch|manjaro)
            if command -v yay &>/dev/null; then
                echo "🛠 Instalando libray desde AUR (yay)…"
                yay -S --noconfirm libray
            else
                echo "⚠️ Necesitas yay para instalar libray desde AUR."
            fi
            ;;
        *)
            echo "❌ Libray no soportado automáticamente en esta distro."
            ;;
    esac
else
    echo "✅ libray ya está instalado"
fi

echo ""
echo "🎉 Comprobación e instalación completadas."
