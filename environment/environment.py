from __future__ import annotations

import random
from ursina import *

from core.assets import texture


def _get(level, name, default):
    return getattr(level, name, default)


def distance_xz(a, b):
    return ((a.x - b.x) ** 2 + (a.z - b.z) ** 2) ** 0.5


def _make_building(parent, x, z, sx, sy, sz):
    building = Entity(
        parent=parent,
        model='cube',
        origin_y=-.5,
        scale=(sx, sy, sz),
        texture=texture('brick'),
        texture_scale=(max(1, sx), max(1, sy / 1.5)),
        position=(x, sy / 2, z),
        collider='box',
        color=color.hsv(0, 0, random.uniform(.62, .9)),
    )

    # Prosty dach, żeby to nie wyglądało jak cmentarz z klocków.
    Entity(
        parent=building,
        model='cube',
        scale=(1.08, .08, 1.08),
        position=(0, .53, 0),
        texture=texture('concrete'),
        texture_scale=(2, 2),
        color=color.rgb(70, 70, 76),
    )
    return building


def _make_tree(parent, x, z):
    trunk = Entity(
        parent=parent,
        model='cube',
        scale=(.75, 4, .75),
        texture=texture('wood'),
        texture_scale=(1, 2),
        color=color.rgb(120, 78, 42),
        position=(x, 2, z),
        collider='box',
    )
    Entity(
        parent=parent,
        model='sphere',
        scale=random.uniform(2.4, 3.8),
        texture=texture('leaf'),
        color=color.rgb(60, random.randint(120, 170), 70),
        position=trunk.position + Vec3(0, 3, 0),
    )
    return trunk


def setup_environment(level=None):
    """
    Buduje cały poziom pod jednym parentem LevelRoot.
    Dzięki temu restart poziomu = destroy(LevelRoot), bez śmieci zostających w scenie.
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
        texture=texture('grass'),
        texture_scale=(bounds / 4, bounds / 4),
        color=color.rgb(190, 215, 190),
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
            color=color.rgba(110, 114, 122, 255),
        )

    # Budynki / osłony. Nie generujemy ich przy spawnie gracza.
    for _ in range(building_count):
        x, z = 0, 0
        for _attempt in range(100):
            x = random.uniform(-bounds + 8, bounds - 8)
            z = random.uniform(-bounds + 8, bounds - 8)
            if distance_xz(Vec3(x, 0, z), spawn) > 13:
                break
        sx = random.uniform(3.5, 8)
        sy = random.uniform(5, 18)
        sz = random.uniform(3.5, 8)
        _make_building(world, x, z, sx, sy, sz)

    for _ in range(tree_count):
        x = random.uniform(-bounds + 5, bounds - 5)
        z = random.uniform(-bounds + 5, bounds - 5)
        if distance_xz(Vec3(x, 0, z), spawn) < 10:
            continue
        _make_tree(world, x, z)

    # Landmarki — punkty orientacyjne, żeby gracz widział gdzie jest.
    landmark_positions = [
        Vec3(0, .05, 0),
        Vec3(bounds * .45, .05, -bounds * .35),
        Vec3(-bounds * .45, .05, bounds * .35),
    ]
    landmark_colors = [color.azure, color.orange, color.violet]
    for idx, pos in enumerate(landmark_positions):
        Entity(
            parent=world,
            name='Landmark',
            model='cube',
            scale=(5, .1, 5),
            position=pos,
            texture=texture('metal'),
            texture_scale=(2, 2),
            color=landmark_colors[idx % len(landmark_colors)],
        )

    sun = DirectionalLight(parent=world)
    sun.look_at(Vec3(1, -1, -1))
    sun.color = color.white

    AmbientLight(parent=world, color=color.rgba(120, 120, 130, 120))

    return world
