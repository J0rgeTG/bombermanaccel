from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform 
from plyer import accelerometer
from widgets import Character

class Bomberman(App):
    sm = None
    level = None 

    def build(self):
        self.sm = Builder.load_file("screens.kv") 
        return self.sm

    def start_game(self):
        level = self.sm.get_screen("game").ids.level
        character = Character()
        print("👾 Personaje creado:", character)
        level.spawn(character)

        self.level = level

        if platform == 'android':
            try:
                accelerometer.enable()
                print("✅ Acelerómetro habilitado correctamente")
            except NotImplementedError:
                print("⚠️ Acelerómetro no disponible")
            else:
                Clock.schedule_interval(self.update_accel, 1 / 10.)

        print("Cambio de pantalla")
        self.sm.current = "game"

    def update_accel(self, dt):
        val = accelerometer.acceleration
        if not val or val == (None, None, None):
            print("⚠️ Acelerómetro sin datos")
            return

        x, y, z = val
        print(f"📡 Accel x={x:.2f}, y={y:.2f}, z={z:.2f}")

        gx = y 
        gy = -x 

        threshold = 0.25 
        speed_scale = 0.035  

        level = self.level
        if not level or not level.players:
            print("🚫 No hay jugadores en el nivel aún")
            return

        char = level.players[0]

        if abs(gx) > abs(gy):
            if abs(gx) > threshold:
                direction = 'right' if gx > 0 else 'left'
                char.move_accel(direction, abs(gx) * speed_scale)
        else:
            if abs(gy) > threshold:
                direction = 'up' if gy > 0 else 'down'
                char.move_accel(direction, abs(gy) * speed_scale)
    
    def on_game_over(self):
        print("🔴 Game Over triggered")
        self.sm.current = "gameover"
    
    def restart_game(self):
        print("🔁 Reiniciando juego")
        level = self.sm.get_screen("game").ids.level
        level.reset()
        char = Character()
        level.spawn(char)
        self.level = level
        self.sm.current = "game"

    def goto_menu(self):
        print("⬅️ Volver al menú")
        self.sm.current = "menu"

if __name__ == '__main__':
    Bomberman().run()