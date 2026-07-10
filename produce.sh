#!/bin/bash
set -e

script_name=$(basename "${BASH_SOURCE[0]}")
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "$script_name: detected OS=$OS ARCH=$ARCH"

# sanity check: warn if no venv is active, since this has bitten us before
# (pyinstaller silently falling back to a system python with none of our
# pinned deps installed, e.g. missing PyQt5 entirely)
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

COMMON_ARGS=(
    --windowed
    --onedir
    --name APacKsplorer
    --add-data "tools:tools"
    --add-data "ui:ui"
    --noconfirm
    ./gui/main_window.py
)

if [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        OUT_NAME="APacKsplorer-arm64"
    elif [[ "$ARCH" == "x86_64" ]]; then
        OUT_NAME="APacKsplorer-x86_64"
    else
        echo "$script_name: unrecognized macOS arch '$ARCH', bailing"
        exit 1
    fi

    echo "$script_name: building macOS .app ($OUT_NAME)"
    # NOTE: no --target-arch universal2 here - PyQt5 does not ship a
    # universal2 wheel (confirmed: separate arm64 / x86_64 wheels only),
    # so a "universal2" PyInstaller build just wraps a single-arch PyQt5
    # in a fat launcher stub, which is broken. build native per-arch instead.
    pyinstaller \
        --icon assets/APacKsplorer.icns \
        --add-data "assets:assets" \
        "${COMMON_ARGS[@]}"

    # rename the produced .app so arm64/x86_64 builds don't clobber each other
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

    echo "$script_name: building Linux onedir build"
    pyinstaller \
        --add-data "assets:assets" \
        "${COMMON_ARGS[@]}"

    echo "$script_name: output at dist/APacKsplorer/ (Linux .deb packaging: TODO)"

else
    echo "$script_name: unsupported OS '$OS'"
    exit 1
fi

echo "$script_name: done."

# xtra flags for reference: --debug=all