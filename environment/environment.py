from __future__ import annotations

import random
from ursina import *

from core.assets import texture


def _get(level, name, default):
    return getattr(level, name, default)


def distance_xz(a, b):
    return ((a.x - b.x) ** 2 + (a.z - b.z) ** 2) ** 0.5


def _make_building(parent, x, z, sx, sy, sz):
    # Bez origin_y=-.5. Poprzednio przez to budynki wisiały w powietrzu.
    building = Entity(
        parent=parent,
        name='Building',
        model='cube',
        scale=(sx, sy, sz),
        position=(x, sy / 2, z),
        texture=texture('brick'),
        texture_scale=(max(1, sx * .7), max(1, sy * .45)),
        color=color.rgb(210, 210, 210),
        collider='box',
    )

    # Dach jako osobny world entity, bez dziedziczenia skali budynku.
    Entity(
        parent=parent,
        name='BuildingRoof',
        model='cube',
        scale=(sx * 1.08, .25, sz * 1.08),
        position=(x, sy + .12, z),
        texture=texture('concrete'),
        texture_scale=(2, 2),
        color=color.rgb(70, 72, 78),
        collider='box',
    )

    # Kilka prostych okien na ścianie frontowej. Tanie, ale od razu czytelniejsze.
    floors = max(2, int(sy // 3))
    columns = max(2, int(sx // 2.5))
    for floor in range(floors):
        y = 1.4 + floor * 2.4
        if y > sy - 1:
            continue
        for col in range(columns):
            offset_x = -sx * .38 + col * (sx * .76 / max(columns - 1, 1))
            Entity(
                parent=parent,
                name='WindowFront',
                model='cube',
                scale=(.55, .75, .06),
                position=(x + offset_x, y, z - sz / 2 - .035),
                color=color.rgb(130, 190, 210),
            )
            Entity(
                parent=parent,
                name='WindowBack',
                model='cube',
                scale=(.55, .75, .06),
                position=(x + offset_x, y, z + sz / 2 + .035),
                color=color.rgb(130, 190, 210),
            )

    return building


def _make_tree(parent, x, z):
    trunk_height = random.uniform(3.2, 4.8)
    trunk = Entity(
        parent=parent,
        name='TreeTrunk',
        model='cube',
        scale=(.55, trunk_height, .55),
        position=(x, trunk_height / 2, z),
        texture=texture('wood'),
        texture_scale=(1, 2),
        color=color.rgb(145, 95, 52),
        collider='box',
    )
    Entity(
        parent=parent,
        name='TreeCrown',
        model='sphere',
        scale=random.uniform(2.4, 3.8),
        texture=texture('leaf'),
        color=color.rgb(80, random.randint(135, 185), 85),
        position=(x, trunk_height + 1.5, z),
    )
    return trunk


def setup_environment(level=None):
    """
    Buduje poziom pod jednym LevelRoot.
    Restart poziomu = destroy(LevelRoot), więc nie zostają śmieci w scenie.
    """
    bounds = int(_get(level, 'bounds', 60))
    building_count = int(_get(level, 'building_count', 14))
    tree_count = int(_get(level, 'tree_count', 22))
    spawn = _get(level, 'spawn', Vec3(-20, 2, -20))

    world = Entity(name='LevelRoot')

    Entity(
        parent=world,
        name='Ground',
        model='plane',
        collider='box',
        scale=bounds * 2,
        position=(0, 0, 0),
        texture=texture('grass'),
        texture_scale=(bounds / 4, bounds / 4),
        color=color.rgb(115, 165, 95),
    )

    # Lekko podniesiona siatka/plac, żeby gracz miał punkty orientacyjne.
    for pos, sc, col in [
        (Vec3(0, .015, 0), (8, .03, 8), color.rgba(60, 70, 75, 220)),
        (Vec3(bounds * .45, .015, -bounds * .35), (6, .03, 6), color.azure),
        (Vec3(-bounds * .45, .015, bounds * .35), (6, .03, 6), color.orange),
    ]:
        Entity(
            parent=world,
            name='Landmark',
            model='cube',
            scale=sc,
            position=pos,
            texture=texture('metal'),
            texture_scale=(2, 2),
            color=col,
            collider='box',
        )

    wall_data = [
        ((0, 2.5, bounds), (bounds * 2, 5, 1)),
        ((0, 2.5, -bounds), (bounds * 2, 5, 1)),
        ((bounds, 2.5, 0), (1, 5, bounds * 2)),
        ((-bounds, 2.5, 0), (1, 5, bounds * 2)),
    ]
    for position, scale_value in wall_data:
        Entity(
            parent=world,
            name='BoundaryWall',
            model='cube',
            collider='box',
            position=position,
            scale=scale_value,
            texture=texture('concrete'),
            texture_scale=(12, 3),
            color=color.rgb(120, 124, 132),
        )

    for _ in range(building_count):
        x, z = 0, 0
        for _attempt in range(100):
            x = random.uniform(-bounds + 8, bounds - 8)
            z = random.uniform(-bounds + 8, bounds - 8)
            if distance_xz(Vec3(x, 0, z), spawn) > 13:
                break
        sx = random.uniform(4.0, 8.5)
        sy = random.uniform(5.5, 18)
        sz = random.uniform(4.0, 8.5)
        _make_building(world, x, z, sx, sy, sz)

    for _ in range(tree_count):
        x = random.uniform(-bounds + 5, bounds - 5)
        z = random.uniform(-bounds + 5, bounds - 5)
        if distance_xz(Vec3(x, 0, z), spawn) < 10:
            continue
        _make_tree(world, x, z)

    # Światło zostaje proste. Zaawansowany shader był głównym podejrzanym białych tekstur.
    sun = DirectionalLight(parent=world)
    sun.look_at(Vec3(1, -1, -1))
    sun.color = color.rgb(245, 245, 235)
    AmbientLight(parent=world, color=color.rgba(100, 100, 110, 90))

    return world
