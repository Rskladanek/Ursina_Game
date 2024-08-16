from ursina import *
from ursina.prefabs.health_bar import HealthBar
from random import uniform

class Enemy(Entity):
    def __init__(self, shootables_parent, player, initial_position=None, **kwargs):
        self.shootables_parent = shootables_parent
        self.player = player
        super().__init__(parent=self.shootables_parent, model='cube', scale_y=2, origin_y=-.5, color=color.red, collider='box', **kwargs)
        self.initial_position = initial_position or self.position
        self.health_bar = HealthBar(parent=self, y=2, z=-1, scale_x=2, world_scale_y=0.1, bar_color=color.red)
        self.max_hp = 100
        self._hp = self.max_hp
        self.speed = 2
        self.state = 'patrol'
        self.patrol_target = Vec3(uniform(-8, 8), 0, uniform(-8, 8))
        self.alive = True  # Added alive attribute

    def update(self):
        if not self.player or not hasattr(self.player, 'alive') or not self.player.alive:
            return

        self.handle_collisions()

        if self.state == 'patrol':
            self.patrol()
        elif self.state == 'chase':
            self.chase()
        elif self.state == 'attack':
            self.attack()

    def patrol(self):
        if not hasattr(self, 'patrol_target'):
            return

        self.look_at_2d(self.patrol_target, 'y')
        self.position += self.forward * time.dt * self.speed
        if distance(self.position, self.patrol_target) < 1:
            self.patrol_target = Vec3(uniform(-8, 8), 0, uniform(-8, 8))

        if self.player and hasattr(self.player, 'position') and distance_xz(self.player.position, self.position) < 10:
            self.state = 'chase'

    def chase(self):
        if not self.player or not hasattr(self.player, 'position') or not self.player.alive:
            return

        self.look_at_2d(self.player.position, 'y')
        self.position += self.forward * time.dt * self.speed * 2

        if distance_xz(self.player.position, self.position) < 2:
            self.state = 'attack'
        elif distance_xz(self.player.position, self.position) > 15:
            self.state = 'patrol'

    def attack(self):
        if not self.player or not hasattr(self.player, 'position') or not self.player.alive:
            return

        if distance_xz(self.player.position, self.position) < 2:
            self.player.hp -= 1
            print(f"{self} is attacking {self.player} and reducing health.")

        if distance_xz(self.player.position, self.position) > 2:
            self.state = 'chase'

    def handle_collisions(self):
        if not self.player or not hasattr(self.player, 'position') or not self.player.alive:
            return

        collision = self.intersects(self.player)
        if collision.hit:
            direction_away = (self.position - self.player.position).normalized()
            direction_away.y = 0
            self.position += direction_away * time.dt * self.speed
            self.player.position -= direction_away * time.dt * self.speed

        for other in self.shootables_parent.children:
            if other is not self and isinstance(other, Enemy):
                collision = self.intersects(other)
                if collision.hit:
                    direction_away = (self.position - other.position).normalized()
                    direction_away.y = 0
                    self.position += direction_away * time.dt * self.speed

        if self.intersects().hit:
            self.position -= self.forward * time.dt * self.speed

    def take_damage(self, damage, direction):
        self._hp -= damage
        self.position += direction * 0.1
        self.health_bar.value = self._hp / self.max_hp
        if self._hp <= 0:
            self.explode()

    def explode(self):
        self.alive = False  # Set alive to False when the enemy dies
        for _ in range(10):
            part = Entity(model='cube', scale=0.2, color=color.red, position=self.position + Vec3(uniform(-0.5, 0.5), uniform(-0.5, 0.5), uniform(-0.5, 0.5)))
            part.animate_scale(0, duration=0.5, curve=curve.linear)
            part.animate_position(part.position + Vec3(uniform(-1, 1), uniform(-1, 1), uniform(-1, 1)), duration=0.5, curve=curve.linear)
            destroy(part, delay=0.5)
        destroy(self)

    def reset(self):
        self._hp = self.max_hp
        self.position = self.initial_position
        self.patrol_target = Vec3(uniform(-8, 8), 0, uniform(-8, 8))
        self.state = 'patrol'
        self.health_bar.value = self._hp / self.max_hp
        self.alive = True  # Reset alive to True

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value
        if value <= 0:
            self.explode()
        self.health_bar.value = self._hp / self.max_hp
        self.health_bar.alpha = 1
