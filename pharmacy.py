import os
import random
import tkinter as tk
from tkinter import ttk

import simpy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

HOURLY_MULT = {
     8: 0.6,  9: 1.0, 10: 1.4, 11: 1.3,
     12: 0.7, 13: 0.6, 14: 1.0, 15: 1.3,
     16: 1.5, 17: 1.6, 18: 1.3, 19: 0.8,
}


def einstellungen():

    result = {}
    root = tk.Tk()
    root.title("Apotheken-Simulation – Parameter")
    root.resizable(False, False)
    root.configure(bg="#F1F5F9")

    BG = "#F1F5F9"
    PANEL = "#FFFFFF"
    BLUE = "#1D4ED8"
    DARK = "#1E293B"
    MUTED = "#64748B"

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TFrame",       background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("TLabel",       background=BG,    font=("Segoe UI", 10), foreground=DARK)
    style.configure("Head.TLabel",  background=PANEL, font=("Segoe UI", 10, "bold"), foreground=BLUE)
    style.configure("Title.TLabel", background=BG,    font=("Segoe UI", 13, "bold"), foreground=BLUE)
    style.configure("Sub.TLabel",   background=BG,    font=("Segoe UI", 9),  foreground=MUTED)
    style.configure("Unit.TLabel",  background=PANEL, font=("Segoe UI", 9),  foreground=MUTED)
    style.configure("Err.TLabel",   background=BG,    font=("Segoe UI", 9),  foreground="#DC2626")
    style.configure("TEntry",       font=("Segoe UI", 10), fieldbackground="white")
    style.configure("Run.TButton",  font=("Segoe UI", 11, "bold"), padding=10,
                    background=BLUE, foreground="white")
    style.map("Run.TButton", background=[("active", "#1E40AF")])

    ttk.Label(root, text="Apotheken-Simulation – Parameter",
              style="Title.TLabel", padding=(20, 14, 20, 2)).grid(row=0, column=0, sticky="w")
    ttk.Label(root, text="Werte anpassen und auf  Simulation starten  klicken.",
              style="Sub.TLabel", padding=(20, 0, 20, 8)).grid(row=1, column=0, sticky="w")

    def panel(row, title):
        outer = ttk.Frame(root, style="TFrame", padding=(16, 4))
        outer.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 2))
        inner = ttk.Frame(outer, style="Panel.TFrame", padding=12)
        inner.pack(fill="x")
        ttk.Label(inner, text=title, style="Head.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        return inner

    def field(p, row, label, default, unit="", width=9):
        ttk.Label(p, text=label, background=PANEL,
                  font=("Segoe UI", 10), foreground=DARK).grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 10))
        var = tk.StringVar(value=str(default))
        ttk.Entry(p, textvariable=var, width=width).grid(row=row, column=1, sticky="w")
        if unit:
            ttk.Label(p, text=unit, style="Unit.TLabel").grid(
                row=row, column=2, sticky="w", padx=(8, 0))
        return var

    # Abschnitt 1 – Kunden
    p1 = panel(2, "Kunden & Ankuenfte")
    v_rate = field(p1, 1, "Basisankunftsrate", 15,  "Kunden / Stunde")
    v_rxp = field(p1, 2, "Rezeptquote", 40,  "%  der Kunden haben ein Rezept")
    v_pat = field(p1, 3, "Maximale Geduld", 10,  "Minuten – danach verlässt Kunde")

    # Abschnitt 2 – Bedienzeiten
    p2 = panel(3, "Bedienzeiten (Modalwert der Dreiecksverteilung)")
    v_otc = field(p2, 1, "Ohne Rezept", 2.5, "min  (einfacher Kauf)")
    v_rx = field(p2, 2, "Mit Rezept", 7.0, "min  (Rezeptpruefung + Beratung)")

    # Abschnitt 3 – Wirtschaft
    p3 = panel(4, "Wirtschaftliche Parameter")
    v_rev = field(p3, 1, "Erloese pro Kunde", 18,  "EUR")
    v_wage = field(p3, 2, "Tagesgehalt pro Apotheker",  120, "EUR / Tag")

    # Abschnitt 4 – Simulation
    p4 = panel(5, "Simulationseinstellungen")
    v_open = field(p4, 1, "Oeffnungsstunde", 8,  "(z.B. 8 = 08:00)")
    v_close = field(p4, 2, "Schlussstunde", 20,  "(z.B. 20 = 20:00)")
    v_maxph = field(p4, 3, "Max. Apothekeranzahl", 5,  "Bereich: 1 … N")
    v_runs = field(p4, 4, "Replikationen", 40,  "pro Konfiguration")

    err_var = tk.StringVar()
    ttk.Label(root, textvariable=err_var, style="Err.TLabel",
              padding=(20, 4, 20, 0)).grid(row=6, column=0, sticky="w")

    def starten():
        try:
            p = {
                "base_rate":  float(v_rate.get()),
                "rx_prob":    float(v_rxp.get()) / 100,
                "patience":   float(v_pat.get()),
                "otc_time":   float(v_otc.get()),
                "rx_time":    float(v_rx.get()),
                "revenue":    float(v_rev.get()),
                "wage":       float(v_wage.get()),
                "open":       int(float(v_open.get())),
                "close":      int(float(v_close.get())),
                "max_ph":     int(float(v_maxph.get())),
                "runs":       int(float(v_runs.get())),
            }
            assert 1 <= p["base_rate"] <= 200, "Ankunftsrate: 1–200"
            assert 1 <= p["rx_prob"] * 100 <= 99,  "Rezeptquote: 1–99 %"
            assert 0 < p["patience"], "Geduld muss > 0 sein"
            assert p["open"] < p["close"], "Oeffnung muss vor Schliessung liegen"
            assert 1 <= p["max_ph"] <= 10, "Max. Apotheker: 1–10"
            assert 1 <= p["runs"] <= 500, "Replikationen: 1–500"
            result.update(p)
            root.destroy()
        except (ValueError, AssertionError) as e:
            err_var.set(f"Fehler: {e}")

    ttk.Button(root, text="▶   Simulation starten", style="Run.TButton",
               command=starten).grid(row=7, column=0, sticky="ew",
                                     padx=16, pady=14, ipadx=10)
    root.mainloop()
    return result if result else None


