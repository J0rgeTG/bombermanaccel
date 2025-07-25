from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from plyer import accelerometer
from widgets import Character
import sys

Builder.load_file("screens.kv")  # este contiene el menú y el juego

class Bomberman(App):
    sm = None
    level = None # Para almacenar la referencia al nivel actual

    def build(self):
        self.sm = Builder.load_file("screens.kv")
        return self.sm

    def start_game(self):
        level = self.sm.get_screen("game").ids.level
        character = Character()
        level.spawn(character)

        self.level = level

        if sys.platform == 'android':
            try:
                accelerometer.enable()
                print("✅ Acelerómetro habilitado correctamente")
            except NotImplementedError:
                print("⚠️ Acelerómetro no disponible")
            else:
                Clock.schedule_interval(self.update_accel, 1/20.)

        self.sm.current = "game"

    def update_accel(self, dt):
        print("📡 Leyendo acelerómetro...")
        val = accelerometer.acceleration
        if not val or val == (None, None, None):
            print("⚠️ Acelerómetro sin datos")
            return

        x, y, _ = val
        print(f"📡 Valor: x={x:.2f}, y={y:.2f}")

        threshold = 0.3  # Ajusta la sensibilidad

        level = self.level
        if not level or not level.players:
            return

        char = level.players[0]

        if x < -threshold:
            char.move('right')
        elif x > threshold:
            char.move('left')
        elif y < -threshold:
            char.move('up')
        elif y > threshold:
            char.move('down')



if __name__ == '__main__':
    Bomberman().run()
