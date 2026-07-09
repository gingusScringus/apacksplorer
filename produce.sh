pyinstaller --windowed --onedir --name APacKsplorer --icon assets/APacKsplorer.icns --add-data "assets:assets" --add-data "tools:tools" --add-data "ui:ui" --target-arch universal2  --noconfirm ./gui/main_window.py

# xtra flags: --target-arch universal2 --debug=all
