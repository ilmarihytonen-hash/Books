"""Store website logins encrypted for the current Windows user."""

import ctypes
import json
import os
import sys
from ctypes import wintypes
from urllib.parse import urlsplit

from app_paths import migrate_legacy_file, writable_path

FILENAME = writable_path("logins.dat")
_MAGIC = b"BOOKAPP-DPAPI-1\n"
_CRYPTPROTECT_UI_FORBIDDEN = 0x1


def password_saving_enabled():
    from configreader import load_config

    return load_config().get("password_saving_enabled", True) is True


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte)),
    ]


def origin_for_url(url):
    try:
        parsed = urlsplit(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("The current website address is invalid") from error

    if (
        parsed.scheme.lower() != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("Saved logins are available only on HTTPS websites")

    hostname = hostname.encode("idna").decode("ascii").lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    port_suffix = f":{port}" if port and port != 443 else ""
    return f"https://{hostname}{port_suffix}"


def _dpapi(data, protect):
    if sys.platform != "win32":
        raise OSError("Windows account protection is available only on Windows")

    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p

    source_buffer = ctypes.create_string_buffer(data)
    source = _DataBlob(
        len(data),
        ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_ubyte)),
    )
    destination = _DataBlob()
    if protect:
        function = crypt32.CryptProtectData
        function.argtypes = [
            ctypes.POINTER(_DataBlob),
            wintypes.LPCWSTR,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]
        function.restype = wintypes.BOOL
        succeeded = function(
            ctypes.byref(source),
            "Bookapp saved website logins",
            None,
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(destination),
        )
    else:
        function = crypt32.CryptUnprotectData
        function.argtypes = [
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.POINTER(_DataBlob),
            ctypes.c_void_p,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(_DataBlob),
        ]
        function.restype = wintypes.BOOL
        succeeded = function(
            ctypes.byref(source),
            None,
            None,
            None,
            None,
            _CRYPTPROTECT_UI_FORBIDDEN,
            ctypes.byref(destination),
        )

    if not succeeded:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(destination.pbData, ctypes.c_void_p))


def _load_logins():
    migrate_legacy_file("logins.dat")
    try:
        with open(FILENAME, "rb") as file:
            encrypted = file.read()
    except FileNotFoundError:
        return {}

    if not encrypted.startswith(_MAGIC):
        raise ValueError("The saved-login file has an unknown format")
    plaintext = _dpapi(encrypted[len(_MAGIC) :], protect=False)
    try:
        logins = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("The saved-login data is invalid") from error
    if not isinstance(logins, dict) or not all(
        isinstance(origin, str)
        and isinstance(login, dict)
        and isinstance(login.get("username"), str)
        and isinstance(login.get("password"), str)
        for origin, login in logins.items()
    ):
        raise ValueError("The saved-login data is invalid")
    return logins


def _save_logins(logins):
    directory = os.path.dirname(FILENAME)
    os.makedirs(directory, exist_ok=True)
    encrypted = _MAGIC + _dpapi(
        json.dumps(logins, ensure_ascii=False).encode("utf-8"), protect=True
    )
    temporary_filename = FILENAME + ".tmp"
    try:
        with open(temporary_filename, "wb") as file:
            file.write(encrypted)
        os.replace(temporary_filename, FILENAME)
    finally:
        if os.path.exists(temporary_filename):
            os.remove(temporary_filename)


def get_login(url):
    if not password_saving_enabled():
        return None
    return _load_logins().get(origin_for_url(url))


def save_login(url, username, password):
    if not password_saving_enabled():
        raise PermissionError("Password saving is disabled in Bookapp settings")
    if not username or not password:
        raise ValueError("Enter both a username and a password")
    logins = _load_logins()
    logins[origin_for_url(url)] = {
        "username": username,
        "password": password,
    }
    _save_logins(logins)


def remove_login(url):
    logins = _load_logins()
    origin = origin_for_url(url)
    if origin not in logins:
        return False
    del logins[origin]
    _save_logins(logins)
    return True


def clear_logins():
    try:
        os.remove(FILENAME)
    except FileNotFoundError:
        return
