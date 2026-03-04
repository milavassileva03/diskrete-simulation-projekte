import tkinter as tk
from tkinter import ttk
import random
import math
import matplotlib.pyplot as plt  # за графиките

# Konstanten
MONATE = ["Jan", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
TEMP_MITTEL = [-1,  1,  5, 10, 15, 18, 20, 20, 15, 10,  4,  0]
OEFFNUNGSTAGE = [8,  8,  9,  9,  4,  4,  4,  4,  4,  8,  9, 13]


def simuliere_jahr(basis_kunden, preis, herstellung, fixkosten, n_sim=500):
    jahres_gewinne = []
    mon_alle = [[] for _ in range(12)]

    for _ in range(n_sim):
        jahresgewinn = 0.0
        for m in range(12):
            monatsgewinn = 0.0
            for _ in range(OEFFNUNGSTAGE[m]):
                # random.gauss(μ, σ)-генерира случайно число от нормално разпределение
                t = random.gauss(TEMP_MITTEL[m], 3)
                # Kundenzahl berechnen:
                faktor = math.exp(-0.07 * max(t, -10))  # Връща по-голямото от двете числа.
                kunden = max(0, int(random.gauss(basis_kunden * faktor, 3)))  # няма отрицателен брой клиенти
                for _ in range(kunden):
                    becher = max(1, round(random.gauss(1.3, 0.5)))
                    monatsgewinn += becher * preis - becher * herstellung
                monatsgewinn -= fixkosten
            jahresgewinn += monatsgewinn
            mon_alle[m].append(monatsgewinn)
        jahres_gewinne.append(jahresgewinn)

    mon_mittel = [sum(mon_alle[m]) / len(mon_alle[m]) for m in range(12)]
    return jahres_gewinne, mon_mittel


def zeige_diagramme(gewinne, mon_mittel, basis_kunden):
    mittel = sum(gewinne) / len(gewinne)
    std = (sum((x - mittel)**2 for x in gewinne) / len(gewinne)) ** 0.5

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle(f"Gluehweinstand  |  {basis_kunden} Kunden/Tag", fontsize=13, fontweight="bold")

    # 1) Histogramm Jahresgewinn
    ax = axes[0]
    ax.hist(gewinne, bins=30, color="steelblue", edgecolor="white")
    ax.axvline(mittel, color="red",    linewidth=2,  label=f"Mittel: {mittel:.0f} EUR")
    ax.axvline(mittel - std, color="orange", linewidth=1, linestyle="--", label=f"-Std")
    ax.axvline(mittel + std, color="orange", linewidth=1, linestyle="--", label=f"+Std")
    ax.set_title("Jahresgewinn-Verteilung")
    ax.set_xlabel("Gewinn (EUR)")
    ax.set_ylabel("Haeufigkeit")
    ax.legend(fontsize=8)

    # 2) Monatlicher Durchschnittsgewinn
    ax = axes[1]
    farben = ["green" if v >= 0 else "red" for v in mon_mittel]
    ax.bar(MONATE, mon_mittel, color=farben, edgecolor="white")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_title("Monatlicher Durchschnittsgewinn")
    ax.set_xlabel("Monat")
    ax.set_ylabel("Gewinn (EUR)")
    ax.tick_params(axis="x", rotation=45)

    # 3) Kumulierter Gewinn (3 Beispielpfade)
    ax = axes[2]
    p = preis_var.get()
    h = hstk_var.get()
    f = fix_var.get()
    for farbe in ["steelblue", "seagreen", "tomato"]:
        kum, total = [], 0
        for m in range(12):
            mg = 0
            for _ in range(OEFFNUNGSTAGE[m]):
                t = random.gauss(TEMP_MITTEL[m], 3)
                faktor = math.exp(-0.07 * max(t, -10))
                k = max(0, int(random.gauss(basis_kunden * faktor, 3)))
                for _ in range(k):
                    b = max(1, round(random.gauss(1.3, 0.5)))
                    mg += b * p - b * h
                mg -= f
            total += mg
            kum.append(total)
        ax.plot(MONATE, kum, color=farbe, linewidth=2)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title("Kumulierter Gewinn (3 Pfade)")
    ax.set_xlabel("Monat")
    ax.set_ylabel("Kum. Gewinn (EUR)")
    ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.show()


def starten():
    k = kunden_var.get()
    n = nsim_var.get()
    p = preis_var.get()
    h = hstk_var.get()
    f = fix_var.get()

    gewinne, mon_mittel = simuliere_jahr(k, p, h, f, n)

    mittel = sum(gewinne) / len(gewinne)
    std = (sum((x - mittel)**2 for x in gewinne) / len(gewinne)) ** 0.5

    lbl_mittel.config(text=f"Mittelwert:  {mittel:,.0f} EUR")
    lbl_std.config(text=f"Std.-Abw.: {std:,.0f} EUR")
    lbl_min.config(text=f"Minimum: {min(gewinne):,.0f} EUR")
    lbl_max.config(text=f"Maximum: {max(gewinne):,.0f} EUR")

    zeige_diagramme(gewinne, mon_mittel, k)


# GUI
root = tk.Tk()
root.title("Monte-Carlo-Simulation: Gluehweinstand")
root.resizable(False, False)

frame = ttk.LabelFrame(root, text="Parameter", padding=12)
frame.grid(row=0, column=0, padx=16, pady=12, sticky="ew")


def add_row(parent, row, label, var, from_, to_, default):
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
    var.set(default)
    ttk.Scale(parent, from_=from_, to=to_, orient="horizontal",
              variable=var, length=200).grid(row=row, column=1, padx=8)
    ttk.Label(parent, textvariable=var).grid(row=row, column=2)


kunden_var = tk.IntVar()
nsim_var = tk.IntVar()
preis_var = tk.DoubleVar()
hstk_var = tk.DoubleVar()
fix_var = tk.DoubleVar()

add_row(frame, 0, "Basis-Kunden / Tag:",      kunden_var, 5,   100,  40)
add_row(frame, 1, "Simulationslaeufe:",        nsim_var,  100, 2000, 500)
add_row(frame, 2, "Verkaufspreis (EUR):",      preis_var, 1.0,  8.0, 3.5)
add_row(frame, 3, "Herstellungskosten (EUR):", hstk_var,  0.5,  3.0, 1.2)
add_row(frame, 4, "Fixkosten / Tag (EUR):",    fix_var,   10,   150,  50)

ttk.Button(root, text="  Simulation starten  ", command=starten).grid(
    row=1, column=0, pady=8)

res = ttk.LabelFrame(root, text="Ergebnis", padding=12)
res.grid(row=2, column=0, padx=16, pady=4, sticky="ew")

lbl_mittel = ttk.Label(res, text="Mittelwert:  –")
lbl_std = ttk.Label(res, text="Std.-Abw.:   –")
lbl_min = ttk.Label(res, text="Minimum:     –")
lbl_max = ttk.Label(res, text="Maximum:     –")
for i, lbl in enumerate([lbl_mittel, lbl_std, lbl_min, lbl_max]):
    lbl.grid(row=i, column=0, sticky="w", pady=2)

root.mainloop()
