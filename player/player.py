from __future__ import annotations

from ursina import *
from ursina.audio import Audio
from ursina.collider import BoxCollider
from ursina.prefabs.first_person_controller import FirstPersonController

from core.assets import audio_path
from enemy.enemy import Enemy
from ui.hud import HUD
from .weapon import Weapon


class Player(FirstPersonController):
    def __init__(self, shootables_parent, initial_enemy_positions, spawn_position=None, game_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.collider = BoxCollider(self, Vec3(0, 1, 0), Vec3(1, 2, 1))

        self.game_manager = game_manager
        self.shootables_parent = shootables_parent
        self.initial_enemy_positions = initial_enemy_positions
        self.initial_position = Vec3(spawn_position or Vec3(-10, 2, -10))
        self.position = self.initial_position

        self.weapon = Weapon(player=self)

        self.jump_height = 2.5
        self.jump_speed = 14
        self.gravity = 1
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.jump_boost = 1.12

        self.max_health = 100
        self.health = self.max_health
        self.hp = float(self.max_health)
        self.score = 0
        self.kills = 0

        self.walk_speed = 3.4
        self.sprint_speed = 6.4
        self.max_speed = 18
        self.sprint_duration = 10
        self.sprint_timer = self.sprint_duration
        self.sprint_active = False
        self.sprint_recharge_rate = 1.45
        self.sprint_bar_bg = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 160), scale=(0.52, 0.06), position=(-0.67, -0.44))
        self.sprint_bar = Entity(parent=camera.ui, model='quad', color=color.azure, scale=(0.5, 0.04), position=(-0.67, -0.44))

        self.inertia = Vec3(0, 0, 0)
        self.friction = 0.1
        self.aiming = False

        self.hud = HUD(player=self)

        self.is_dead = False
        self.alive = True
        self.damage_flash = Entity(parent=camera.ui, model='quad', enabled=False, color=color.rgba(255, 0, 0, 55), scale=(2.2, 2.2), z=.15)

        try:
            self.step_sound = Audio(audio_path('step.wav'), autoplay=False)
        except Exception:
            self.step_sound = None

    def update(self):
        if application.paused or self.is_dead:
            self.alive = not self.is_dead
            return

        self.alive = True
        super().update()
        self.handle_input()
        self.apply_gravity()
        self.detect_ground()
        self.check_enemy_collision()
        self.apply_inertia()
        self.update_sprint()
        self.hud.update()

        if self.hp <= 0:
            self.die()

    def handle_input(self):
        move_direction = Vec3(self.forward * (held_keys['w'] - held_keys['s']) + self.right * (held_keys['d'] - held_keys['a'])).normalized()

        self.speed = self.walk_speed
        moving = move_direction.length() > 0 or held_keys['space']
        if held_keys['shift'] and self.sprint_timer > 0 and moving and not held_keys['right mouse']:
            self.speed = self.sprint_speed
            self.sprint_active = True
            self.sprint_timer -= time.dt
        else:
            self.sprint_active = False

        if self.grounded and move_direction.length() > 0:
            self.inertia = move_direction * self.speed

        if held_keys['left mouse'] and not self.weapon.reloading:
            self.weapon.shoot()
        if held_keys['right mouse']:
            self.aim()
        else:
            self.stop_aim()
        if held_keys['space']:
            if self.grounded:
                self.jump()
            else:
                self.bunny_hop()
        if held_keys['r']:
            self.weapon.reload()

        if self.aiming:
            camera.fov = lerp(camera.fov, 52, 0.18)
        elif self.sprint_active:
            camera.fov = lerp(camera.fov, 98, 0.12)
        else:
            camera.fov = lerp(camera.fov, 88, 0.12)

    def apply_gravity(self):
        if not self.grounded:
            self.velocity.y -= self.gravity * time.dt
        else:
            self.velocity.y = 0
        self.position += self.velocity * time.dt

    def apply_inertia(self):
        if not self.grounded:
            self.position += self.inertia * time.dt
        else:
            self.inertia *= (1 - self.friction)
            self.position += self.inertia * time.dt

    def jump(self):
        self.velocity.y = self.jump_speed
        self.grounded = False

    def bunny_hop(self):
        if not self.grounded and self.sprint_active:
            self.inertia *= self.jump_boost
            if self.inertia.length() > self.max_speed:
                self.inertia = self.inertia.normalized() * self.max_speed

    def detect_ground(self):
        ray = raycast(self.world_position, self.down, distance=1.6, ignore=(self,))
        if ray.hit and self.velocity.y <= 0:
            self.grounded = True
            self.velocity.y = 0
            self.position.y = ray.world_point.y + 1
            if self.inertia.length() < 0.08 and not any((held_keys['w'], held_keys['s'], held_keys['a'], held_keys['d'])):
                self.inertia = Vec3(0, 0, 0)
        else:
            self.grounded = False

    def update_sprint(self):
        if not self.sprint_active and self.sprint_timer < self.sprint_duration:
            self.sprint_timer += self.sprint_recharge_rate * time.dt
            self.sprint_timer = min(self.sprint_timer, self.sprint_duration)
        ratio = max(0, min(1, self.sprint_timer / self.sprint_duration))
        self.sprint_bar.scale_x = .5 * ratio
        self.sprint_bar.x = -0.67 - (0.5 - self.sprint_bar.scale_x) / 2

    def aim(self):
        self.aiming = True
        self.weapon.position = lerp(self.weapon.position, Vec3(.25, -.18, .25), .18)

    def stop_aim(self):
        self.aiming = False
        self.weapon.position = lerp(self.weapon.position, Vec3(.5, -.25, .25), .18)

    def take_damage(self, amount):
        if self.is_dead:
            return
        self.hp = max(0, self.hp - amount)
        self.health = self.hp
        if not self.damage_flash.enabled:
            self.damage_flash.enabled = True
            self.damage_flash.alpha = .35
            self.damage_flash.animate('alpha', 0, duration=.25)
            invoke(setattr, self.damage_flash, 'enabled', False, delay=.26)
        if self.hp <= 0:
            self.die()

    def die(self):
        if self.is_dead:
            return
        self.is_dead = True
        self.alive = False
        self.disable()
        self.weapon.enabled = False
        self.hud.enabled = False
        mouse.locked = False
        mouse.visible = True

    def respawn(self):
        self.hp = float(self.max_health)
        self.health = self.max_health
        self.weapon.ammo = self.weapon.max_ammo
        self.weapon.reloading = False
        self.position = self.initial_position
        self.velocity = Vec3(0, 0, 0)
        self.inertia = Vec3(0, 0, 0)
        self.is_dead = False
        self.alive = True
        self.enable()
        self.weapon.enabled = True
        self.hud.enabled = True
        self.hud.update()

    def input(self, key):
        # R jako restart obsługuje centralnie GameManager; tutaj zostawiamy tylko input FPC.
        super().input(key)

    def check_enemy_collision(self):
        for enemy in list(self.shootables_parent.children):
            if isinstance(enemy, Enemy) and enemy.alive:
                collision = self.intersects(enemy)
                if collision.hit:
                    direction_away = self.position - enemy.position
                    direction_away.y = 0
                    if direction_away.length() > 0:
                        direction_away = direction_away.normalized()
                        self.position += direction_away * time.dt * self.speed
                        enemy.position -= direction_away * time.dt * enemy.speed

    def cleanup(self):
        for obj in (self.hud, self.weapon, self.sprint_bar, self.sprint_bar_bg, self.damage_flash):
            if obj:
                try:
                    if hasattr(obj, 'cleanup'):
                        obj.cleanup()
                    else:
                        destroy(obj)
                except Exception:
                    pass
