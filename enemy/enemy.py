from __future__ import annotations

import math
from random import uniform

from ursina import *
from ursina.prefabs.health_bar import HealthBar

from core.assets import texture


def distance_xz(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.z - b.z) ** 2)


class Enemy(Entity):
    all_enemies = []

    def __init__(self, shootables_parent, player, patrol_points=None, group=None, **kwargs):
        self.shootables_parent = shootables_parent
        self.player = player

        initial_position = kwargs.pop('initial_position', None)
        if initial_position is not None:
            kwargs.setdefault('position', initial_position)
        self.initial_position = Vec3(kwargs.get('position', Vec3(0, 1, 0)))

        self.max_hp = int(kwargs.pop('max_hp', 100))
        self.speed = float(kwargs.pop('speed', 2))
        self.detect_radius = float(kwargs.pop('detect_radius', 15))
        self.kill_score = int(kwargs.pop('kill_score', 100))

        super().__init__(
            parent=self.shootables_parent,
            model='cube',
            scale=(1.05, 2, 1.05),
            origin_y=-.5,
            texture=texture('enemy'),
            color=color.rgb(255, 90, 90),
            collider='box',
            **kwargs,
        )

        self.health_bar = HealthBar(parent=self, y=2.25, z=-.7, scale_x=1.35, world_scale_y=0.08, bar_color=color.red)
        self._hp = self.max_hp
        self.health_bar.value = 1
        self.state = 'patrol'
        self.alive = True
        self.group = group
        self.patrol_points = patrol_points or self._make_patrol_points()
        self.current_patrol_index = 0
        self.fov = 105
        self.search_timer = 0
        self.attack_damage_per_second = 14
        self.target = None
        Enemy.all_enemies.append(self)

    def _make_patrol_points(self):
        return [self.initial_position + Vec3(uniform(-9, 9), 0, uniform(-9, 9)) for _ in range(4)]

    def update(self):
        if application.paused or not self.enabled:
            return
        if not self.player or not getattr(self.player, 'alive', False) or not self.alive:
            return

        self.handle_collisions()

        if self.state == 'patrol':
            self.patrol()
        elif self.state == 'chase':
            self.chase()
        elif self.state == 'attack':
            self.attack()
        elif self.state == 'search':
            self.search()

    def look_at_2d(self, target_pos):
        target_pos = Vec3(target_pos.x, self.position.y, target_pos.z)
        self.look_at(target_pos)

    def patrol(self):
        self.color = color.rgb(255, 80, 80)
        target_point = self.patrol_points[self.current_patrol_index]
        self.look_at_2d(target_point)
        self.position += self.forward * time.dt * self.speed

        if distance_xz(self.position, target_point) < 1.2:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

        if self.can_see_player():
            self.state = 'chase'
            self.inform_others()

    def chase(self):
        self.color = color.orange
        if not self.can_see_player():
            self.state = 'search'
            self.search_timer = time.time()
            return

        self.look_at_2d(self.player.position)
        self.position += self.forward * time.dt * self.speed * 1.45

        if distance_xz(self.player.position, self.position) < 2.2:
            self.state = 'attack'

    def attack(self):
        self.color = color.yellow
        if not self.can_see_player():
            self.state = 'search'
            self.search_timer = time.time()
            return
        if distance_xz(self.player.position, self.position) > 2.5:
            self.state = 'chase'
            return

        self.look_at_2d(self.player.position)
        if hasattr(self.player, 'take_damage'):
            self.player.take_damage(self.attack_damage_per_second * time.dt)

    def search(self):
        self.color = color.magenta
        if time.time() - self.search_timer > 4:
            self.state = 'patrol'
            return
        self.rotation_y += time.dt * 70
        if self.can_see_player():
            self.state = 'chase'
            self.inform_others()

    def can_see_player(self):
        direction_to_player = self.player.position - self.position
        if distance_xz(self.position, self.player.position) > self.detect_radius:
            return False

        direction_to_player_xz = Vec3(direction_to_player.x, 0, direction_to_player.z)
        if direction_to_player_xz.length() == 0:
            return True
        direction_to_player_xz = direction_to_player_xz.normalized()

        forward_xz = Vec3(self.forward.x, 0, self.forward.z)
        if forward_xz.length() == 0:
            return True
        forward_xz = forward_xz.normalized()

        angle = forward_xz.angleDeg(direction_to_player_xz)
        if angle > self.fov / 2:
            return False

        hit = raycast(self.world_position + Vec3(0, 1, 0), direction_to_player.normalized(), distance=self.detect_radius, ignore=(self,))
        return not hit.hit or hit.entity == self.player

    def inform_others(self):
        for enemy in list(Enemy.all_enemies):
            if enemy is not self and enemy.alive and distance_xz(self.position, enemy.position) < self.detect_radius * 1.8:
                if enemy.state != 'attack':
                    enemy.state = 'chase'

    def handle_collisions(self):
        for other in list(Enemy.all_enemies):
            if other is self or not other.alive:
                continue
            if distance_xz(self.position, other.position) < 1.15:
                direction_away = self.position - other.position
                direction_away.y = 0
                if direction_away.length() > 0:
                    self.position += direction_away.normalized() * time.dt * self.speed

    def take_damage(self, damage, direction):
        if not self.alive:
            return
        self._hp -= damage
        knockback = Vec3(direction.x, 0, direction.z)
        if knockback.length() > 0:
            self.position += knockback.normalized() * 0.18
        self.health_bar.value = max(0, self._hp / self.max_hp)
        self.health_bar.alpha = 1
        if self._hp <= 0:
            self.die()

    def die(self):
        if not self.alive:
            return
        self.alive = False
        self.state = 'dead'
        self.collider = None
        self.health_bar.enabled = False
        self.color = color.dark_gray
        if self in Enemy.all_enemies:
            Enemy.all_enemies.remove(self)
        if self.player:
            self.player.kills = getattr(self.player, 'kills', 0) + 1
            self.player.score = getattr(self.player, 'score', 0) + self.kill_score
        destroy(self, delay=.75)

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value
        self.health_bar.value = max(0, self._hp / self.max_hp)
        if value <= 0:
            self.die()
