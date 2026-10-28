"""Строит чертежи docs/img/build-front.svg и build-top.svg из model.py."""
import pathlib
import model as M

IMG = pathlib.Path(__file__).resolve().parents[1] / "img"
FONT = "'Segoe UI', Helvetica, Arial, sans-serif"
INK, MUTED = "#2B2118", "#6B5D4B"


def head(w, h, title, sub):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">',
            '<defs><marker id="a" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 Z" fill="{INK}"/></marker>'
            '<pattern id="soil" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="14" height="14" fill="#E9E1D0"/><line x1="0" y1="0" x2="0" y2="14" stroke="#CDBFA3" stroke-width="3"/></pattern></defs>',
            f'<rect width="{w}" height="{h}" rx="20" fill="#FFFBF2"/>',
            f'<text x="36" y="50" fill="{INK}" font-size="24" font-weight="700">{title}</text>',
            f'<text x="36" y="76" fill="{MUTED}" font-size="14">{sub}</text>']


def dim_h(o, x0, x1, y, text, ext_from=None):
    """Горизонтальный размер от x0 до x1 на уровне y (экранные координаты)."""
    if ext_from is not None:
        for x in (x0, x1):
            o.append(f'<line x1="{x:.1f}" y1="{ext_from:.1f}" x2="{x:.1f}" y2="{y + (6 if y > ext_from else -6):.1f}" stroke="{MUTED}" stroke-width="0.8"/>')
    o.append(f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" stroke="{INK}" stroke-width="1.1" marker-start="url(#a)" marker-end="url(#a)"/>')
    o.append(f'<rect x="{(x0 + x1) / 2 - 4 * len(text) - 6:.1f}" y="{y - 17:.1f}" width="{8 * len(text) + 12:.1f}" height="16" fill="#FFFBF2"/>')
    o.append(f'<text x="{(x0 + x1) / 2:.1f}" y="{y - 4:.1f}" fill="{INK}" font-size="14" font-weight="600" text-anchor="middle">{text}</text>')


def dim_v(o, y0, y1, x, text, ext_from=None, side="left"):
    if ext_from is not None:
        for y in (y0, y1):
            o.append(f'<line x1="{ext_from:.1f}" y1="{y:.1f}" x2="{x + (6 if x > ext_from else -6):.1f}" y2="{y:.1f}" stroke="{MUTED}" stroke-width="0.8"/>')
    o.append(f'<line x1="{x:.1f}" y1="{y0:.1f}" x2="{x:.1f}" y2="{y1:.1f}" stroke="{INK}" stroke-width="1.1" marker-start="url(#a)" marker-end="url(#a)"/>')
    cx, cy = x + (-8 if side == "left" else 8), (y0 + y1) / 2
    o.append(f'<text x="{cx:.1f}" y="{cy + 5:.1f}" fill="{INK}" font-size="14" font-weight="600" text-anchor="{"end" if side == "left" else "start"}">{text}</text>')


def callout(o, x, y, n, dx, dy):
    lx, ly = x + dx, y + dy
    o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{lx:.1f}" y2="{ly:.1f}" stroke="{INK}" stroke-width="1.2"/>')
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{INK}"/>')
    o.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="14" fill="#E8A317" stroke="{INK}" stroke-width="1.2"/>')
    o.append(f'<text x="{lx:.1f}" y="{ly + 5:.1f}" fill="{INK}" font-size="14" font-weight="700" text-anchor="middle">{n}</text>')


# ---------------------------------------------------------------- вид спереди
def front():
    W, H = 1200, 1340
    S = 0.48
    OX, OY = 560, 760           # экранные координаты точки x=0, z=0
    X = lambda x: OX + x * S
    Z = lambda z: OY - z * S
    o = head(W, H, "Вид спереди", "размеры в мм · улей показан условно — сними размеры своего · датчик L6G — по паспорту")
    # грунт
    o.append(f'<rect x="{X(-620):.1f}" y="{Z(0):.1f}" width="{1240 * S:.1f}" height="{(M.LEG_DOWN + 80) * S:.1f}" fill="url(#soil)"/>')
    o.append(f'<line x1="{X(-640):.1f}" y1="{Z(0):.1f}" x2="{X(640):.1f}" y2="{Z(0):.1f}" stroke="{INK}" stroke-width="1.6"/>')
    o.append(f'<text x="{X(-610):.1f}" y="{Z(0) + 20:.1f}" fill="{MUTED}" font-size="13">земля</text>')
    bx = [b for b in M.boxes if b["group"] not in ("ground",)]
    bx.sort(key=lambda b: -(b["y0"] + b["y1"]))   # дальние сначала
    for b in bx:
        if b["group"] in ("hive",):
            continue
        dashed = b["group"] == "strap"
        if dashed:
            continue
        o.append(f'<rect x="{X(b["x0"]):.1f}" y="{Z(b["z1"]):.1f}" width="{(b["x1"] - b["x0"]) * S:.1f}" height="{(b["z1"] - b["z0"]) * S:.1f}" '
                 f'fill="{b["color"]}" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.6"/>')
    # улей — контур
    hx, hy = M.HIVE_X / 2, M.HIVE_Y / 2
    hb = [b for b in M.boxes if b["group"] == "hive" and b["name"] != "Ножка дна"]
    for b in hb:
        o.append(f'<rect x="{X(b["x0"]):.1f}" y="{Z(b["z1"]):.1f}" width="{(b["x1"] - b["x0"]) * S:.1f}" height="{(b["z1"] - b["z0"]) * S:.1f}" '
                 f'fill="#F2D27A" fill-opacity="0.25" stroke="#C9A445" stroke-width="1.2" stroke-dasharray="6 4"/>')
    o.append(f'<text x="{X(0):.1f}" y="{Z(1000):.1f}" fill="#A8862E" font-size="16" font-weight="700" text-anchor="middle">улей (условно)</text>')
    # ремень
    for b in M.boxes:
        if b["group"] == "strap" and b["name"] == "Ремень" and b["y0"] < 0:
            o.append(f'<rect x="{X(b["x0"]):.1f}" y="{Z(b["z1"]):.1f}" width="{max((b["x1"] - b["x0"]) * S, 1.5):.1f}" height="{max((b["z1"] - b["z0"]) * S, 1.5):.1f}" fill="#E8701A" fill-opacity="0.75"/>')
    # размеры
    o.append(f'<line x1="{X(-300):.1f}" y1="{Z(M.z_deck):.1f}" x2="{X(-300):.1f}" y2="{Z(M.HEIGHT_TOP) - 34:.1f}" stroke="{MUTED}" stroke-width="0.8" stroke-dasharray="2 3"/>')
    o.append(f'<line x1="{X(300):.1f}" y1="{Z(M.z_deck):.1f}" x2="{X(300):.1f}" y2="{Z(M.HEIGHT_TOP) - 34:.1f}" stroke="{MUTED}" stroke-width="0.8" stroke-dasharray="2 3"/>')
    dim_h(o, X(-300), X(300), Z(M.HEIGHT_TOP) - 40, "600 настил")
    yb = Z(-M.LEG_DOWN) + 76
    dim_h(o, X(-325), X(325), yb, "650", ext_from=Z(-M.LEG_DOWN))
    dim_h(o, X(-275), X(275), yb + 34, "550 между осями ножек", ext_from=Z(-M.LEG_DOWN) + 20)
    xr = X(470)
    dim_v(o, Z(0), Z(M.z_frame0), xr, f"{M.z_frame0}", ext_from=X(175), side="right")
    dim_v(o, Z(0), Z(M.z_deck), xr + 70, f"≈{M.z_deck} настил", ext_from=X(300), side="right")
    dim_v(o, Z(0), Z(M.HEIGHT_TOP), xr + 210, f"≈{round(M.HEIGHT_TOP, -1):.0f} верх улья", ext_from=X(300), side="right")
    dim_v(o, Z(-M.LEG_DOWN), Z(0), xr, f"{M.SPIKE} пика в земле", ext_from=X(325), side="right")
    callout(o, X(-275), Z(-300), 10, -110, 0)
    callout(o, X(-275), Z(230), 1, -150, 30)
    callout(o, X(-200), Z(235), 2, -150, -40)
    callout(o, X(-60), Z(185), 3, -60, 110)
    callout(o, X(-110), Z(M.z_lt + 5), 4, -170, 10)
    callout(o, X(110), Z(M.z_ut0 - 5), 4, 120, 60)
    callout(o, X(20), Z((M.z_cell0 + M.z_cell1) / 2), 5, 30, 130)
    callout(o, X(220), Z(M.z_ut0 + 25), 6, 150, -20)
    callout(o, X(-220), Z(M.z_deck - 12), 7, -150, -80)
    callout(o, X(275), Z(M.z_leg + 15), 8, 150, 40)
    o.append(f'<text x="{X(-320):.1f}" y="{Z(900):.1f}" fill="{MUTED}" font-size="13" text-anchor="end">наклон к летку 1–2 см:</text>')
    o.append(f'<text x="{X(-320):.1f}" y="{Z(900) + 17:.1f}" fill="{MUTED}" font-size="13" text-anchor="end">передние ножки ниже задних</text>')
    o.append("</svg>")
    (IMG / "build-front.svg").write_text("\n".join(o), encoding="utf-8")


# ---------------------------------------------------------------- вид сверху
def top():
    W, H = 1200, 900
    S = 0.62
    OX, OY = 560, 460
    X = lambda x: OX + x * S
    Y = lambda y: OY - y * S
    o = head(W, H, "Вид сверху", "без улья · настил показан контуром · перед — внизу")
    bx = [b for b in M.boxes if b["group"] in ("base", "cell", "top")]
    bx.sort(key=lambda b: b["z1"])
    for b in bx:
        if b["name"].startswith("Ножка") and "мастике" in b["name"]:
            continue
        op = 0.55 if b["group"] == "top" else 1
        o.append(f'<rect x="{X(b["x0"]):.1f}" y="{Y(b["y1"]):.1f}" width="{(b["x1"] - b["x0"]) * S:.1f}" height="{(b["y1"] - b["y0"]) * S:.1f}" '
                 f'fill="{b["color"]}" fill-opacity="{op}" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.6"/>')
    # настил и улей
    o.append(f'<rect x="{X(-300):.1f}" y="{Y(300):.1f}" width="{600 * S:.1f}" height="{600 * S:.1f}" fill="#7A4E2D" fill-opacity="0.12" stroke="#7A4E2D" stroke-width="2" stroke-dasharray="10 6"/>')
    o.append(f'<rect x="{X(-M.HIVE_X / 2):.1f}" y="{Y(M.HIVE_Y / 2):.1f}" width="{M.HIVE_X * S:.1f}" height="{M.HIVE_Y * S:.1f}" fill="none" stroke="#C9A445" stroke-width="1.5" stroke-dasharray="3 5"/>')
    o.append(f'<text x="{X(0):.1f}" y="{Y(-M.HIVE_Y / 2) - 8:.1f}" fill="#A8862E" font-size="13" text-anchor="middle">контур дна улья (условно)</text>')
    # стрелка «перед / леток»
    o.append(f'<text x="{X(0):.1f}" y="{Y(-560):.1f}" fill="{MUTED}" font-size="14" font-weight="700" text-anchor="middle">▼ перед (леток)</text>')
    # размеры
    dim_v(o, Y(325), Y(-325), X(-500), "650", ext_from=X(-325))
    dim_v(o, Y(275), Y(-275), X(-420), "550", ext_from=X(-325))
    o.append(f'<text x="{X(-420) - 8:.1f}" y="{Y(0) + 24:.1f}" fill="{MUTED}" font-size="12" text-anchor="end">оси ножек</text>')
    dim_v(o, Y(300), Y(-300), X(470), "600 настил", ext_from=X(300), side="right")
    dim_h(o, X(-280), X(280), Y(325) - 50, "560 верхняя траверса", ext_from=Y(100))
    dim_h(o, X(-325), X(325), Y(-325) + 60, "650", ext_from=Y(-325))
    dim_h(o, X(-275), X(275), Y(-325) + 100, "550 между осями ножек", ext_from=Y(-275))
    callout(o, X(-275), Y(-275), 1, -110, 60)
    callout(o, X(200), Y(220), 2, -70, -55)
    callout(o, X(-130), Y(-90), 3, 150, 60)
    callout(o, X(0), Y(0), 5, 40, -110)
    callout(o, X(250), Y(70), 6, 120, -60)
    callout(o, X(-275), Y(275), 8, -90, -60)
    callout(o, X(360), Y(250), 9, 90, -40)
    o.append("</svg>")
    (IMG / "build-top.svg").write_text("\n".join(o), encoding="utf-8")


def export_js():
    import json
    (pathlib.Path(__file__).parent / "model.js").write_text(
        "const MODEL = " + json.dumps(dict(boxes=M.boxes), ensure_ascii=False) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    front()
    top()
    export_js()
    print("ok")
