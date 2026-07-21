#!/bin/bash
set -e

script_name=$(basename "${BASH_SOURCE[0]}")
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "$script_name: detected OS=$OS ARCH=$ARCH"

if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "$script_name: WARNING - no venv appears to be active."
    echo "$script_name: run 'source .venv/bin/activate' first, or this build"
    echo "$script_name: may use the wrong python/PyQt5 (or none at all)."
    read -p "$script_name: continue anyway? [y/N] " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo "$script_name: aborting."
        exit 1
    fi
fi

echo "$script_name: building via spec file"
pyinstaller --noconfirm APacKsplorer.spec

if [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        OUT_NAME="APacKsplorer-arm64"
    elif [[ "$ARCH" == "x86_64" ]]; then
        OUT_NAME="APacKsplorer-x86_64"
    else
        echo "$script_name: unrecognized macOS arch '$ARCH', bailing"
        exit 1
    fi

    # NOTE: still no universal2 - PyQt5 ships arch-specific wheels only,
    # same reasoning as before, just now enforced by whichever venv/python
    # ran pyinstaller rather than a --target-arch flag.
    if [[ -d "dist/APacKsplorer.app" && "$OUT_NAME" != "APacKsplorer" ]]; then
        rm -rf "dist/${OUT_NAME}.app"
        mv "dist/APacKsplorer.app" "dist/${OUT_NAME}.app"
        echo "$script_name: output at dist/${OUT_NAME}.app"
    fi

elif [[ "$OS" == "Linux" ]]; then
    if [[ "$ARCH" != "x86_64" ]]; then
        echo "$script_name: unsupported Linux arch '$ARCH' (x86_64 only for now)"
        exit 1
    fi
    echo "$script_name: output at dist/APacKsplorer/ (Linux .deb packaging: TODO)"

elif [[ "$OS" == "Windows_NT" || "$OS" =~ ^MINGW ]]; then
    echo "$script_name: output at dist/APacKsplorer/"

else
    echo "$script_name: unsupported OS '$OS'"
    exit 1
fi

echo "$script_name: done."