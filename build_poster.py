"""UK Crime Hotspots: one-poster animated infographic.

Single vertical canvas (720x1080) where every panel lives together,
infographic style: panels build in one after another and the finished
poster holds at the end. Dark police/forensic theme.
"""
import imageio.v2 as imageio
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LinearSegmentedColormap

# ------------------------------------------------------------- theme
BG = "#0B0F1E"          # near-black navy
CARD = "#141B30"        # panel background
EDGE = "#232D4D"
YELLOW = "#FFD60A"      # police-tape yellow
RED = "#FF453A"         # hotspot red
CYAN = "#5AC8FA"
TEXT = "#E8ECF6"
MUTED = "#8E9BB3"

HEAT = LinearSegmentedColormap.from_list(
    "heat", ["#1B2440", "#3A2E63", "#B0303F", "#FF453A", "#FFD60A"])

plt.rcParams.update({
    "font.family": "Arial",
    "text.color": TEXT,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": EDGE,
})

W, H, DPI = 7.2, 10.8, 100  # 720 x 1080

# ------------------------------------------------------------- data
df = pd.read_csv("data/street_crimes.csv")
CAT_NICE = {
    "anti-social-behaviour": "Anti-social behaviour", "violent-crime": "Violence",
    "shoplifting": "Shoplifting", "other-theft": "Other theft",
    "theft-from-the-person": "Theft from person", "vehicle-crime": "Vehicle crime",
    "burglary": "Burglary", "criminal-damage-arson": "Damage & arson",
    "public-order": "Public order", "robbery": "Robbery", "drugs": "Drugs",
    "bicycle-theft": "Bike theft", "possession-of-weapons": "Weapons",
    "other-crime": "Other",
}
df["cat"] = df.category.map(CAT_NICE).fillna("Other")
df["city_short"] = df.city.str.replace(" (Westminster)", "", regex=False)

MAP_CITY = "London (Westminster)"
mapdf = df[df.city == MAP_CITY].copy()

# Web Mercator coords + dark basemap tiles, fetched once and reused
import contextily as cx
R = 6378137.0
mapdf["mx"] = np.radians(mapdf.lng) * R
mapdf["my"] = np.log(np.tan(np.pi / 4 + np.radians(mapdf.lat) / 2)) * R
MX0, MX1 = mapdf.mx.quantile(0.005), mapdf.mx.quantile(0.995)
MY0, MY1 = mapdf.my.quantile(0.005), mapdf.my.quantile(0.995)
BASEMAP, BM_EXT = cx.bounds2img(MX0, MY0, MX1, MY1,
                                source=cx.providers.CartoDB.DarkMatter)

total = len(df)
by_city = df.groupby("city_short").size().sort_values()
by_cat = df.groupby("cat").size().sort_values().tail(8)
monthly = df.groupby(["month", "city_short"]).size().unstack().fillna(0)
top_street = (mapdf[~mapdf.street.str.startswith("On or near Shopping")]
              .groupby("street").size().nlargest(1))
violent_share = (df.category == "violent-crime").mean() * 100
peak_month = df.groupby("month").size().idxmax()

CITY_COLORS = {c: col for c, col in zip(
    by_city.index[::-1],
    [YELLOW, RED, CYAN, "#BF5AF2", "#32D74B", "#FF9F0A", "#64D2FF", "#FF6482"])}


# ------------------------------------------------------------- helpers
def card(fig, x, y, w, h):
    fig.patches.append(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.012",
        transform=fig.transFigure, facecolor=CARD, edgecolor=EDGE,
        linewidth=0.8, zorder=-1))


def kicker(fig, x, y, num, label):
    fig.text(x, y, num, fontsize=9, color=YELLOW, fontweight="bold",
             family="Consolas", zorder=5)
    fig.text(x + 0.045, y, label.upper(), fontsize=9, color=MUTED,
             fontweight="bold", family="Consolas", zorder=5)


def fig_to_frame(fig):
    fig.canvas.draw()
    a = np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()
    plt.close(fig)
    return a


def hazard_stripe(fig, y, h=0.006):
    n = 40
    for i in range(n):
        fig.patches.append(plt.Rectangle(
            (i / n, y), 1 / n / 2, h, transform=fig.transFigure,
            facecolor=YELLOW if i % 2 == 0 else BG, zorder=6))


