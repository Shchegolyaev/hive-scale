"""Генерирует docs/img/chart.svg — пример графика на модельных (синтетических) данных."""
import math, random, pathlib

random.seed(7)
STEP = 10  # минут
N = 3 * 24 * 60 // STEP
SWARM_AT = (2 * 24 + 13) * 60 + 20  # день 3, 13:20

def flyers(h):  # доля лётных пчёл вне улья
    if 7 <= h < 19:
        x = (h - 7) / 12
        return math.sin(math.pi * x) ** 0.6
    return 0.0

w, ws, tin, tout = 52.0, [], [], []
nectar_total = 0.0
for i in range(N):
    m = i * STEP
    h = (m % 1440) / 60
    day = m // 1440
    if 9 <= h < 18:
        nectar_total += (1.5 + 0.4 * day) / (9 * 60 / STEP)
    elif h >= 21 or h < 6:
        nectar_total -= 0.35 / (9 * 60 / STEP)  # испарение ночью
    swarm = -2.3 * min(1, max(0, (m - SWARM_AT) / 20)) if m >= SWARM_AT else 0
    fly = -0.8 * flyers(h)
    ws.append(w + nectar_total + fly + swarm + random.gauss(0, 0.025))
    tout.append(13 + 9 * math.sin(math.pi * (h - 9) / 12))
    tin.append(34.6 + 0.25 * math.sin(math.pi * (h - 10) / 12) + random.gauss(0, 0.05) - (0.6 if SWARM_AT <= m < SWARM_AT + 90 else 0))

W, H = 1200, 540
L, R = 80, 1150
T1, B1 = 70, 330      # панель веса
T2, B2 = 410, 510     # панель температуры
x = lambda i: L + (R - L) * i / (N - 1)
wmin, wmax = 48.5, 55.5
yw = lambda v: B1 - (B1 - T1) * (v - wmin) / (wmax - wmin)
tmin, tmax = 0, 40
yt = lambda v: B2 - (B2 - T2) * (v - tmin) / (tmax - tmin)

def path(vals, fy):
    return "M" + " L".join(f"{x(i):.1f} {fy(v):.1f}" for i, v in enumerate(vals))

out = []
o = out.append
o(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="\'Segoe UI\', Helvetica, Arial, sans-serif">')
o('<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#E8A317" stop-opacity="0.28"/><stop offset="1" stop-color="#E8A317" stop-opacity="0"/></linearGradient></defs>')
o(f'<rect width="{W}" height="{H}" rx="20" fill="#FFFBF2"/>')
o(f'<text x="{L}" y="42" fill="#2B2118" font-size="19" font-weight="700">Вес улья, кг</text>')
o(f'<text x="{R}" y="42" fill="#8A7A62" font-size="13" text-anchor="end">модельные данные для иллюстрации · шаг 10 мин</text>')
# сетка
for v in range(49, 56):
    o(f'<line x1="{L}" y1="{yw(v):.1f}" x2="{R}" y2="{yw(v):.1f}" stroke="#2B2118" stroke-opacity="0.07"/>')
    o(f'<text x="{L-10}" y="{yw(v)+4:.1f}" fill="#8A7A62" font-size="12" text-anchor="end">{v}</text>')
# ночи
for d in range(3):
    for a, b in ((d * 1440 - 120, d * 1440 + 360), (d * 1440 + 1320, d * 1440 + 1440)):
        a, b = max(0, a), min(N * STEP - STEP, b)
        if b > a:
            o(f'<rect x="{x(a/STEP):.1f}" y="{T1}" width="{x(b/STEP)-x(a/STEP):.1f}" height="{B2-T1}" fill="#26476E" fill-opacity="0.05"/>')
for d, name in enumerate(["день 1", "день 2", "день 3"]):
    o(f'<text x="{x((d*1440+720)/STEP):.1f}" y="{B1+22}" fill="#8A7A62" font-size="13" text-anchor="middle">{name}</text>')
    o(f'<line x1="{x(d*1440/STEP):.1f}" y1="{T1}" x2="{x(d*1440/STEP):.1f}" y2="{B2}" stroke="#2B2118" stroke-opacity="0.12"/>')
p = path(ws, yw)
o(f'<path d="{p} L{x(N-1):.1f} {B1} L{L} {B1} Z" fill="url(#a)"/>')
o(f'<path d="{p}" fill="none" stroke="#E8A317" stroke-width="2.6" stroke-linejoin="round"/>')
# аннотации
i0 = (1440 + 9 * 60) // STEP
o(f'<text x="{x(i0):.1f}" y="{yw(ws[i0])+28:.1f}" fill="#6B5D4B" font-size="13" text-anchor="middle">утренний вылет</text>')
i1 = (1440 + 22 * 60) // STEP
o(f'<text x="{x(i1):.1f}" y="{yw(ws[i1])+28:.1f}" fill="#2E8B57" font-size="13" font-weight="700" text-anchor="middle">+ взяток за день</text>')
si = SWARM_AT // STEP
sx, sy = x(si + 1), yw(ws[si + 3])
o(f'<circle cx="{sx:.1f}" cy="{(yw(ws[si-1])+sy)/2:.1f}" r="20" fill="#D6452B" fill-opacity="0.14"/>')
bx, by = sx - 250, yw(50.9)
o(f'<line x1="{sx:.1f}" y1="{(yw(ws[si-1])+sy)/2+20:.1f}" x2="{bx+150:.1f}" y2="{by:.1f}" stroke="#D6452B" stroke-width="1.6"/>')
o(f'<rect x="{bx:.1f}" y="{by:.1f}" width="190" height="48" rx="10" fill="#D6452B"/>')
o(f'<text x="{bx+95:.1f}" y="{by+21:.1f}" fill="#FFF" font-size="16" font-weight="700" text-anchor="middle">РОЙ · −2,3 кг</text>')
o(f'<text x="{bx+95:.1f}" y="{by+39:.1f}" fill="#FFE1D9" font-size="12.5" text-anchor="middle">тревога в Telegram, 13:20</text>')
# температуры
o(f'<text x="{L}" y="{T2-14}" fill="#2B2118" font-size="16" font-weight="700">Температура, °C</text>')
o(f'<text x="{L+150}" y="{T2-14}" fill="#D6452B" font-size="13" font-weight="700">● гнездо (t1)</text>')
o(f'<text x="{L+260}" y="{T2-14}" fill="#2F7BB8" font-size="13" font-weight="700">● снаружи</text>')
for v in (0, 20, 40):
    o(f'<line x1="{L}" y1="{yt(v):.1f}" x2="{R}" y2="{yt(v):.1f}" stroke="#2B2118" stroke-opacity="0.07"/>')
    o(f'<text x="{L-10}" y="{yt(v)+4:.1f}" fill="#8A7A62" font-size="12" text-anchor="end">{v}</text>')
o(f'<path d="{path(tout, yt)}" fill="none" stroke="#2F7BB8" stroke-width="2"/>')
o(f'<path d="{path(tin, yt)}" fill="none" stroke="#D6452B" stroke-width="2"/>')
o('</svg>')
pathlib.Path(__file__).resolve().parents[1].joinpath("img/chart.svg").write_text("\n".join(out), encoding="utf-8")
print("ok")
