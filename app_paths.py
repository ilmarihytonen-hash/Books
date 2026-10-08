"""Resolve bundled resources and writable files in source and frozen builds."""

import os
import shutil
import sys


def application_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def local_appdata_dir():
    base_dir = os.environ.get("LOCALAPPDATA")
    if not base_dir:
        base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return base_dir


def user_data_dir():
    if sys.platform == "win32" and getattr(sys, "frozen", False):
        return os.path.join(local_appdata_dir(), "Bookapp")
    return application_dir()


def resource_path(filename):
    bundle_dir = getattr(sys, "_MEIPASS", application_dir())
    return os.path.join(bundle_dir, filename)


def writable_path(filename):
    return os.path.join(user_data_dir(), filename)


def migrate_legacy_file(filename):
    """Copy existing files into the user data folder on first run."""
    destination = writable_path(filename)
    if os.path.exists(destination):
        return
    legacy_dirs = [application_dir()]
    if sys.platform == "win32" and getattr(sys, "frozen", False):
        legacy_dirs.append(
            os.path.join(local_appdata_dir(), "Programs", "Bookapp")
        )
    for legacy_dir in legacy_dirs:
        source = os.path.join(legacy_dir, filename)
        if os.path.abspath(source) == os.path.abspath(destination):
            continue
        if os.path.isfile(source):
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source, destination)
            return