def bedienzeit(is_rx, p):
    if is_rx:
        return random.triangular(4.0, 12.0, p["rx_time"])
    else:
        return random.triangular(1.0, 5.0,  p["otc_time"])


def kunde(env, schalter, stats, p):
    ankunft = env.now
    is_rx = random.random() < p["rx_prob"]

    with schalter.request() as req:
        ergebnis = yield req | env.timeout(p["patience"])
        if req in ergebnis:
            stats["wartezeiten"].append(env.now - ankunft)
            stats["bedient"] += 1
            yield env.timeout(bedienzeit(is_rx, p))
        else:
            stats["abgebrochen"] += 1


def ankunftsgenerator(env, schalter, stats, p):
    yield env.timeout(p["open"] * 60)
    while env.now < p["close"] * 60:
        stunde = int(env.now // 60)
        rate_pro_min = p["base_rate"] * HOURLY_MULT.get(stunde, 1.0) / 60.0
        yield env.timeout(random.expovariate(rate_pro_min))
        if env.now < p["close"] * 60:
            env.process(kunde(env, schalter, stats, p))


def simuliere_tag(n_apotheker, p):
    stats = {"wartezeiten": [], "bedient": 0, "abgebrochen": 0}
    env = simpy.Environment()
    schalter = simpy.Resource(env, capacity=n_apotheker)
    env.process(ankunftsgenerator(env, schalter, stats, p))
    env.run(until=p["close"] * 60 + 60)

    w = stats["wartezeiten"]
    gewinn = stats["bedient"] * p["revenue"] - n_apotheker * p["wage"] - stats["abgebrochen"] * 8
    return {
        "bedient": stats["bedient"],
        "abgebrochen": stats["abgebrochen"],
        "avg_wait": np.mean(w) if w else 0.0,
        "gewinn": gewinn,
    }


def szenario(n, p):
    tage = [simuliere_tag(n, p) for _ in range(p["runs"])]
    return {
        "avg_wait": np.mean([t["avg_wait"] for t in tage]),
        "gewinn": np.mean([t["gewinn"] for t in tage]),
        "bedient": np.mean([t["bedient"] for t in tage]),
        "abgebrochen": np.mean([t["abgebrochen"] for t in tage]),
    }


def stundenweise_wartezeit(n_apotheker, p, runs=20):
    stunden_wz = {h: [] for h in range(p["open"], p["close"])}

    for _ in range(runs):
        def cust(env, sc, arr, is_rx):
            with sc.request() as req:
                res = yield req | env.timeout(p["patience"])
                if req in res:
                    stunden_wz[min(int(arr // 60), p["close"] - 1)].append(env.now - arr)
                    yield env.timeout(bedienzeit(is_rx, p))

        def gen(env, sc):
            yield env.timeout(p["open"] * 60)
            while env.now < p["close"] * 60:
                h = int(env.now // 60)
                rate = p["base_rate"] * HOURLY_MULT.get(h, 1.0) / 60.0
                yield env.timeout(random.expovariate(rate))
                if env.now < p["close"] * 60:
                    env.process(cust(env, sc, env.now, random.random() < p["rx_prob"]))

        env = simpy.Environment()
        sc = simpy.Resource(env, capacity=n_apotheker)
        env.process(gen(env, sc))
        env.run(until=p["close"] * 60 + 60)

    stunden = list(range(p["open"], p["close"]))
    return stunden, [np.mean(stunden_wz[h]) if stunden_wz[h] else 0.0 for h in stunden]


def sensitivitaet(n_opt, p, runs=20):
    orig_rate = p["base_rate"]
    orig_rxp = p["rx_prob"]

    raten = [orig_rate * f for f in [0.7, 0.85, 1.0, 1.15, 1.30]]
    wz_rate = []
    for r in raten:
        p["base_rate"] = r
        tage = [simuliere_tag(n_opt, p) for _ in range(runs)]
        wz_rate.append(np.mean([t["avg_wait"] for t in tage]))
    p["base_rate"] = orig_rate

    rxps = [0.20, 0.30, 0.40, 0.50, 0.60]
    wz_rxp = []
    for rx in rxps:
        p["rx_prob"] = rx
        tage = [simuliere_tag(n_opt, p) for _ in range(runs)]
        wz_rxp.append(np.mean([t["avg_wait"] for t in tage]))
    p["rx_prob"] = orig_rxp

    return raten, wz_rate, rxps, wz_rxp


def grafiken(p):
    ns = list(range(1, p["max_ph"] + 1))
    print("Simulation laeuft ...")
    ergebn = {n: szenario(n, p) for n in ns}
    opt = max(ns, key=lambda n: ergebn[n]["gewinn"])

    print("Stuendliches Lastprofil ...")
    stunden, last_1 = stundenweise_wartezeit(1,   p)
    stunden, last_opt = stundenweise_wartezeit(opt, p)

    BLAU = "#2563EB"
    GRUEN = "#16A34A"
    ROT = "#DC2626"
    GELB = "#D97706"
    BG = "#F8FAFC"

    fig = plt.figure(figsize=(13, 9), facecolor=BG)
    fig.suptitle(
        f"Diskrete Simulation – Apotheke  |  "
        f"Rate {p['base_rate']}/h  |  Rezept {int(p['rx_prob']*100)}%  |  "
        f"Geduld {p['patience']} min  |  {p['runs']} Replikationen",
        fontsize=11, fontweight="bold", color="#1E293B", y=0.99
    )
    gs = gridspec.GridSpec(2, 2, hspace=0.42, wspace=0.32,
                           left=0.07, right=0.97, top=0.93, bottom=0.08)

    # F1 – Wartezeit
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(ns, [ergebn[n]["avg_wait"] for n in ns],
             "o-", color=BLAU, lw=2.2, ms=7, label="Mittlere Wartezeit")
    ax1.axhline(5,  color=GRUEN, ls=":", lw=1.5, label="Ziel: 5 min")
    ax1.axhline(10, color=GELB,  ls=":", lw=1.2, label="Limit: 10 min")
    ax1.axvline(opt, color=GRUEN, ls="--", lw=1.2, alpha=0.5)
    ax1.set_title("Wie lange warten Kunden?", fontsize=9, fontweight="bold")
    ax1.set_xlabel("Anzahl Apotheker"); ax1.set_ylabel("Minuten")
    ax1.set_xticks(ns); ax1.legend(fontsize=7); ax1.grid(True, alpha=0.3)

    # F2 – Gewinn
    ax2 = fig.add_subplot(gs[0, 1])
    farben = [GRUEN if n == opt else BLAU for n in ns]
    bars = ax2.bar(ns, [ergebn[n]["gewinn"] for n in ns],
                     color=farben, edgecolor="white")
    for bar, n in zip(bars, ns):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                 f"{ergebn[n]['gewinn']:.0f}€", ha="center", va="bottom", fontsize=8)
    ax2.axvline(opt, color=GRUEN, ls="--", lw=1.4, alpha=0.7,
                label=f"Optimal = {opt} Apotheker")
    ax2.set_title("Welche Anzahl maximiert den Gewinn?", fontsize=9, fontweight="bold")
    ax2.set_xlabel("Anzahl Apotheker"); ax2.set_ylabel("Tagesgewinn (EUR)")
    ax2.set_xticks(ns); ax2.legend(fontsize=7); ax2.grid(True, axis="y", alpha=0.3)

    # F3 – Stuendliche Last
    ax3 = fig.add_subplot(gs[1, 0])
    x = range(len(stunden))
    ax3.bar(x, last_1,   color=ROT,  alpha=0.7, label="1 Apotheker")
    ax3.bar(x, last_opt, color=BLAU, alpha=0.8, label=f"{opt} Apotheker (optimal)")
    ax3.set_xticks(list(x))
    ax3.set_xticklabels([f"{h}:00" for h in stunden], rotation=45, fontsize=7)
    ax3.set_title("Stoszeiten im Tagesverlauf", fontsize=9, fontweight="bold")
    ax3.set_xlabel("Tageszeit"); ax3.set_ylabel("Ø Wartezeit (min)")
    ax3.legend(fontsize=7); ax3.grid(True, axis="y", alpha=0.3)

    # F4 – Bedient vs. Abgebrochen
    ax4 = fig.add_subplot(gs[1, 1])
    w, x = 0.35, np.array(ns)
    ax4.bar(x - w/2, [ergebn[n]["bedient"] for n in ns], w,
            color=GRUEN, label="Bedient",     edgecolor="white")
    ax4.bar(x + w/2, [ergebn[n]["abgebrochen"] for n in ns], w,
            color=ROT,   label="Abgebrochen", edgecolor="white")
    ax4.axvline(opt, color=GELB, ls="--", lw=1.4, alpha=0.7)
    ax4.set_title("Bediente vs. abgebrochene Kunden", fontsize=9, fontweight="bold")
    ax4.set_xlabel("Anzahl Apotheker"); ax4.set_ylabel("Kunden / Tag")
    ax4.set_xticks(ns); ax4.legend(fontsize=7); ax4.grid(True, axis="y", alpha=0.3)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pharmacy_results.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"Grafik gespeichert: {out}")
    plt.show()

    print(f"\n{'Apo.':>5}  {'Ø Warte':>8}  {'Bedient':>8}  {'Abgebr.':>8}  {'Gewinn':>9}")
    print("-" * 50)
    for n in ns:
        r = ergebn[n]
        mark = "  <- OPTIMAL" if n == opt else ""
        print(f"{n:>5}  {r['avg_wait']:>7.1f}m  {r['bedient']:>8.0f}  "
              f"{r['abgebrochen']:>8.0f}  {r['gewinn']:>8.0f} EUR{mark}")


if __name__ == "__main__":
    params = einstellungen()
    if params:
        print("\nGewaehlte Parameter:")
        for k, v in params.items():
            print(f"  {k:15} = {v}")
        print()
        grafiken(params)
    else:
        print("Simulation abgebrochen.")