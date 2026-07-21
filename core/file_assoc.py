import os
import sys
import platform
import subprocess

system = platform.system()


class AssocError(Exception):
    pass


def _get_exe_path():
    if getattr(sys, "frozen", False):
        return sys.executable
    raise AssocError(
        "not running as a frozen build - refusing to register the current "
        "python interpreter as the .apk handler. build the app first."
    )


def associate_apk_windows(icon_path=None):
    import winreg

    exe_path = _get_exe_path()
    prog_id = "APacKsplorer.apk"

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, "APK Package File")

    icon_value = icon_path if icon_path else f"{exe_path},0"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\DefaultIcon") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, icon_value)

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Classes\{prog_id}\shell\open\command") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, f'"{exe_path}" "%1"')

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.apk") as key:
        winreg.SetValue(key, "", winreg.REG_SZ, prog_id)

    import ctypes
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)


def associate_apk_linux(icon_path=None):
    exe_path = _get_exe_path()
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_file = os.path.join(desktop_dir, "apacksplorer.desktop")

    with open(desktop_file, "w") as f:
        f.write(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=APacKsplorer\n"
            f"Exec={exe_path} %f\n"
            f"Icon={icon_path or 'apacksplorer'}\n"
            "MimeType=application/vnd.android.package-archive;\n"
            "Terminal=false\n"
        )

    subprocess.run(["update-desktop-database", desktop_dir], check=False)
    subprocess.run(["xdg-mime", "default", "apacksplorer.desktop", "application/vnd.android.package-archive"], check=False)


def associate_apk(icon_path=None):
    if system == "Windows":
        associate_apk_windows(icon_path)
    elif system == "Linux":
        associate_apk_linux(icon_path)
    elif system == "Darwin":
        raise AssocError("handled automatically via app bundle Info.plist - no action needed")
    else:
        raise AssocError(f"unsupported platform: {system}")