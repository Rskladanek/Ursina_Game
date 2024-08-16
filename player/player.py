from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.collider import BoxCollider
from ursina.audio import Audio
from .weapon import Weapon
from ui.hud import HUD
from enemy.enemy import Enemy

class Player(FirstPersonController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collider = BoxCollider(self, Vec3(0, 1, 0), Vec3(1, 2, 1))

        # Initialize the weapon
        self.weapon = Weapon(player=self)

        # Jumping
        self.jump_height = 2.5
        self.jump_speed = 14
        self.gravity = 1
        self.velocity = Vec3(0, 0, 0)
        self.grounded = False
        self.jump_boost = 1.2

        # Player health
        self.max_health = 100
        self.health = self.max_health
        self.hp = self.max_health

        # Sprinting
        self.walk_speed = 3
        self.sprint_speed = 6
        self.max_speed = 20
        self.sprint_duration = 10
        self.sprint_cooldown = 3
        self.sprint_timer = self.sprint_duration
        self.sprint_active = False
        self.sprint_recharge_rate = 1
        self.sprint_bar = Entity(parent=camera.ui, model='quad', color=color.azure, scale=(0.5, 0.05, 0.05), position=(-0.75, -0.45))

        # Inertia
        self.inertia = Vec3(0, 0, 0)
        self.friction = 0.1
        self.air_control = 0.5
        self.air_inertia_multiplier = 1.5

        # UI
        self.hud = HUD(player=self)

        # Initial position
        self.initial_position = Vec3(-10, 1, -10)
        self.position = self.initial_position

        # Game state
        self.is_dead = False
        self.alive = True

        # Player sounds
        self.step_sound = Audio('../asserts/step.wav', autoplay=False)


    def update(self):
        if self.is_dead:
            self.alive = False
            return
        self.alive = True
        super().update()
        self.handle_input()
        self.apply_gravity()
        self.detect_ground()
        self.hud.update()
        self.check_enemy_collision()
        self.apply_inertia()
        self.update_sprint()
        if self.hp <= 0:
            self.die()

    def apply_gravity(self):
        if not self.grounded:
            self.velocity.y -= self.gravity * time.dt
        else:
            self.velocity.y = 0
        self.position += self.velocity * time.dt

    def handle_input(self):
        if self.is_dead:
            return

        move_direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s']) +
            self.right * (held_keys['d'] - held_keys['a'])
        ).normalized()

        if self.grounded and move_direction.length() > 0:
            # Inercja jest ustawiana tylko, gdy postać jest na ziemi i się porusza
            self.inertia = move_direction * self.speed
            #self.play_step_sound()

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
            if self.is_dead:
                self.respawn()
            else:
                self.weapon.reload()

        self.speed = self.walk_speed
        if held_keys['shift'] and self.sprint_timer > 0 and (move_direction.length() > 0 or held_keys['space']):
            self.speed = self.sprint_speed
            self.sprint_active = True
            self.sprint_timer -= time.dt
            camera.fov = lerp(camera.fov, 100, 0.1)
        else:
            self.sprint_active = False
            camera.fov = lerp(camera.fov, 90, 0.1)


    def play_step_sound(self):
        if self.step_sound:
            self.step_sound.play()


    def apply_inertia(self):
        # Stosowanie inercji do ruchu
        if not self.grounded:
            # Gdy w powietrzu, kontynuuj ruch z użyciem inercji
            self.position += self.inertia * time.dt
        else:
            # Na ziemi inercja jest stopniowo redukowana
            self.inertia *= (1 - self.friction)
            self.position += self.inertia * time.dt

    def jump(self):
        self.velocity.y = self.jump_speed
        self.grounded = False

    def bunny_hop(self):
        # Zachowanie pędu w powietrzu
        if not self.grounded:
            if self.sprint_active:
                self.inertia *= self.jump_boost
                if self.inertia.length() > self.max_speed:
                    self.inertia = self.inertia.normalized() * self.max_speed

    def detect_ground(self):
        ray = raycast(self.world_position, self.down, distance=1.5, ignore=(self,))
        if ray.hit and self.velocity.y <= 0:
            self.grounded = True
            self.velocity.y = 0
            self.position.y = ray.world_point.y + 1

            # Resetowanie inercji tylko po wylądowaniu, gdy prędkość jest bardzo niska
            if self.inertia.length() < 0.1 and not any((held_keys['w'], held_keys['s'], held_keys['a'], held_keys['d'])):
                self.inertia = Vec3(0, 0, 0)
        else:
            self.grounded = False

    def update_sprint(self):
        if not self.sprint_active and self.sprint_timer < self.sprint_duration:
            self.sprint_timer += self.sprint_recharge_rate * time.dt
            self.sprint_timer = min(self.sprint_timer, self.sprint_duration)
        self.sprint_bar.scale_x = self.sprint_timer / self.sprint_duration

    def aim(self):
        self.aiming = True
        camera.fov = 40

    def stop_aim(self):
        self.aiming = False

    def die(self):
        if not self.death_screen:
            self.is_dead = True
            self.hud.enabled = False
            self.death_screen = Entity(parent=camera.ui, model='quad', color=color.rgba(255, 0, 0, 128), scale=(2, 2, 1))
            self.death_text = Text(text="You are dead\nPress R to restart", parent=self.death_screen, origin=(0, 0), scale=2, color=color.white)

    def respawn(self):
        self.hp = self.max_health
        self.health = self.max_health
        self.weapon.ammo = self.weapon.max_ammo
        self.position = self.initial_position
        self.velocity = Vec3(0, 0, 0)
        self.inertia = Vec3(0, 0, 0)
        self.is_dead = False
        self.alive = True

        for enemy in self.shootables_parent.children:
            if isinstance(enemy, Enemy):
                destroy(enemy)

        for initial_pos in self.initial_enemy_positions:
            Enemy(shootables_parent=self.shootables_parent, player=self, initial_position=initial_pos)

        if self.death_screen:
            destroy(self.death_screen)
            self.death_screen = None
        self.hud.enabled = True
        print(f"Respawned at position: {self.position}")

    def update_ui(self):
        self.health_text.text = f'HP: {self.hp}'
        self.ammo_text.text = f'Ammo: {self.weapon.ammo}/{self.weapon.max_ammo}'

    def input(self, key):
        if key == 'r' and self.is_dead:
            self.respawn()
        super().input(key)

    def check_enemy_collision(self):
        for enemy in self.shootables_parent.children:
            if isinstance(enemy, Enemy):
                collision = self.intersects(enemy)
                if collision.hit:
                    direction_away = (self.position - enemy.position).normalized()
                    direction_away.y = 0
                    self.position += direction_away * time.dt * self.speed
                    enemy.position -= direction_away * time.dt * self.speed
