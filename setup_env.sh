#!/bin/bash
set -e

script_name=$(basename "${BASH_SOURCE[0]}")
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "$script_name: detected OS=$OS ARCH=$ARCH"

# ---- pick the right python interpreter for this machine ----
# each machine in this project builds for its own native arch only.
# no cross-arch venv juggling here - that lives in produce.sh instead,
# by way of running this script separately on each physical machine.

PYTHON_BIN=""

if [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        echo "$script_name: macOS arm64 (Apple Silicon)"
        # python.org universal2 pkg install
        if [[ -x "/usr/local/bin/python3.8" ]]; then
            PYTHON_BIN="/usr/local/bin/python3.8"
        elif command -v python3.8 >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v python3.8)"
        fi

    elif [[ "$ARCH" == "x86_64" ]]; then
        echo "$script_name: macOS x86_64 (Intel)"
        # MacPorts install (Mojave has no modern Homebrew/pyenv support)
        if [[ -x "/opt/local/bin/python3.8" ]]; then
            PYTHON_BIN="/opt/local/bin/python3.8"
        elif command -v python3.8 >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v python3.8)"
        fi

    else
        echo "$script_name: unrecognized macOS arch '$ARCH', bailing"
        exit 1
    fi

elif [[ "$OS" == "Linux" ]]; then
    if [[ "$ARCH" == "x86_64" ]]; then
        echo "$script_name: Linux x86_64"
        if command -v python3.8 >/dev/null 2>&1; then
            PYTHON_BIN="$(command -v python3.8)"
        fi
    else
        echo "$script_name: unsupported Linux arch '$ARCH' (this project targets x86_64 only for now)"
        exit 1
    fi

else
    echo "$script_name: unsupported OS '$OS'"
    exit 1
fi

if [[ -z "$PYTHON_BIN" ]]; then
    echo "$script_name: could not find a python3.8 interpreter on this machine."
    echo "$script_name: macOS arm64  -> install via python.org's universal2 pkg"
    echo "$script_name: macOS x86_64 -> install via MacPorts (port install python38)"
    echo "$script_name: Linux        -> install via your distro's package manager / pyenv"
    exit 1
fi

echo "$script_name: using interpreter at $PYTHON_BIN"
"$PYTHON_BIN" --version

# ---- venv setup ----
VENV_DIR=".venv"

echo "$script_name: creating venv at $VENV_DIR"
"$PYTHON_BIN" -m venv "$VENV_DIR"

if [[ "$(arch)" == "arm64" ]]; then 
    echo "$script_name: arm64ing venv"
else
    echo "$script_name: activating venv"
fi

source "$VENV_DIR/bin/activate"

echo "$script_name: upgrading pip"
pip install --upgrade pip

echo "$script_name: installing dependencies (no-cache, avoids stale cross-arch wheel reuse)"
pip install --no-cache-dir -r requirements.txt

echo "$script_name: done. run 'source $VENV_DIR/bin/activate' to activate this venv in future shells."