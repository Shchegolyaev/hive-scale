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
SLEEPER_GAP = 500     # между осями лежней
SLEEPER_L = 1000
BEAM = 100            # брус 100×100
SPACER = 10           # стальная проставка
CELL_L, CELL_W, CELL_H = 300, 70, 70   # условно; реальные — по паспорту датчика
RIB = 50              # брус 50×50
RIB_L = 700
LEG_UP = 140          # ножка над землёй
LEG_DOWN = 600        # ножка в земле (вариант «вкопать»)
LEG_Y = 430           # оси ножек по Y
STOP_GAP = 3          # зазор стоп-болтов (дерево «дышит» — больше, чем у стали)

z_frame0 = LEG_UP                              # 150 — низ рамы
z_sleeper = z_frame0 + BEAM                    # 250 — верх рамы
z_lt = z_sleeper                               # средняя поперечина — заподлицо с лежнями
z_cell0 = z_lt + SPACER                        # 260
z_cell1 = z_cell0 + CELL_H                     # 330
z_ut0 = z_cell1 + SPACER                       # 340
z_ut1 = z_ut0 + BEAM                           # 440
z_rib1 = z_ut1 + RIB                           # 490
z_deck = z_rib1 + DECK_T                       # 511

HIVE_X, HIVE_Y = 530, 550   # условные габариты улья; измерь свой

boxes = []


def box(name, x0, x1, y0, y1, z0, z1, color, group="base", num=None):
    boxes.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1,
                      color=color, group=group, num=num))


# Грунт
box("Грунт", -600, 600, -650, 650, -LEG_DOWN - 100, 0, GRAVEL, "ground")

# Рама: 4 ножки, 2 лежня, 3 поперечины — всё брус 100×100
for sx in (-1, 1):
    c = sx * SLEEPER_GAP / 2
    for sy in (-1, 1):
        y = sy * LEG_Y
        box("Ножка: брус 100×100, часть в земле — в мастике", c - 50, c + 50, y - 50, y + 50, -LEG_DOWN, 50, BITUMEN, "base", 1)
        box("Ножка: брус 100×100", c - 50, c + 50, y - 50, y + 50, 50, z_frame0, WOOD, "base", 1)
    box("Лежень: брус 100×100×1000", c - 50, c + 50, -SLEEPER_L / 2, SLEEPER_L / 2, z_frame0, z_sleeper, WOOD, "base", 2)
for sy in (-1, 1):
    y0, y1 = sorted((sy * (SLEEPER_L / 2 - 100), sy * SLEEPER_L / 2))
    box("Крайняя поперечина: брус 100×100×400", -200, 200, y0, y1, z_frame0, z_sleeper, WOOD_L, "base", 3)
box("Средняя поперечина (несёт датчик): брус 100×100×400", -200, 200, -50, 50, z_frame0, z_sleeper, WOOD_L, "base", 4)

# Датчик и проставки
box("Проставка, сталь 10 мм (неподвижный конец)", -CELL_L / 2, -CELL_L / 2 + 80, -CELL_W / 2, CELL_W / 2, z_lt, z_cell0, STEEL_D, "base", 5)
box("Датчик L6G 200 кг", -CELL_L / 2, CELL_L / 2, -CELL_W / 2, CELL_W / 2, z_cell0, z_cell1, ALU, "cell", 6)
box("Проставка, сталь 10 мм (грузовой конец)", CELL_L / 2 - 80, CELL_L / 2, -CELL_W / 2, CELL_W / 2, z_cell1, z_ut0, STEEL_D, "top", 5)
# Верхняя траверса
box("Верхняя траверса: брус 100×100×560", -280, 280, -50, 50, z_ut0, z_ut1, WOOD_L, "top", 7)
# Рёбра
for cx in (-250, 0, 250):
    box("Ребро: брус 50×50×700", cx - RIB / 2, cx + RIB / 2, -RIB_L / 2, RIB_L / 2, z_ut1, z_rib1, WOOD, "top", 8)
# Настил
box("Настил: ламинированная фанера 21 мм, 600×600", -DECK / 2, DECK / 2, -DECK / 2, DECK / 2, z_rib1, z_deck, PLY, "deck", 9)

# Стоп-болты под крайними рёбрами
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * 250, sy * 250
        box("Стоп-болт: шуруп-шпилька М10", x - 5, x + 5, y - 5, y + 5, z_sleeper, z_rib1 - STOP_GAP - 8, STEEL_D, "base", 10)
        box("Стоп-болт: гайка", x - 9, x + 9, y - 9, y + 9, z_rib1 - STOP_GAP - 8, z_rib1 - STOP_GAP, "#3A424A", "base", 10)

# Г-упоры из дерева: стойка 50×50 на наружной грани лежня, полка-доска нависает над концом
# крайнего ребра с зазором 5 мм сверху и 10 мм по торцу
for sx in (-1, 1):
    for sy in (-1, 1):
        e = RIB_L / 2
        post = sorted((sy * (e + 10), sy * (e + 60)))
        hook = sorted((sy * (e - 25), sy * (e + 60)))
        px = sorted((sx * 300, sx * 350))
        hk = sorted((sx * 225, sx * 350))
        box("Г-упор: стойка, брус 50×50", px[0], px[1], *post, z_frame0 + 10, z_rib1 + 30, WOOD_L, "base", 11)
        box("Г-упор: полка, доска 25 мм", hk[0], hk[1], *hook, z_rib1 + 5, z_rib1 + 30, WOOD_L, "base", 11)

# Коробка электроники — на неподвижной части
box("Корпус электроники IP65", 300, 370, -80, 80, z_frame0 - 40, z_frame0 + 120, BOX, "base", 12)

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