def build_poster(p_map=1.0, p_city=1.0, p_cat=1.0, p_trend=1.0, p_stat=1.0,
                 show=("map", "city", "cat", "trend", "stat")):
    """Draw the full poster; p_* in [0,1] animate each panel's reveal."""
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    fig.patch.set_facecolor(BG)

    # ---------------- header
    hazard_stripe(fig, 0.982)
    fig.text(0.05, 0.952, "UK CRIME", fontsize=27, fontweight="bold",
             color=TEXT)
    fig.text(0.315, 0.952, "HOTSPOTS", fontsize=27, fontweight="bold",
             color=RED)
    fig.text(0.05, 0.932, "12 months of street-level records  ·  8 city centres  ·  "
             "police.uk open data", fontsize=9, color=MUTED)
    fig.text(0.95, 0.952, f"{total:,}\nrecords", fontsize=11, color=YELLOW,
             ha="right", fontweight="bold", linespacing=1.3)

    # ---------------- panel 1: London hotspot map (left, tall)
    card(fig, 0.04, 0.545, 0.55, 0.36)
    kicker(fig, 0.06, 0.878, "01", "the hotspot map · central London")
    ax = fig.add_axes([0.05, 0.55, 0.53, 0.315])
    ax.set_facecolor(CARD)
    ax.imshow(BASEMAP, extent=(BM_EXT[0], BM_EXT[1], BM_EXT[2], BM_EXT[3]),
              interpolation="bilinear")
    if "map" in show:
        k = max(int(len(mapdf) * p_map), 50)
        sub = mapdf.iloc[:k]
        ax.hexbin(sub.mx, sub.my, gridsize=42, cmap=HEAT, mincnt=1,
                  bins="log", linewidths=0.1, alpha=0.55)
    ax.set_xlim(MX0, MX1)
    ax.set_ylim(MY0, MY1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.text(0.06, 0.556, "1-mile radius around Westminster. Brighter = more crimes.  "
             "Basemap (c) OpenStreetMap, (c) CARTO", fontsize=6.5, color=MUTED)

    # ---------------- panel 2: big stats (right column)
    card(fig, 0.62, 0.715, 0.34, 0.19)
    kicker(fig, 0.64, 0.878, "02", "headline numbers")
    t = p_stat if "stat" in show else 0
    fig.text(0.64, 0.835, f"{int(total * t):,}", fontsize=22, color=YELLOW,
             fontweight="bold")
    fig.text(0.64, 0.818, "street-level crime records", fontsize=8, color=MUTED)
    fig.text(0.64, 0.778, f"{violent_share * t:.0f}%", fontsize=22, color=RED,
             fontweight="bold")
    fig.text(0.64, 0.761, "of all records are violence", fontsize=8,
             color=MUTED)
    fig.text(0.64, 0.736, f"peak month: {peak_month}" if t > 0.6 else "",
             fontsize=8.5, color=CYAN, fontweight="bold")

    # ---------------- panel 3: city ranking (right column)
    card(fig, 0.62, 0.545, 0.34, 0.155)
    kicker(fig, 0.64, 0.683, "03", "city centre ranking")
    ax = fig.add_axes([0.70, 0.553, 0.245, 0.115])
    ax.set_facecolor(CARD)
    v = by_city.values * (p_city if "city" in show else 0)
    ax.barh(range(len(by_city)), v, height=0.62,
            color=[CITY_COLORS[c] for c in by_city.index])
    ax.set_yticks(range(len(by_city)))
    ax.set_yticklabels(by_city.index, fontsize=6.4)
    ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    for i, val in enumerate(v):
        if val > 0:
            ax.text(val + by_city.max() * 0.03, i, f"{val/1000:.1f}k",
                    va="center", fontsize=6, color=MUTED)
    ax.set_xlim(0, by_city.max() * 1.22)

    # ---------------- panel 4: what kind of crime (mid band)
    card(fig, 0.04, 0.335, 0.92, 0.185)
    kicker(fig, 0.06, 0.498, "04", "what kind of crime")
    ax = fig.add_axes([0.30, 0.345, 0.62, 0.145])
    ax.set_facecolor(CARD)
    v = by_cat.values * (p_cat if "cat" in show else 0)
    cols = [RED if c == "Violence" else YELLOW if c == "Shoplifting"
            else "#3E4C78" for c in by_cat.index]
    ax.barh(range(len(by_cat)), v, height=0.65, color=cols)
    ax.set_yticks(range(len(by_cat)))
    ax.set_yticklabels(by_cat.index, fontsize=7.5)
    ax.set_xticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    for i, val in enumerate(v):
        if val > 0:
            ax.text(val + by_cat.max() * 0.015, i, f"{int(val):,}",
                    va="center", fontsize=6.5, color=MUTED)
    ax.set_xlim(0, by_cat.max() * 1.18)

    # ---------------- panel 5: seasonality (lower band)
    card(fig, 0.04, 0.115, 0.92, 0.195)
    kicker(fig, 0.06, 0.288, "05", "the rhythm of the year")
    ax = fig.add_axes([0.10, 0.143, 0.83, 0.122])
    ax.set_facecolor(CARD)
    if "trend" in show and p_trend > 0:
        k = max(int(len(monthly) * p_trend), 2)
        x = range(k)
        for c in monthly.columns:
            ax.plot(x, monthly[c].iloc[:k], color=CITY_COLORS[c], lw=1.4,
                    alpha=0.9)
        if p_trend >= 1:
            # spread the right-edge labels so they never overlap
            finals = monthly.iloc[k - 1].sort_values()
            span = monthly.max().max() * 1.1
            ys, min_gap = [], span * 0.075
            for val in finals.values:
                y = val if not ys else max(val, ys[-1] + min_gap)
                ys.append(y)
            for (c, val), y in zip(finals.items(), ys):
                ax.annotate(c, (k - 1, y), fontsize=5.5,
                            color=CITY_COLORS[c], textcoords="offset points",
                            xytext=(5, -2))
    ax.set_xlim(0, len(monthly) + 1.8)
    ax.set_ylim(0, monthly.max().max() * 1.1)
    ax.set_xticks(range(len(monthly)))
    ax.set_xticklabels([m[2:] for m in monthly.index], fontsize=6, rotation=0)
    ax.tick_params(axis="y", labelsize=6)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", color=EDGE, lw=0.4)
    fig.text(0.06, 0.119, "Monthly records by city centre, May 2025 - Apr 2026",
             fontsize=7.5, color=MUTED)

    # ---------------- footer
    hazard_stripe(fig, 0.095)
    fig.text(0.05, 0.060, "HONEST CAVEAT", fontsize=7.5, color=YELLOW,
             fontweight="bold", family="Consolas")
    fig.text(0.05, 0.030, "Recorded crime is not all crime. Locations are anonymised to\n"
             "street level. Greater Manchester is absent: GMP stopped supplying data.",
             fontsize=7.5, color=MUTED, linespacing=1.5)
    fig.text(0.95, 0.045, "Ibtisam Ahmed Khan", fontsize=8.5, color=TEXT,
             ha="right", fontweight="bold")
    fig.text(0.95, 0.028, "Source: data.police.uk open API", fontsize=7,
             color=MUTED, ha="right")
    return fig


# ------------------------------------------------------------- animate
frames = []
ease = lambda t: t * t * (3 - 2 * t)  # smoothstep

# header + empty cards first
frames.append(fig_to_frame(build_poster(show=())))
frames.append(frames[-1])

# map points pour in
for t in np.linspace(0.12, 1, 6):
    frames.append(fig_to_frame(build_poster(p_map=ease(t), show=("map",))))

# stats count up
for t in np.linspace(0.25, 1, 4):
    frames.append(fig_to_frame(build_poster(p_stat=ease(t), show=("map", "stat"))))

# city bars grow
for t in np.linspace(0.25, 1, 4):
    frames.append(fig_to_frame(build_poster(p_city=ease(t),
                                            show=("map", "stat", "city"))))

# category bars grow
for t in np.linspace(0.25, 1, 4):
    frames.append(fig_to_frame(build_poster(p_cat=ease(t),
                                            show=("map", "stat", "city", "cat"))))

# trend lines draw
for t in np.linspace(0.15, 1, 6):
    frames.append(fig_to_frame(build_poster(p_trend=ease(t))))

# hold the finished poster
frames.extend([frames[-1]] * 10)

imageio.mimsave("gifs/uk_crime_hotspots_poster.gif", frames, fps=3, loop=0)
print("GIF frames:", len(frames))
try:
    imageio.mimsave("gifs/uk_crime_hotspots_poster.mp4", frames, fps=3)
    print("MP4 written")
except Exception as e:
    print("MP4 skipped:", e)

# static poster
fig = build_poster()
fig.savefig("charts/poster_static.png", dpi=150, facecolor=BG)
plt.close(fig)

print("\nTotal records:", f"{total:,}")
print("Violence share:", f"{violent_share:.1f}%")
print("Peak month:", peak_month)
print("\nBy city:\n", by_city.sort_values(ascending=False))
print("\nTop categories:\n", by_cat.sort_values(ascending=False))
print("\nBusiest street:", top_street.index[0], int(top_street.iloc[0]))
