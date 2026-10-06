"""Resolve bundled resources and writable files in source and frozen builds."""

import os
import sys


def application_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(filename):
    bundle_dir = getattr(sys, "_MEIPASS", application_dir())
    return os.path.join(bundle_dir, filename)


def writable_path(filename):
    return os.path.join(application_dir(), filename)
