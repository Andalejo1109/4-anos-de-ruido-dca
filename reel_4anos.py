"""Reel '4 años de razones para no invertir' — GIF 9:16 (educativo, no es asesoría).
Portafolio MODELO con pesos del core (no es la cuenta real de eToro).
Datos: Yahoo Finance (Adj Close) vía yfinance, caché parquet. Estilo = GIF 'De 70 mil a 225 mil'."""
import subprocess, shutil
from pathlib import Path
import numpy as np, pandas as pd, yfinance as yf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt

OUT = Path(__file__).parent; FR = OUT / "frames"
W = {"SPYG": .32, "BRK-B": .22, "IEMG": .20, "SMH": .19, "VTI": .07}   # pesos del core
CAPITAL_INICIAL = 1000   # [DEFAULT, pendiente de aprobación]
APORTE_MENSUAL = 200     # [DEFAULT, pendiente de aprobación]
INI, APORTE = CAPITAL_INICIAL, APORTE_MENSUAL
INICIO, FIN = "2021-12-01", "2026-10-21"
# Paleta (copiada del GIF 70k→225k)
BG, GRID, TEXT, MUTED, FOOT = "#0B1020", "#1C2438", "#E8ECF4", "#8B93A7", "#5C6478"
MENTA, AZUL, ROJO, AMBAR = "#3DDB8A", "#6EA8FE", "#F2777A", "#F5B042"

# 1) Precios diarios ajustados (caché local)
pq = OUT / "data/precios.parquet"
if pq.exists(): px = pd.read_parquet(pq)
else:
    px = yf.download(list(W), start="2021-10-01", end="2026-10-22", auto_adjust=True, progress=False)["Close"]
    px.to_parquet(pq)
px = px[list(W)].dropna()

# 2) Índice del core con rebalanceo mensual: pesos objetivo al inicio de cada mes, deriva dentro del mes
def indice(p):
    r = p.pct_change().fillna(0); val = [1.0]; v = 1.0
    for mes, g in r.groupby(r.index.to_period("M")):
        cr = (1 + g).cumprod()                       # crecimiento de cada activo dentro del mes
        serie = v * (cr * pd.Series(W)).sum(axis=1)
        val.append(serie); v = serie.iloc[-1]
    return pd.concat(val[1:])
idx_all = indice(px)

# 3) Drawdown 2021-22 (pico dic-2021 → valle hasta sep-2022) del core B&H
w = idx_all["2021-12-01":"2022-09-30"]
pico_f = w.idxmax(); valle_f = w[pico_f:].idxmin()
dd2122 = w[valle_f] / w[pico_f] - 1

# 4) DCA mensual desde oct-2022: unidades del índice compradas el 1er día hábil de cada mes
idx = idx_all[INICIO:FIN]
primeros = idx.groupby(idx.index.to_period("M")).head(1).index
aporte = pd.Series(0.0, index=idx.index); aporte[primeros] = APORTE; aporte.iloc[0] = INI
unidades = (aporte / idx).cumsum()
valor = unidades * idx; aportado = aporte.cumsum()

# 5) Eventos y su caída (pico previo de 20 días → mínimo en los 60 días siguientes, índice sin aportes)
EVENTOS = [("2022-11-02", "Fed: alzas de tasas\n(hasta jul-2023)"), ("2023-03-10", "Quiebra bancos\nregionales (SVB)"),
           ("2025-04-02", "Liberation Day\n(aranceles)"), ("2026-02-28", "Guerra EE.UU./Israel\nvs Irán"),
           ("2026-10-01", "Caída de chips\noct-2026")]
filas = []
for f, txt in EVENTOS:
    f = pd.Timestamp(f); a = idx_all[f - pd.Timedelta(days=28): f + pd.Timedelta(days=90)]
    pk = a[:f + pd.Timedelta(days=3)].idxmax(); vl = a[pk:].idxmin()
    filas.append(dict(evento=txt.replace("\n", " "), fecha=f.date(), pico=pk.date(), valle=vl.date(), dd_pct=round((a[vl]/a[pk]-1)*100, 2)))
ev = pd.DataFrame(filas)
resumen = pd.DataFrame([dict(evento="DD core 2021-22", fecha="", pico=pico_f.date(), valle=valle_f.date(), dd_pct=round(dd2122*100, 2)),
    dict(evento="Aportado final", fecha=idx.index[-1].date(), pico="", valle="", dd_pct=aportado.iloc[-1]),
    dict(evento="Valor final", fecha=idx.index[-1].date(), pico="", valle="", dd_pct=round(valor.iloc[-1], 2))])
