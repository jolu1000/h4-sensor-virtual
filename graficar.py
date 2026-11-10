#!/usr/bin/env python3
"""
Proyecto H4 - Gráfico de evidencia del primer hito.

Lee h4_lecturas.db y genera evidencia_hito1.png con:
  arriba: d1 (sensor a sustituir) y d2 (variable correlacionada) vs. tiempo
  abajo:  d1 vs. d2, con la correlación de Pearson y la recta de ajuste

Uso:
    python3 graficar.py
    python3 graficar.py --db h4_lecturas.db --salida evidencia_hito1.png
"""
import argparse
import sqlite3
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="h4_lecturas.db")
    ap.add_argument("--salida", default="evidencia_hito1.png")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    filas = con.execute(
        "SELECT ts, d1_cm, d2_cm FROM lecturas ORDER BY ts_unix").fetchall()
    con.close()
    if not filas:
        raise SystemExit("La base de datos no tiene lecturas.")

    t = [datetime.fromisoformat(f[0]) for f in filas]
    d1 = np.array([np.nan if f[1] is None else f[1] for f in filas])
    d2 = np.array([np.nan if f[2] is None else f[2] for f in filas])

    ok = ~np.isnan(d1) & ~np.isnan(d2)
    r = np.corrcoef(d1[ok], d2[ok])[0, 1] if ok.sum() > 2 else float("nan")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8))

    ax1.plot(t, d1, label="d1: HC-SR04 #1 (sensor a sustituir)", lw=1.2)
    ax1.plot(t, d2, label="d2: HC-SR04 #2 (variable correlacionada)", lw=1.2)
    ax1.set_xlabel("Hora (marca de tiempo de la Raspberry Pi)")
    ax1.set_ylabel("Distancia [cm]")
    ax1.set_title(f"Lecturas registradas — {t[0]:%d-%m-%Y %H:%M:%S}, "
                  f"{len(filas)} muestras")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M:%S"))

    ax2.scatter(d2[ok], d1[ok], s=8, alpha=0.6)
    if ok.sum() > 2:
        m, b = np.polyfit(d2[ok], d1[ok], 1)
        xs = np.linspace(np.nanmin(d2[ok]), np.nanmax(d2[ok]), 50)
        ax2.plot(xs, m * xs + b, color="C1",
                 label=f"d1 = {m:.2f}·d2 {'+' if b >= 0 else '−'} {abs(b):.2f}")
        ax2.legend()
    ax2.set_xlabel("d2 [cm]")
    ax2.set_ylabel("d1 [cm]")
    ax2.set_title(f"Correlación entre sensores: r = {r:.3f}")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(args.salida, dpi=150)
    print(f"Gráfico guardado en {args.salida} (r = {r:.3f})")


if __name__ == "__main__":
    main()
