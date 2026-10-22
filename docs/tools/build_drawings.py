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
    W, H = 1200, 1290
    S = 0.48
    OX, OY = 560, 840           # экранные координаты точки x=0, z=0
    X = lambda x: OX + x * S
    Z = lambda z: OY - z * S
    o = head(W, H, "Вид спереди", "размеры в мм · улей показан условно — сними размеры своего · датчик L6G — по паспорту")
    # грунт
    o.append(f'<rect x="{X(-620):.1f}" y="{Z(0):.1f}" width="{1240 * S:.1f}" height="{(M.LEG_DOWN + 80) * S:.1f}" fill="url(#soil)"/>')
    o.append(f'<line x1="{X(-640):.1f}" y1="{Z(0):.1f}" x2="{X(640):.1f}" y2="{Z(0):.1f}" stroke="{INK}" stroke-width="1.6"/>')
    o.append(f'<text x="{X(-610):.1f}" y="{Z(0) + 20:.1f}" fill="{MUTED}" font-size="13">земля</text>')
    # гравийная подушка под ножками
    for sx in (-1, 1):
        c = sx * 250
        o.append(f'<rect x="{X(c - 90):.1f}" y="{Z(-M.LEG_DOWN):.1f}" width="{180 * S:.1f}" height="{100 * S:.1f}" fill="#BDB6A6" stroke="{MUTED}" stroke-dasharray="3 3"/>')
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
    for cx in (-130, 130):
        o.append(f'<rect x="{X(cx - 13):.1f}" y="{Z(M.HEIGHT_TOP + 3):.1f}" width="{26 * S:.1f}" height="{(M.HEIGHT_TOP + 3 - M.z_rib1 + 3) * S:.1f}" fill="#E8701A" fill-opacity="0.55"/>')
    # размеры
    top = Z(M.z_deck)
    dim_h(o, X(-300), X(300), Z(M.HEIGHT_TOP) - 40, "600 настил", ext_from=None)
    o.append(f'<line x1="{X(-300):.1f}" y1="{top:.1f}" x2="{X(-300):.1f}" y2="{Z(M.HEIGHT_TOP) - 34:.1f}" stroke="{MUTED}" stroke-width="0.8" stroke-dasharray="2 3"/>')
    o.append(f'<line x1="{X(300):.1f}" y1="{top:.1f}" x2="{X(300):.1f}" y2="{Z(M.HEIGHT_TOP) - 34:.1f}" stroke="{MUTED}" stroke-width="0.8" stroke-dasharray="2 3"/>')
    yb = Z(-M.LEG_DOWN) + 76
    dim_h(o, X(-300), X(300), yb, "600", ext_from=Z(-M.LEG_DOWN))
    dim_h(o, X(-250), X(250), yb + 34, "500 между осями ножек", ext_from=Z(-M.LEG_DOWN) + 20)
    # высоты справа
    xr = X(450)
    dim_v(o, Z(0), Z(M.z_frame0), xr, f"{M.z_frame0}", ext_from=X(300), side="right")
    dim_v(o, Z(0), Z(M.z_sleeper), xr + 70, f"{M.z_sleeper}", ext_from=X(300), side="right")
    dim_v(o, Z(0), Z(M.z_deck), xr + 140, f"≈{M.z_deck} настил", ext_from=X(300), side="right")
    dim_v(o, Z(0), Z(M.HEIGHT_TOP), xr + 270, f"≈{round(M.HEIGHT_TOP, -1):.0f} верх улья", ext_from=X(300), side="right")
    dim_v(o, Z(-M.LEG_DOWN), Z(0), xr, f"{M.LEG_DOWN} в земле", ext_from=X(300), side="right")
    # выноски
    callout(o, X(-250), Z(-250), 1, -150, 0)
    callout(o, X(-250), Z(200), 2, -150, 0)
    callout(o, X(-300), Z(M.z_lt - 30), 4, -100, -20)
    callout(o, X(-110), Z(M.z_cell0 - 5), 5, -120, 40)
    callout(o, X(0), Z((M.z_cell0 + M.z_cell1) / 2), 6, -50, 100)
    callout(o, X(110), Z(M.z_ut0 - 5), 5, 60, 80)
    callout(o, X(200), Z(M.z_ut0 + 30), 7, 110, 40)
    callout(o, X(-250), Z(M.z_rib1 - 10), 8, -200, -60)
    callout(o, X(-200), Z(M.z_deck - 10), 9, -150, -100)
    callout(o, X(335), Z(M.z_frame0 + 20), 12, -10, 150)
    callout(o, X(320), Z(M.z_sleeper + 120), 11, 110, 30)
    # зазоры
    o.append(f'<text x="{X(-370):.1f}" y="{Z(M.z_cell1) - 28:.1f}" fill="{MUTED}" font-size="12.5" text-anchor="end">зазор ≥ 5 мм между</text>')
    o.append(f'<text x="{X(-370):.1f}" y="{Z(M.z_cell1) - 13:.1f}" fill="{MUTED}" font-size="12.5" text-anchor="end">датчиком и траверсами</text>')
    o.append("</svg>")
    (IMG / "build-front.svg").write_text("\n".join(o), encoding="utf-8")


