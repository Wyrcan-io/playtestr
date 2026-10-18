"""Bounded Windows synthetic console-input diagnostic; zero campaign credit."""
import ctypes
from ctypes import byref,wintypes
import json
import msvcrt
import sys
import time
from pathlib import Path

from textual.drivers import win32


def main():
    kernel=win32.KERNEL32
    handle=win32.GetStdHandle(win32.STD_INPUT_HANDLE)
    stream=msvcrt.get_osfhandle(sys.stdin.fileno())
    print('probe handles',int(handle),int(stream),flush=True)
    mode=wintypes.DWORD()
    kernel.GetConsoleMode.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD)]
    kernel.SetConsoleMode.argtypes=[wintypes.HANDLE,wintypes.DWORD]
    obtained=kernel.GetConsoleMode(handle,byref(mode))
    if not obtained:raise ctypes.WinError(ctypes.get_last_error())
    original=mode.value
    if not kernel.SetConsoleMode(handle,win32.ENABLE_VIRTUAL_TERMINAL_INPUT):raise ctypes.WinError(ctypes.get_last_error())
    try:
        print('console diagnostic ready',flush=True)
        records=(win32.INPUT_RECORD*32)();count=wintypes.DWORD()
        kernel.ReadConsoleInputW.argtypes=[wintypes.HANDLE,ctypes.POINTER(win32.INPUT_RECORD),wintypes.DWORD,ctypes.POINTER(wintypes.DWORD)]
        end=time.monotonic()+8
        while time.monotonic()<end:
            if win32.wait_for_handles([handle],200) is None:continue
            if not kernel.ReadConsoleInputW(handle,records,32,byref(count)):raise ctypes.WinError(ctypes.get_last_error())
            output=[]
            for record in records[:count.value]:
                if record.EventType==1:
                    key=record.Event.KeyEvent
                    output.append(dict(down=bool(key.bKeyDown),char=ord(key.uChar.UnicodeChar),virtual_key=key.wVirtualKeyCode,control=key.dwControlKeyState))
            print('console records '+json.dumps(output),flush=True)
            if any(r['down'] and r['char']==47 for r in output):
                destination=Path(sys.argv[1])
                owned=Path(__file__).resolve().parents[2]/'artifacts/runner-readiness-ten-project-pass/frogmouth/input-reduction'
                destination.resolve().relative_to(owned.resolve())
                with destination.open('x',encoding='utf-8') as receipt:json.dump(dict(std_handle=int(handle),stream_handle=int(stream),records=output),receipt,indent=2)
                print('synthetic slash received',flush=True);return
        raise RuntimeError('no synthetic slash observed within diagnostic bound')
    finally:kernel.SetConsoleMode(handle,original)


if __name__=='__main__':main()