resumen = pd.concat([resumen, pd.DataFrame([dict(evento="Múltiplo valor/aportado", fecha=idx.index[-1].date(), pico="", valle="", dd_pct=round(valor.iloc[-1]/aportado.iloc[-1], 2))])])
pd.concat([ev, resumen]).to_csv(OUT / "cifras.csv", index=False); print(pd.concat([ev, resumen]).to_string())

# 6) Frames
FPS, N_CARD, N_DRAW, N_HOLD = 20, 30, 170, 40            # 12 s
semanas = valor.resample("W-FRI").last().index
semanas = [valor.index[valor.index.get_indexer([s], method="pad")[0]] for s in semanas] + [valor.index[-1]]
money = lambda v: f"US${v:,.0f}".replace(",", ".")
MESES = "ene feb mar abr may jun jul ago sep oct nov dic".split()
fecha_txt = lambda d: f"{MESES[d.month-1]} {d.year}"

def base():
    fig = plt.figure(figsize=(10.8, 19.2), dpi=100); fig.patch.set_facecolor(BG)
    fig.text(.5, .955, "Portafolio modelo con los pesos de mi core  ·  DCA mensual", ha="center", color=MUTED, fontsize=22)
    fig.text(.5, .915, "4 AÑOS DE RAZONES", ha="center", color=TEXT, fontsize=50, fontweight="bold")
    fig.text(.5, .878, "PARA NO INVERTIR", ha="center", color=TEXT, fontsize=40, fontweight="bold")
    fig.text(.5, .848, "SPYG 32% · BRK.B 22% · IEMG 20% · SMH 19% · VTI 7%", ha="center", color=MUTED, fontsize=20)
    fig.text(.5, .045, "Portafolio modelo, no es la cuenta real. Aporte ilustrativo, sin apalancamiento.\n"
             "Educativo, no es asesoría. Riesgo de pérdida. Rentabilidades pasadas no garantizan futuras.\n"
             "Fuente: Yahoo Finance (Adj Close), cálculo propio.",
             ha="center", va="center", color=FOOT, fontsize=14, linespacing=1.5)
    fig.text(.5, .012, "@Andalejo1109", ha="center", color=MUTED, fontsize=18, fontweight="bold")
    return fig

def card(i):
    fig = base(); a = min(1, i / 10)
    fig.text(.5, .64, "DIC 2021: EMPIEZO A APORTAR", ha="center", color=MUTED, fontsize=30, alpha=a)
    fig.text(.5, .55, f"{dd2122*100:.1f}%".replace(".", ","), ha="center", color=ROJO, fontsize=130, fontweight="bold", alpha=a)
    fig.text(.5, .49, f"caída del core: {fecha_txt(pico_f)} → {fecha_txt(valle_f)}", ha="center", color=TEXT, fontsize=30, alpha=a)
    fig.text(.5, .43, "Lo que vino después: no vendí.", ha="center", color=MENTA, fontsize=30, fontweight="bold", alpha=a)
    return fig