# ---------------------------------------------------------------- вид сверху
def top():
    W, H = 1200, 1010
    S = 0.62
    OX, OY = 560, 520
    X = lambda x: OX + x * S
    Y = lambda y: OY - y * S
    o = head(W, H, "Вид сверху", "без улья · настил показан контуром · перед — внизу")
    bx = [b for b in M.boxes if b["group"] in ("base", "cell", "top")]
    bx.sort(key=lambda b: b["z1"])
    for b in bx:
        if b["name"].startswith("Ножка"):
            continue
        op = 0.9 if b["group"] == "top" else 1
        o.append(f'<rect x="{X(b["x0"]):.1f}" y="{Y(b["y1"]):.1f}" width="{(b["x1"] - b["x0"]) * S:.1f}" height="{(b["y1"] - b["y0"]) * S:.1f}" '
                 f'fill="{b["color"]}" fill-opacity="{op}" stroke="{INK}" stroke-width="0.8" stroke-opacity="0.6"/>')
    # ножки — пунктиром (под лежнями)
    for b in M.boxes:
        if b["name"] == "Ножка: брус 100×100":
            o.append(f'<rect x="{X(b["x0"]):.1f}" y="{Y(b["y1"]):.1f}" width="{100 * S:.1f}" height="{100 * S:.1f}" fill="none" stroke="{INK}" stroke-width="1.4" stroke-dasharray="5 4"/>')
            o.append(f'<line x1="{X(b["x0"]):.1f}" y1="{Y(b["y1"]):.1f}" x2="{X(b["x1"]):.1f}" y2="{Y(b["y0"]):.1f}" stroke="{INK}" stroke-width="0.8" stroke-dasharray="3 3"/>')
            o.append(f'<line x1="{X(b["x1"]):.1f}" y1="{Y(b["y1"]):.1f}" x2="{X(b["x0"]):.1f}" y2="{Y(b["y0"]):.1f}" stroke="{INK}" stroke-width="0.8" stroke-dasharray="3 3"/>')
    # настил и улей
    o.append(f'<rect x="{X(-300):.1f}" y="{Y(300):.1f}" width="{600 * S:.1f}" height="{600 * S:.1f}" fill="#7A4E2D" fill-opacity="0.12" stroke="#7A4E2D" stroke-width="2" stroke-dasharray="10 6"/>')
    o.append(f'<rect x="{X(-M.HIVE_X / 2):.1f}" y="{Y(M.HIVE_Y / 2):.1f}" width="{M.HIVE_X * S:.1f}" height="{M.HIVE_Y * S:.1f}" fill="none" stroke="#C9A445" stroke-width="1.5" stroke-dasharray="3 5"/>')
    o.append(f'<text x="{X(0):.1f}" y="{Y(-M.HIVE_Y / 2) - 8:.1f}" fill="#A8862E" font-size="13" text-anchor="middle">контур дна улья (условно)</text>')
    # стрелка «перед / леток»
    o.append(f'<text x="{X(0):.1f}" y="{Y(-560):.1f}" fill="{MUTED}" font-size="14" font-weight="700" text-anchor="middle">▼ перед (леток)</text>')
    # размеры
    dim_v(o, Y(500), Y(-500), X(-470), "1000", ext_from=X(-300))
    dim_v(o, Y(430), Y(-430), X(-400), "860", ext_from=X(-300))
    o.append(f'<text x="{X(-400) - 8:.1f}" y="{Y(0) + 24:.1f}" fill="{MUTED}" font-size="12" text-anchor="end">оси ножек</text>')
    dim_v(o, Y(350), Y(-350), X(600), "700 рёбра", ext_from=X(270), side="right")
    dim_v(o, Y(300), Y(-300), X(520), "600", ext_from=X(300), side="right")
    dim_h(o, X(-250), X(0), Y(500) - 40, "250", ext_from=Y(350))
    dim_h(o, X(0), X(250), Y(500) - 40, "250", ext_from=Y(350))
    dim_h(o, X(-300), X(300), Y(-500) + 60, "600 по наружным граням лежней", ext_from=Y(-500))
    dim_h(o, X(-350), X(350), Y(-500) + 100, "700 нижняя траверса", ext_from=Y(-20))
    # выноски
    callout(o, X(-250), Y(-430), 1, -110, 40)
    callout(o, X(250), Y(150), 2, -90, -40)
    callout(o, X(-100), Y(470), 3, -60, -50)
    callout(o, X(-330), Y(0), 4, -70, -40)
    callout(o, X(0), Y(28), 6, 30, -70)
    callout(o, X(140), Y(0), 7, 60, 60)
    callout(o, X(0), Y(-330), 8, 50, 20)
    callout(o, X(250), Y(-250), 10, -90, 20)
    callout(o, X(320), Y(-363), 11, 70, 50)
    callout(o, X(370), Y(60), 12, 60, -110)
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
