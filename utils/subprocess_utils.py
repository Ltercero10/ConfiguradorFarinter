# -*- coding: utf-8 -*-
import subprocess


def get_hidden_startupinfo():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def hidden_run(command, **kwargs):
    return subprocess.run(
        command,
        startupinfo=get_hidden_startupinfo(),
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs
    )


def hidden_popen(command, **kwargs):
    return subprocess.Popen(
        command,
        startupinfo=get_hidden_startupinfo(),
        creationflags=subprocess.CREATE_NO_WINDOW,
        **kwargs
    )