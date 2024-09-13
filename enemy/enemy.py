from ursina import *
from ursina.prefabs.health_bar import HealthBar
from random import uniform, randint
import math

def distance_xz(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.z - b.z) ** 2)

class Enemy(Entity):
    all_enemies = []

    def __init__(self, shootables_parent, player, patrol_points=None, group=None, **kwargs):
        self.shootables_parent = shootables_parent
        self.player = player
        super().__init__(parent=self.shootables_parent, model='cube', scale_y=2, origin_y=-.5, color=color.red,
                         collider='box', **kwargs)
        self.health_bar = HealthBar(parent=self, y=2, z=-1, scale_x=2, world_scale_y=0.1, bar_color=color.red)
        self.max_hp = 100
        self._hp = self.max_hp
        self.speed = 2
        self.state = 'patrol'
        self.alive = True
        self.group = group  # Grupa, do której należy wróg
        self.patrol_points = patrol_points or [Vec3(uniform(-8, 8), 0, uniform(-8, 8)) for _ in range(4)]
        self.current_patrol_index = 0
        self.detect_radius = 15  # Promień wykrywania gracza
        self.fov = 90  # Pole widzenia (w stopniach)
        self.target = None  # Cel, na który wróg jest skupiony
        Enemy.all_enemies.append(self)  # Dodajemy do listy wszystkich wrogów

    def update(self):
        if not self.player or not hasattr(self.player, 'alive') or not self.player.alive:
            return

        if not self.alive:
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
        # Poruszanie się po punktach patrolowych
        target_point = self.patrol_points[self.current_patrol_index]
        self.look_at_2d(target_point)
        self.position += self.forward * time.dt * self.speed

        if distance_xz(self.position, target_point) < 1:
            self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)

        # Wykrywanie gracza
        if self.can_see_player():
            self.state = 'chase'
            self.inform_others()

    def chase(self):
        if not self.can_see_player():
            self.state = 'search'
            self.search_timer = time.time()
            return

        self.look_at_2d(self.player.position)
        self.position += self.forward * time.dt * self.speed * 1.5

        if distance_xz(self.player.position, self.position) < 2:
            self.state = 'attack'

    def attack(self):
        if not self.can_see_player():
            self.state = 'search'
            self.search_timer = time.time()
            return

        if distance_xz(self.player.position, self.position) > 2:
            self.state = 'chase'
            return

        # Atakowanie gracza
        self.player.hp -= 1 * time.dt * 10  # Zadaje obrażenia w czasie
        print(f"{self} atakuje {self.player} i zadaje obrażenia.")

    def search(self):
        # Wrogowie rozglądają się, gdy stracą z oczu gracza
        if time.time() - self.search_timer > 5:
            self.state = 'patrol'
            return

        self.look_around()
        if self.can_see_player():
            self.state = 'chase'
            self.inform_others()

    def look_around(self):
        # Proste obracanie się w celu poszukiwania gracza
        self.rotation_y += time.dt * 45  # Obraca się z prędkością 45 stopni na sekundę

    def can_see_player(self):
        # Sprawdza, czy wróg może zobaczyć gracza
        direction_to_player = self.player.position - self.position

        # Projekcja na płaszczyznę XZ
        direction_to_player_xz = Vec3(direction_to_player.x, 0, direction_to_player.z).normalized()
        forward_xz = Vec3(self.forward.x, 0, self.forward.z).normalized()

        # Oblicz kąt między wektorem 'forward' a kierunkiem do gracza
        angle = forward_xz.angleDeg(direction_to_player_xz)

        if distance_xz(self.position, self.player.position) < self.detect_radius and angle < self.fov / 2:
            # Opcjonalnie: sprawdź, czy między wrogiem a graczem nie ma przeszkód (raycasting)
            return True
        return False

    def inform_others(self):
        # Informuje innych wrogów w pobliżu o obecności gracza
        for enemy in Enemy.all_enemies:
            if enemy is not self and enemy.alive and distance_xz(self.position, enemy.position) < self.detect_radius * 2:
                enemy.state = 'chase'

    def handle_collisions(self):
        # Unikanie kolizji z innymi wrogami
        for other in Enemy.all_enemies:
            if other is not self and other.alive:
                if distance_xz(self.position, other.position) < 1:
                    direction_away = (self.position - other.position).normalized()
                    self.position += direction_away * time.dt * self.speed

    def take_damage(self, damage, direction):
        self._hp -= damage
        self.position += direction * 0.1
        self.health_bar.value = self._hp / self.max_hp
        if self._hp <= 0:
            self.die()

    def die(self):
        self.alive = False
        self.state = 'dead'
        self.health_bar.enabled = False
        destroy(self, delay=2)  # Usuwa wroga po 2 sekundach

    def reset(self):
        self._hp = self.max_hp
        self.position = self.initial_position
        self.state = 'patrol'
        self.health_bar.value = self._hp / self.max_hp
        self.alive = True
        self.health_bar.enabled = True

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value
        if value <= 0:
            self.die()
        self.health_bar.value = self._hp / self.max_hp
        self.health_bar.alpha = 1