def chart(k, cierre=False):
    fig = base(); ax = fig.add_axes([.12, .2, .80, .6]); ax.set_facecolor(BG)
    fin = semanas[min(len(semanas)-1, k)]; v, c = valor[:fin], aportado[:fin]
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=16); ax.yaxis.grid(True, color=GRID, lw=.8)
    ax.set_xlim(valor.index[0], valor.index[-1] + pd.Timedelta(days=30)); ax.set_ylim(0, valor.max()*1.15)
    import matplotlib.dates as mdates; ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(4000)); ax.yaxis.set_major_formatter(lambda y, _: f"{y/1000:.0f}K")
    ax.plot(c.index, c, color=AZUL, lw=2.5, ls=(0, (6, 4)), drawstyle="steps-post")
    ax.plot(v.index, v, color=MENTA, lw=4, solid_capstyle="round")
    ax.scatter([fin], [v.iloc[-1]], s=160, color=MENTA, edgecolors="white", zorder=6)
    tarde = fin > pd.Timestamp("2025-06-01"); ha = "right" if tarde else "left"; pad = "  " if not tarde else ""
    ax.text(fin, v.iloc[-1]*1.03, f"{pad}valor  ", color=MENTA, fontsize=17, va="bottom", ha=ha)
    ax.text(fin, c.iloc[-1]*0.95, f"{pad}aportado  ", color=AZUL, fontsize=17, va="top", ha=ha)
    if fin >= pd.Timestamp("2022-01-03"):   # inset: core B&H sin aportes, base 100
        ins = ax.inset_axes([0.22, 0.57, 0.38, 0.15]); ins.set_facecolor(BG)
        b = idx_all["2021-12-01":"2022-12-31"]; b = b / b.iloc[0] * 100; bv = b[:fin]
        for sp in ins.spines.values(): sp.set_color(GRID)
        ins.tick_params(colors=MUTED, labelsize=11); ins.yaxis.grid(True, color=GRID, lw=.6)
        ins.set_xlim(b.index[0], b.index[-1]); ins.set_ylim(b.min()*0.92, b.max()*1.08)
        ins.xaxis.set_major_locator(mdates.MonthLocator([1, 4, 7, 10])); ins.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        ins.plot(bv.index, bv, color=MENTA, lw=2)
        tramo = bv[pico_f:valle_f]
        if len(tramo): ins.plot(tramo.index, tramo, color=ROJO, lw=2.4)
        if fin >= valle_f:
            ins.scatter([valle_f], [b[valle_f]], s=50, color=ROJO, edgecolors="white", zorder=5)
            ins.text(valle_f, b[valle_f], f" {dd2122*100:.1f}%".replace(".", ","), color=ROJO, fontsize=13, fontweight="bold", va="top")
        ins.set_title("Core sin aportes, 2022 (base 100)", color=MUTED, fontsize=13, loc="left")
    for j, ((f, txt), r) in enumerate(zip(EVENTOS, filas)):
        f = pd.Timestamp(f)
        if f <= fin:
            y = valor.max()*[1.06, .97, .86, .34, .22][j]; ha = "right" if j >= 3 else "left"
            ax.axvline(f, color=AMBAR, lw=1.2, alpha=.6, ls=":")
            ax.text(f, y, f" {txt} ", color=AMBAR, fontsize=14, va="top", ha=ha)
    fig.text(.9, .815, fecha_txt(fin), ha="right", color=TEXT, fontsize=36, fontweight="bold", alpha=.9)
    if cierre:
        fig.text(.5, .15, "MISMO APORTE, 4 AÑOS DE RUIDO", ha="center", color=TEXT, fontsize=30, fontweight="bold")
        fig.text(.5, .118, f"Seguiste aportando cada mes  ·  valor ≈ {valor.iloc[-1]/aportado.iloc[-1]:.1f}x lo aportado".replace(".", ","), ha="center", color=MENTA, fontsize=20)
    else:
        fig.text(.5, .135, "Línea punteada: lo que puse. Línea verde: lo que vale.\nCada evento gritaba \"vende\". El aporte siguió igual cada mes.",
             ha="center", va="center", color=MUTED, fontsize=20, linespacing=1.5)
    return fig

(OUT / "output").mkdir(exist_ok=True)
f = chart(len(semanas)-1, cierre=True); f.savefig(OUT / "output/reel_4anos_final.svg", facecolor=BG); plt.close(f)   # versión estática en texto (SVG)
if FR.exists(): shutil.rmtree(FR)
FR.mkdir(); n = 0
def save(fig):
    global n; fig.savefig(FR / f"f{n:04d}.png", facecolor=BG); plt.close(fig); n += 1
for i in range(N_CARD): save(card(i))
for i in range(N_DRAW): save(chart(int(round(i * (len(semanas)-1) / (N_DRAW-1)))))
for i in range(N_HOLD): save(chart(len(semanas)-1, cierre=True))
shutil.copy(FR / f"f{n-1:04d}.png", OUT / "output/preview.png")
subprocess.run(f"ffmpeg -y -loglevel error -framerate {FPS} -i {FR}/f%04d.png -c:v libx264 -pix_fmt yuv420p {OUT}/output/reel_4anos.mp4", shell=True, check=True)
subprocess.run(f"ffmpeg -y -loglevel error -framerate {FPS} -i {FR}/f%04d.png -vf \"fps=15,scale=1080:1920,split[a][b];[a]palettegen=max_colors=96[p];[b][p]paletteuse=dither=bayer\" {OUT}/output/reel_4anos.gif", shell=True, check=True)
