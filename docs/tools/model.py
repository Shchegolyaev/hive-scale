"""Модель платформы весов: список параллелепипедов в миллиметрах.

Оси: X — влево/вправо, Y — назад (+) / вперёд (−), Z — вверх. Z=0 — верх щебёночной подушки.
Из этой модели строятся вид спереди, вид сверху (build_drawings.py) и 3D-рендер (render3d.html).
"""

# Цвета
WOOD = "#B9824A"
STEEL = "#8D99A6"
STEEL_D = "#4F5862"
ALU = "#C9CED4"
PLY = "#7A4E2D"
SLAB = "#B9B4AA"
GRAVEL = "#CFC8BA"
RUST = "#8B4A2B"
HIVE = "#F2D27A"
HIVE_D = "#E3BE5A"
ROOF = "#C9A445"
STRAP = "#E8701A"
BITUMEN = "#2E2A26"
WOOD_L = "#C69159"
BOX = "#E6E9EC"

# Ключевые размеры
DECK = 600            # настил 600×600 (предел платформы для L6G)
DECK_T = 21           # фанера 21 мм
SLEEPER_X = 250       # оси лежней (над ними — крайние рёбра и стоп-болты)
SLEEPER_L = 1000
LEG_X = 325           # оси ножек: лежни прикручены к их внутренним граням
LEG_Y = 430
SPACER = 10           # стальная проставка
CELL_L, CELL_W, CELL_H = 300, 70, 70   # условно; реальные — по паспорту датчика
RIB = 50              # брус 50×50
RIB_L = 700
LEG_DOWN = 600        # ножка в земле (вариант «вкопать»)
STOP_GAP = 3          # зазор стоп-болтов (дерево «дышит» — больше, чем у стали)

z_sleeper = 240                                # верх ножек = верх лежней
z_frame0 = z_sleeper - 150                     # 90 — низ лежней (доска 50×150 на ребро)
z_lt = z_sleeper                               # средняя поперечина — заподлицо с лежнями
z_cell0 = z_lt + SPACER                        # 250
z_cell1 = z_cell0 + CELL_H                     # 320
z_ut0 = z_cell1 + SPACER                       # 330
z_ut1 = z_ut0 + 100                            # 430
z_rib1 = z_ut1 + RIB                           # 480
z_deck = z_rib1 + DECK_T                       # 501

HIVE_X, HIVE_Y = 530, 550   # условные габариты улья; измерь свой

boxes = []


def box(name, x0, x1, y0, y1, z0, z1, color, group="base", num=None):
    boxes.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1,
                      color=color, group=group, num=num))


# Грунт
box("Грунт", -650, 650, -650, 650, -LEG_DOWN - 100, 0, GRAVEL, "ground")

# Ножки — брус 100×100, лежни — доска 50×150 на ребро, прикручены к внутренним граням ножек
for sx in (-1, 1):
    c = sx * LEG_X
    for sy in (-1, 1):
        y = sy * LEG_Y
        box("Ножка: брус 100×100, часть в земле — в мастике", c - 50, c + 50, y - 50, y + 50, -LEG_DOWN, 50, BITUMEN, "base", 1)
        box("Ножка: брус 100×100", c - 50, c + 50, y - 50, y + 50, 50, z_sleeper, WOOD, "base", 1)
    l0, l1 = sorted((sx * (SLEEPER_X - 25), sx * (SLEEPER_X + 25)))
    box("Лежень: доска 50×150×1000", l0, l1, -SLEEPER_L / 2, SLEEPER_L / 2, z_frame0, z_sleeper, WOOD_L, "base", 2)
for sy in (-1, 1):
    y0, y1 = sorted((sy * (SLEEPER_L / 2 - 50), sy * SLEEPER_L / 2))
    box("Крайняя поперечина: доска 50×150×450", -225, 225, y0, y1, z_frame0, z_sleeper, WOOD, "base", 3)
for y0, y1 in ((-50, 0), (0, 50)):
    box("Средняя поперечина: 2 доски 50×100×450", -225, 225, y0, y1, z_sleeper - 100, z_sleeper, WOOD, "base", 4)

# Датчик и проставки
box("Проставка, сталь 10 мм (неподвижный конец)", -CELL_L / 2, -CELL_L / 2 + 80, -CELL_W / 2, CELL_W / 2, z_lt, z_cell0, STEEL_D, "base", 5)
box("Датчик L6G 200 кг", -CELL_L / 2, CELL_L / 2, -CELL_W / 2, CELL_W / 2, z_cell0, z_cell1, ALU, "cell", 6)
box("Проставка, сталь 10 мм (грузовой конец)", CELL_L / 2 - 80, CELL_L / 2, -CELL_W / 2, CELL_W / 2, z_cell1, z_ut0, STEEL_D, "top", 5)
# Верхняя траверса — две доски 50×100
for y0, y1 in ((-50, 0), (0, 50)):
    box("Верхняя траверса: 2 доски 50×100×560", -280, 280, y0, y1, z_ut0, z_ut1, WOOD_L, "top", 7)
