# Infrastructure Validation Report

Generated: 2026-07-15T09:10:20.939906+00:00

## Service Health
| Service | Status |
|---------|--------|
| FastAPI (8500) | UP |

## CPU
```
cpu  2381331 64615 386268 1273645870 55113 0 3464 2440 0 0
```

## Memory
```
MemTotal:       15510480 kB
MemFree:         3484592 kB
MemAvailable:   12987744 kB
```

## Disk
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2       492G   44G  423G  10% /
```

## Top Processes (by memory)
```
USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
bmkg       31468  0.0  5.4 6044532 844232 ?      Ssl  Jul08   0:22 /home/bmkg/miniconda3/envs/pimes-prod/bin/python scheduler.py
bmkg      163683  0.5  3.4 3936696 536612 ?      Ssl  15:50   0:07 /home/bmkg/miniconda3/envs/pimes-prod/bin/python3.11 /home/bmkg/miniconda3/envs/pimes-prod/bin/uvicorn api:app --host 127.0.0.1 --port 8000
gdm         1612  0.2  1.6 6460516 251108 tty1   Sl+  Jul06  33:40 /usr/bin/gnome-shell
gdm         2001  0.0  0.6 3191744 101768 tty1   Sl+  Jul06   0:00 /usr/libexec/mutter-x11-frames
gdm         2019  0.0  0.4 495432 74776 tty1     Sl   Jul06   0:00 /usr/libexec/ibus-x11 --kill-daemon
gdm         1733  0.0  0.4 244808 66988 tty1     S+   Jul06   0:00 /usr/bin/Xwayland :1024 -rootless -noreset -accessx -core -auth /run/user/120/.mutter-Xwaylandauth.VKCWR3 -listenfd 4 -listenfd 5 -displayfd 6 -initfd 7 -byteswappedclients
bmkg      163990  0.5  0.4 918092 65284 ?        Sl   15:53   0:05 /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500
root         450  0.0  0.3 108132 53496 ?        S<s  Jul06   0:19 /usr/lib/systemd/systemd-journald
root       11651  0.0  0.2 2961336 45840 ?       Ssl  Jul07   1:18 /snap/snapd/current/usr/lib/snapd/snapd
```
