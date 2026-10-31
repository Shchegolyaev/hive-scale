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
WOOD_L = "#C69159"
BOX = "#E6E9EC"

# Ключевые размеры
DECK = 600            # настил 600×600 (предел платформы для L6G)
DECK_T = 27           # ламинированная фанера 27 мм — несёт улей без рёбер
LEG = 275             # оси ножек: квадрат 550×550, ножки под углами настила
SPIKE = 900           # пика забивной опоры
CUP = 150             # высота стакана опоры над землёй
LEG_DOWN = SPIKE
SPACER = 10           # стальная проставка
CELL_L, CELL_W, CELL_H = 174, 65, 60   # Zemic L6G 300 кг, по паспорту; сверь со своим
BOARD = 50            # доска 50×100 плашмя: 100 шириной, 50 высотой
BOARD_W = 100
STOP_GAP = 3          # зазор стоп-болтов (дерево «дышит» — больше, чем у стали)

z_frame0 = CUP + 10                            # 160 — низ лежней: на 1 см выше стакана опоры
z_sleeper = z_frame0 + 100                     # 260 — верх лежней (доска 50×100 на ребро)
z_lt = z_frame0 + BOARD                        # 210 — верх средней поперечины
z_cell0 = z_lt + SPACER                        # 220
z_cell1 = z_cell0 + CELL_H                     # 280
z_ut0 = z_cell1 + SPACER                       # 290
z_ut1 = z_ut0 + BOARD                          # 340 — верх верхней траверсы = низ настила
z_deck = z_ut1 + DECK_T                        # 367
z_leg = z_ut1 - 40                             # 300 — верх ножек; в торце — стоп-болт

HIVE_X, HIVE_Y = 530, 550   # условные габариты улья; измерь свой

boxes = []


def box(name, x0, x1, y0, y1, z0, z1, color, group="base", num=None):
    boxes.append(dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z1,
                      color=color, group=group, num=num))


# Грунт
box("Грунт", -600, 600, -600, 600, -SPIKE - 100, 0, GRAVEL, "ground")

# 1. Забивные опоры и ножки — брус 100×100 в стакане опоры, дерево не касается земли
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * LEG, sy * LEG
        box("Забивная опора 100×100: пика", x - 20, x + 20, y - 20, y + 20, -SPIKE, 0, STEEL, "base", 10)
        box("Забивная опора 100×100: пластина", x - 58, x + 58, y - 58, y + 58, 0, 3, STEEL, "base", 10)
        for (a0, a1, b0, b1) in ((-52, -50, -52, 52), (50, 52, -52, 52), (-50, 50, -52, -50), (-50, 50, 50, 52)):
            box("Забивная опора 100×100: стакан", x + a0, x + a1, y + b0, y + b1, 3, CUP, STEEL, "base", 10)
        box("Ножка: брус 100×100", x - 50, x + 50, y - 50, y + 50, 3, z_leg, WOOD, "base", 1)

# 2. Лежни — доска 50×100 на ребро, на внутренних гранях ножек
for sx in (-1, 1):
    l0, l1 = sorted((sx * (LEG - 100), sx * (LEG - 50)))
    box("Лежень: доска 50×100×650", l0, l1, -LEG - 50, LEG + 50, z_frame0, z_sleeper, WOOD_L, "base", 2)

# 3. Средняя поперечина — доска 50×100 плашмя между лежнями
box("Средняя поперечина: доска 50×100×350 плашмя", -(LEG - 100), LEG - 100, -BOARD_W / 2, BOARD_W / 2, z_frame0, z_lt, WOOD, "base", 3)

# 4–5. Датчик и проставки
box("Проставка, сталь 10 мм (неподвижный конец)", -CELL_L / 2, -CELL_L / 2 + 80, -CELL_W / 2, CELL_W / 2, z_lt, z_cell0, STEEL_D, "base", 4)
box("Датчик L6G 300 кг", -CELL_L / 2, CELL_L / 2, -CELL_W / 2, CELL_W / 2, z_cell0, z_cell1, ALU, "cell", 5)
box("Проставка, сталь 10 мм (грузовой конец)", CELL_L / 2 - 80, CELL_L / 2, -CELL_W / 2, CELL_W / 2, z_cell1, z_ut0, STEEL_D, "top", 4)

# 6. Верхняя траверса — доска 50×100 плашмя
box("Верхняя траверса: доска 50×100×560 плашмя", -280, 280, -BOARD_W / 2, BOARD_W / 2, z_ut0, z_ut1, WOOD_L, "top", 6)

# 7. Настил
box("Настил: ламинированная фанера 27 мм, 600×600", -DECK / 2, DECK / 2, -DECK / 2, DECK / 2, z_ut1, z_deck, PLY, "deck", 7)

# 8. Стоп-болты в торцах ножек
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * LEG, sy * LEG
        box("Стоп-болт: шуруп-шпилька М10", x - 5, x + 5, y - 5, y + 5, z_leg, z_ut1 - STOP_GAP - 8, STEEL_D, "base", 8)
        box("Стоп-болт: гайка", x - 9, x + 9, y - 9, y + 9, z_ut1 - STOP_GAP - 8, z_ut1 - STOP_GAP, "#3A424A", "base", 8)

# 9. Коробка электроники — на наружной грани задней правой ножки (неподвижная часть)
box("Корпус электроники IP65", LEG + 50, LEG + 120, LEG - 80, LEG + 80, CUP + 10, CUP + 170, BOX, "base", 9)

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

# Ремни — вдоль X: через крышу, по бокам улья и по низу настила (в стороне от траверсы)
z_top_roof = z_top
for cy in (-150, 150):
    y0, y1 = cy - 13, cy + 13
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (hx + 3), sx * hx))
        box("Ремень", x0, x1, y0, y1, z_deck, z_top - 80, STRAP, "strap")
        x0, x1 = sorted((sx * (hx + 13), sx * (hx + 10)))
        box("Ремень", x0, x1, y0, y1, z_top - 80, z_top + 3, STRAP, "strap")
        x0, x1 = sorted((sx * (DECK / 2 + 3), sx * DECK / 2))
        box("Ремень", x0, x1, y0, y1, z_ut1 - 3, z_deck, STRAP, "strap")
        x0, x1 = sorted((sx * hx, sx * DECK / 2 + 3 * sx))
        box("Ремень", x0, x1, y0, y1, z_deck, z_deck + 3, STRAP, "strap")
    box("Ремень", -hx - 13, hx + 13, y0, y1, z_top, z_top + 3, STRAP, "strap")
    box("Ремень", -DECK / 2 - 3, DECK / 2 + 3, y0, y1, z_ut1 - 3, z_ut1, STRAP, "strap")
    box("Храповик", hx + 3, hx + 9, y0 - 5, y1 + 5, z_deck + 250, z_deck + 300, "#3A424A", "strap")

HEIGHT_TOP = z_top