# Рёбра
for cx in (-SLEEPER_X, 0, SLEEPER_X):
    box("Ребро: брус 50×50×700", cx - RIB / 2, cx + RIB / 2, -RIB_L / 2, RIB_L / 2, z_ut1, z_rib1, WOOD, "top", 8)
# Настил
box("Настил: ламинированная фанера 21 мм, 600×600", -DECK / 2, DECK / 2, -DECK / 2, DECK / 2, z_rib1, z_deck, PLY, "deck", 9)

# Стоп-болты: в верхнюю кромку лежней под крайними рёбрами
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * SLEEPER_X, sy * 250
        box("Стоп-болт: шуруп-шпилька М10", x - 5, x + 5, y - 5, y + 5, z_sleeper, z_rib1 - STOP_GAP - 8, STEEL_D, "base", 10)
        box("Стоп-болт: гайка", x - 9, x + 9, y - 9, y + 9, z_rib1 - STOP_GAP - 8, z_rib1 - STOP_GAP, "#3A424A", "base", 10)

# Г-упоры: стойка 50×50 на внутренней грани лежня, полка-доска нависает над концом
# крайнего ребра с зазором 5 мм сверху и 10 мм по торцу
for sx in (-1, 1):
    for sy in (-1, 1):
        e = RIB_L / 2
        post = sorted((sy * (e + 10), sy * (e + 60)))
        hook = sorted((sy * (e - 25), sy * (e + 60)))
        px = sorted((sx * 175, sx * 225))
        hk = sorted((sx * 175, sx * 280))
        box("Г-упор: стойка, брус 50×50", px[0], px[1], *post, z_frame0 + 10, z_rib1 + 30, WOOD, "base", 11)
        box("Г-упор: полка, доска 25 мм", hk[0], hk[1], *hook, z_rib1 + 5, z_rib1 + 30, WOOD, "base", 11)

# Коробка электроники — на неподвижной части (наружная грань лежня между ножками)
box("Корпус электроники IP65", 275, 345, -80, 80, 60, 220, BOX, "base", 12)

# Улей (условные размеры)
hx, hy = HIVE_X / 2, HIVE_Y / 2
for lx in (-hx + 40, 0, hx - 40):
    for ly in (-hy + 40, hy - 40):
        box("Ножка дна", lx - 15, lx + 15, ly - 15, ly + 15, z_deck, z_deck + 20, HIVE_D, "hive")
z = z_deck + 20
box("Дно", -hx, hx, -hy, hy, z, z + 60, HIVE_D, "hive"); z += 60
box("Корпус", -hx, hx, -hy, hy, z, z + 330, HIVE, "hive"); z += 330
box("Корпус", -hx, hx, -hy, hy, z, z + 330, HIVE, "hive"); z += 330
box("Крыша", -hx - 10, hx + 10, -hy - 10, hy + 10, z, z + 80, ROOF, "hive"); z_top = z + 80

# Ремни (огибают улей и настил, проходят под настилом между рёбрами)
for cx in (-130, 130):
    x0, x1 = cx - 13, cx + 13
    for s in (-1, 1):
        y0, y1 = sorted((s * (hy + 3), s * hy))
        box("Ремень", x0, x1, y0, y1, z_deck, z_top - 80, STRAP, "strap")
        y0, y1 = sorted((s * (hy + 13), s * (hy + 10)))
        box("Ремень", x0, x1, y0, y1, z_top - 80, z_top + 3, STRAP, "strap")
        y0, y1 = sorted((s * (DECK / 2 + 3), s * DECK / 2))
        box("Ремень", x0, x1, y0, y1, z_rib1 - 3, z_deck, STRAP, "strap")
    box("Ремень", x0, x1, -hy - 13, hy + 13, z_top, z_top + 3, STRAP, "strap")
    box("Ремень", x0, x1, -DECK / 2, DECK / 2, z_rib1 - 3, z_rib1, STRAP, "strap")
    box("Храповик", x0 - 5, x1 + 5, -hy - 9, -hy - 3, z_deck + 250, z_deck + 300, "#3A424A", "strap")

HEIGHT_TOP = z_top
