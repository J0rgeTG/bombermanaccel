from kivy.app import App
from kivy.atlas import Atlas
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.lang import Builder
from kivy.uix.button import Button
from widgets.bomb import Bomb
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    ReferenceListProperty,
    StringProperty,
)
from kivy.uix.widget import Widget
from widgets import Bomb
import math


class Character(Widget):
    keymap = DictProperty({
        273: '+up',
        274: '+down',
        275: '+right',
        276: '+left',
        32: 'bomb',
    })
    last_action = StringProperty('down')
    current_actions = ListProperty()
    level = ObjectProperty()
    coord_x = NumericProperty()
    coord_y = NumericProperty()
    coords = ReferenceListProperty(coord_x, coord_y)
    scale = NumericProperty(1)
    radius = NumericProperty(45)
    atlas = ObjectProperty(Atlas('data/images.atlas'))
    animation_frame = NumericProperty(0)
    animation_timer = ObjectProperty(allownone=True)
    movement_speed = NumericProperty(450)
    bombs = ListProperty()
    bomb_power = NumericProperty(2)
    bomb_wall_traversal = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Character, self).__init__(**kwargs)
        Window.bind(
            on_key_down=lambda w, keycode, *_: self.update_keys('down', keycode),
            on_key_up=lambda w, keycode, *_: self.update_keys('up', keycode),
        )
        Clock.schedule_interval(self.update, 1 / 60.)

    def on_level(self, character, level):
        if level:
            tile = level.tile_at(*[int(i) for i in self.coords])
            tile.bind(
                pos=lambda *_: self.update_coords(),
                size=lambda *_: self.update_coords(),
            )

    def on_coords(self, character, coords):
        if not self.level:
            return
        self.update_coords()

    def update_coords(self):
        coords = self.coords
        x, y = int(coords[0]), int(coords[1])

        if not (0 <= x < self.level.map_size[0] and 0 <= y < self.level.map_size[1]):
            print(f"⚠️ Coordenadas inválidas en update_coords: ({x}, {y})")
            return

        tile = self.level.tile_at(x, y)
        self.scale = min(*tile.size) / 100.
        self.center = (
            tile.x + (coords[0] - x) * tile.width,
            tile.y + (coords[1] - y) * tile.height,
        )

    def update_keys(self, state, keycode):
        if keycode in self.keymap:
            reverse_trigger = False
            action = action_name = self.keymap[keycode]
            if action.startswith(('+', '-')):
                reverse_trigger = action[0] == '-'
                action_name = action[1:]
            if state == 'down' or (state == 'up' and reverse_trigger):
                if action_name not in self.current_actions:
                    self.current_actions.append(action_name)
            if state == 'up' or (state == 'down' and reverse_trigger):
                if action_name in self.current_actions:
                    self.current_actions.remove(action_name)

    def update(self, dt):
        for action in self.current_actions[:]:
            if action == 'up':
                self.coord_y += self.movement_speed * dt / 100.
            if action == 'down':
                self.coord_y -= self.movement_speed * dt / 100.
            if action == 'right':
                self.coord_x += self.movement_speed * dt / 100.
            if action == 'left':
                self.coord_x -= self.movement_speed * dt / 100.
            if action == 'bomb':
                self.current_actions.remove('bomb')
                level = self.level
                tx, ty = level.coords(*self.center)
                tile = level.tile_at(tx, ty)

                if tile.__class__.__name__ != 'Grass':
                    continue
                if any(bomb.tile is tile for bomb in level.bombs):
                    continue

                bomb = Bomb(
                    level=level,
                    tile=tile,
                    owner=self,
                )
                level.add_widget(bomb, index=1)


        if self.current_actions:
            self.last_action = self.current_actions[-1]
            if not self.animation_timer:
                self.animation_timer = Clock.schedule_interval(
                    self.update_animation, .25
                )
                self.animation_frame = 1
        else:
            Clock.unschedule(self.animation_timer)
            self.animation_timer = None
            self.animation_frame = 0
        self.update_collisions()

    def update_animation(self, dt):
        animation_duration = len([
            key for key in self.atlas.textures
            if key.startswith(self.last_action)
            and key.split('_')[1].isdigit()
        ])
        if self.animation_frame < animation_duration - 1:
            self.animation_frame += 1
        else:
            self.animation_frame = 1

    def update_collisions(self):
        level = self.level
        radius = self.radius / 100.

        for axis, coord in enumerate(self.coords):
            min_axis, max_axis = (
                radius,
                level.map_size[axis] - radius,
            )
            self.coords[axis] = max(
                min_axis,
                min(max_axis, coord)
            )

        for nid, offset in enumerate((
            (-1, +1), (+0, +1), (+1, +1),
            (-1, +0),           (+1, +0),
            (-1, -1), (+0, -1), (+1, -1),
        )):
            neighbor = [int(self.coords[i]) + offset[i] for i in range(2)]
            if(
                neighbor[0] < 0 or neighbor[1] < 0 or
                neighbor[0] >= level.map_size[0] or
                neighbor[1] >= level.map_size[1]
            ):
                continue
            tile = level.tile_at(*neighbor)
            if level.collides(tile, self):
                tcoords = tile.coords

                for axis, coord in enumerate(self.coords):
                    na = not axis
                    for side in (0, 1):
                        if(
                            coord - radius < tcoords[axis] + side < coord + radius and
                            tcoords[na] <= self.coords[na] <= tcoords[na] + 1
                        ):
                            self.coords[axis] = tcoords[axis] + side + (
                                radius if side else -radius
                            )

                for corner, neighbors_offset in (
                    ((tcoords[0], tcoords[1]), ((-1, 0), (0, -1))),
                    ((tcoords[0] + 1, tcoords[1]), ((1, 0), (0, -1))),
                    ((tcoords[0] + 1, tcoords[1] + 1), ((1, 0), (0, 1))),
                    ((tcoords[0], tcoords[1] + 1), ((-1, 0), (0, 1))),
                ):
                    corner_dist = math.hypot(*[
                        self.coords[i] - corner[i] for i in range(2)
                    ])
                    if corner_dist < radius and all([
                        coord - radius < corner[i] < coord + radius
                        for i, coord in enumerate(self.coords)
                    ]) and not any([
                        level.collides(level.tile_at(
                            *[neighbor[i] + offset[i] for i in range(2)]
                        ), self) for offset in neighbors_offset
                    ]):
                        ratio = radius / corner_dist
                        self.coords = [
                            corner[i] + sum([
                                offset[i] for offset in neighbors_offset
                            ]) * abs(self.coords[i] - corner[i]) * ratio
                            for i in range(2)
                        ]
    
    def move(self, direction):
        if not self.level:
            print("🚫 No hay nivel asociado")
            return

        step = self.movement_speed / 100.
        new_x, new_y = self.coord_x, self.coord_y

        if direction == 'up':
            new_y += step
        elif direction == 'down':
            new_y -= step
        elif direction == 'right':
            new_x += step
        elif direction == 'left':
            new_x -= step

        max_x = self.level.map_size[0] - 0.5
        max_y = self.level.map_size[1] - 0.5
        min_x = 0.5
        min_y = 0.5

        if not (min_x <= new_x <= max_x and min_y <= new_y <= max_y):
            print(f"🚧 Movimiento cancelado: fuera del mapa ({new_x:.2f}, {new_y:.2f})")
            return

        self.coord_x = new_x
        self.coord_y = new_y

    def move_accel(self, direction, step):

        step = min(step, 0.2) 

        if not self.level:
            print("🚫 No hay nivel asociado")
            return

        new_x, new_y = self.coord_x, self.coord_y

        if direction == 'up':
            new_y += step
        elif direction == 'down':
            new_y -= step
        elif direction == 'right':
            new_x += step
        elif direction == 'left':
            new_x -= step

        max_x = self.level.map_size[0] - 0.5
        max_y = self.level.map_size[1] - 0.5
        min_x = 0.5
        min_y = 0.5

        if not (min_x <= new_x <= max_x and min_y <= new_y <= max_y):
            print(f"🚧 Movimiento cancelado: fuera del mapa ({new_x:.2f}, {new_y:.2f})")
            return

        self.coord_x = new_x
        self.coord_y = new_y

        tile = self.level.tile_at(int(self.coord_x), int(self.coord_y))
        if self.level.collides(tile, self):
            print("🚫 Movimiento bloqueado por colisión con obstáculo")
            return
    
    def die(self):
        print("☠️ El personaje ha muerto")
        app = App.get_running_app()
        if hasattr(self.level, "players_area"):
            self.level.players_area.remove_widget(self)
        if self in self.level.players:
            self.level.players.remove(self)
        app.on_game_over()

Factory.register('Character', module='widgets')
Builder.load_file('widgets/character.kv')
