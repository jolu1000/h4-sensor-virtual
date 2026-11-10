#!/usr/bin/env python3
"""
Proyecto H4 - Registrador de lecturas (corre en la Raspberry Pi).

Lee las líneas que manda el Arduino por USB ("t_ms,angulo,d1_cm,d2_cm"),
les agrega la marca de tiempo de la Raspberry y las guarda en SQLite.

Uso:
    python3 registrar.py                    # detecta el puerto solo
    python3 registrar.py --puerto /dev/ttyUSB0   (Linux)
    python registrar.py --puerto COM3            (Windows)
    python3 registrar.py --simular          # sin hardware, para probar
    python3 registrar.py --duracion 120     # graba 2 minutos y termina

Ctrl+C para detener.
"""
import argparse
import math
import random
import sqlite3
import sys
import time
from datetime import datetime

ESQUEMA = """
CREATE TABLE IF NOT EXISTS lecturas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT    NOT NULL,   -- marca de tiempo ISO 8601 (Raspberry)
    ts_unix     REAL    NOT NULL,   -- segundos desde epoch
    t_arduino   INTEGER,            -- millis() del Arduino
    angulo      INTEGER,            -- comando del servo [grados]
    d1_cm       REAL,               -- HC-SR04 #1, sensor a sustituir (NULL = sin eco)
    d2_cm       REAL                -- HC-SR04 #2, variable correlacionada
);
"""


def detectar_puerto():
    """Busca el Arduino en Linux (/dev/ttyUSB*, /dev/ttyACM*) o Windows (COMx)."""
    from serial.tools import list_ports
    puertos = list(list_ports.comports())
    # Los clones con chip CH340 tienen VID 0x1A86; los UNO originales, 0x2341.
    for p in puertos:
        if p.vid in (0x1A86, 0x2341, 0x2A03):
            return p.device
    for p in puertos:
        if "USB" in p.device or "ACM" in p.device or "CH340" in (p.description or ""):
            return p.device
    sys.exit("No encontré el Arduino. ¿Está conectado por USB? Indica el puerto "
             "a mano: --puerto /dev/ttyUSB0 (Linux) o --puerto COM3 (Windows)")


def parsear(linea):
    """Devuelve (t_ms, angulo, d1, d2) o None si la línea no sirve."""
    linea = linea.strip()
    if not linea or linea.startswith("#"):
        return None
    partes = linea.split(",")
    if len(partes) != 4:
        return None
    try:
        t_ms = int(partes[0])
        ang = int(partes[1])
        d1 = float(partes[2])
        d2 = float(partes[3])
    except ValueError:
        return None
    # -1 significa "sin eco": se guarda como NULL para distinguirlo de 0 cm
    d1 = None if d1 < 0 else d1
    d2 = None if d2 < 0 else d2
    return t_ms, ang, d1, d2


def fuente_serial(puerto, baudios):
    import serial  # pip install pyserial
    with serial.Serial(puerto, baudios, timeout=1) as s:
        time.sleep(2)            # el UNO se reinicia al abrir el puerto
        s.reset_input_buffer()
        while True:
            yield s.readline().decode("utf-8", errors="ignore")


def fuente_simulada():
    """Imita al Arduino: servo en barrido y dos sensores correlacionados."""
    t0 = time.time()
    while True:
        t = time.time() - t0
        ang = int(90 + 60 * math.sin(2 * math.pi * t / 12))
        base = 10 + 0.12 * (ang - 30)
        d1 = base + random.gauss(0, 0.3)
        d2 = base + 1.5 + random.gauss(0, 0.3)
        time.sleep(0.1)
        yield f"{int(t * 1000)},{ang},{d1:.1f},{d2:.1f}\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--puerto", help="ej. /dev/ttyUSB0 (por defecto, autodetecta)")
    ap.add_argument("--baudios", type=int, default=115200)
    ap.add_argument("--db", default="h4_lecturas.db")
    ap.add_argument("--duracion", type=float, default=0,
                    help="segundos a grabar (0 = hasta Ctrl+C)")
    ap.add_argument("--simular", action="store_true",
                    help="genera datos falsos para probar sin hardware")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.execute(ESQUEMA)
    con.commit()

    if args.simular:
        fuente = fuente_simulada()
        print("Modo simulado (sin hardware).")
    else:
        puerto = args.puerto or detectar_puerto()
        print(f"Leyendo desde {puerto} a {args.baudios} baudios...")
        fuente = fuente_serial(puerto, args.baudios)

    print(f"Guardando en {args.db}. Ctrl+C para detener.\n")
    print(f"{'hora':<26}{'ang':>5}{'d1 [cm]':>10}{'d2 [cm]':>10}")

    inicio = time.time()
    n = 0
    try:
        for linea in fuente:
            dato = parsear(linea)
            if dato is None:
                continue
            t_ms, ang, d1, d2 = dato
            ahora = time.time()
            ts = datetime.fromtimestamp(ahora).isoformat(timespec="milliseconds")
            con.execute(
                "INSERT INTO lecturas (ts, ts_unix, t_arduino, angulo, d1_cm, d2_cm) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ts, ahora, t_ms, ang, d1, d2))
            n += 1
            if n % 10 == 0:                 # commit cada ~1 s
                con.commit()
            fmt = lambda d: "sin eco" if d is None else f"{d:.1f}"
            print(f"{ts:<26}{ang:>5}{fmt(d1):>10}{fmt(d2):>10}")
            if args.duracion and ahora - inicio >= args.duracion:
                break
    except KeyboardInterrupt:
        pass
    finally:
        con.commit()
        con.close()
        print(f"\n{n} lecturas guardadas en {args.db}")


if __name__ == "__main__":
    main()
