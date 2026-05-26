from __future__ import annotations

from dataclasses import dataclass
from ursina import Vec3


@dataclass(frozen=True)
class LevelConfig:
    name: str
    subtitle: str
    enemy_count: int
    bounds: int
    enemy_hp: int
    enemy_speed: float
    detect_radius: float
    spawn: Vec3
    music: str
    building_count: int
    tree_count: int
    goal_text: str
    sky_color: tuple[int, int, int] = (120, 170, 255)


LEVELS = [
    LevelConfig(
        name='Poziom 1: Rozgrzewka',
        subtitle='Mała mapa, wolniejsi przeciwnicy. Naucz się strzelać i przeładowywać.',
        enemy_count=6,
        bounds=42,
        enemy_hp=80,
        enemy_speed=1.8,
        detect_radius=13,
        spawn=Vec3(-18, 2, -18),
        # Bez .mp3. Loader sam szuka level1.ogg albo level1.wav.
        music='level1',
        building_count=8,
        tree_count=16,
        goal_text='Wyczyść pierwszy sektor',
    ),
    LevelConfig(
        name='Poziom 2: Miasto',
        subtitle='Więcej osłon, więcej wrogów, szybsze tempo.',
        enemy_count=10,
        bounds=58,
        enemy_hp=100,
        enemy_speed=2.25,
        detect_radius=16,
        spawn=Vec3(-24, 2, -24),
        music='level2',
        building_count=15,
        tree_count=22,
        goal_text='Przebij się przez patrol',
        sky_color=(90, 120, 160),
    ),
    LevelConfig(
        name='Poziom 3: Boss Fight',
        subtitle='Dużo przeciwników i agresywne AI. Tutaj gra przestaje być spacerkiem.',
        enemy_count=15,
        bounds=72,
        enemy_hp=120,
        enemy_speed=2.75,
        detect_radius=20,
        spawn=Vec3(-30, 2, -30),
        music='BoSS_Fight',
        building_count=22,
        tree_count=26,
        goal_text='Przeżyj finałową falę',
        sky_color=(80, 80, 110),
    ),
]
