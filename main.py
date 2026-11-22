"""星轨穿梭 / Starway Flight. Run with Python 3.10+ using `python main.py`."""

import json
import math
import os
import random
import tempfile
import time
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

from hud import Hud
from scene import Scene
from sound import SoundEffects


TARGET = 1800.0
SHIP_RADIUS = 0.38
X_LIMIT = 4.7
Y_LIMIT = 2.9
MOVE_SPEED = 10.5
SPAWN_DEPTH = 115.0
COLUMNS = (-3.7, -1.85, 0.0, 1.85, 3.7)
ROWS = (-2.05, 0.0, 2.05)
LANES = [(column, row) for column in range(len(COLUMNS)) for row in range(len(ROWS))]
DEFAULT_SETTINGS = Path(os.environ.get("LOCALAPPDATA") or Path.home() / ".local" / "share")
SETTINGS_FILE = DEFAULT_SETTINGS / "StarwayFlight" / "settings.json"


@dataclass(slots=True)
class Obstacle:
    kind: str
    x: float
    y: float
    z: float
    radius: float
    phase: float
    spent: bool = False


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    life: float
    duration: float
    color: str


class Flight:
    def __init__(self, rng=None):
        self.rng = rng if rng is not None else random.Random()
        self.x = self.y = self.vx = self.vy = self.bank = 0.0
        self.elapsed = self.distance = self.invulnerable = 0.0
        self.health = 3
        self.score = 0
        self.outcome = None
        self.message = ""
        self.message_until = 0.0
        self.particles = []
        self.objects = [
            Obstacle("crystal", 0.0, 0.0, 54.0, 0.64, 0.0),
            Obstacle("rock", 0.0, 0.0, 100.0, 1.04, 1.1),
            Obstacle("rock", -3.45, -1.8, 102.0, 0.92, 2.8),
            Obstacle("crystal", 1.85, 0.0, 104.0, 0.64, 0.9),
        ]
        self.next_wave = 162.0
        self.crystal_lane = (3, 1)

    @property
    def speed(self):
        return 36.0 + 23.0 * (self.distance / TARGET)

    def step(self, dt, horizontal, vertical):
        if self.outcome or dt <= 0:
            return []

        events = []
        old_x, old_y = self.x, self.y
        length = max(1.0, math.hypot(horizontal, vertical))
        blend = 1.0 - math.exp(-dt * 14.0)
        desired_vx = horizontal * MOVE_SPEED / length
        desired_vy = vertical * MOVE_SPEED / length
        self.vx += (desired_vx - self.vx) * blend
        self.vy += (desired_vy - self.vy) * blend
        self.x = max(-X_LIMIT, min(X_LIMIT, self.x + self.vx * dt))
        self.y = max(-Y_LIMIT, min(Y_LIMIT, self.y + self.vy * dt))
        self.bank += (-self.vx / MOVE_SPEED * 0.44 - self.bank) * blend
        self.elapsed += dt
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.update_particles(dt)

        travel = min(self.speed * dt, TARGET - self.distance)
        self.distance += travel
        for obstacle in self.objects:
            obstacle.z -= travel
            if self.health > 0:
                self.check_collision(obstacle, old_x, old_y, travel, events)

        # Leave a short clear stretch after the last wave.
        while self.next_wave < TARGET - 46 and self.next_wave - self.distance <= SPAWN_DEPTH:
            self.spawn_wave(self.next_wave - self.distance)
            gap = self.rng.uniform(39.0, 51.0) - 5.0 * self.distance / TARGET
            self.next_wave += gap

        self.objects = [
            obstacle for obstacle in self.objects
            if obstacle.z > -4.4 and not (obstacle.kind == "crystal" and obstacle.spent)
        ]
        if self.health == 0:
            self.outcome = "lost"
        elif self.distance >= TARGET:
            self.outcome = "won"
        if self.outcome:
            events.append(self.outcome)
        return events

    def spawn_wave(self, depth):
        last_column, last_row = self.crystal_lane
        nearby_lanes = [
            lane for lane in LANES
            if lane != self.crystal_lane and abs(lane[0] - last_column) <= 2 and abs(lane[1] - last_row) <= 1
        ]
        self.crystal_lane = self.rng.choice(nearby_lanes)
        column, row = self.crystal_lane
        self.objects.append(Obstacle("crystal", COLUMNS[column], ROWS[row], depth, 0.64, self.rng.random() * math.tau))

        available_lanes = [lane for lane in LANES if lane != self.crystal_lane]
        rock_count = 2 + int(self.distance / TARGET * 4) + self.rng.randrange(2)
        for column, row in self.rng.sample(available_lanes, rock_count):
            self.objects.append(Obstacle(
                "rock", COLUMNS[column], ROWS[row], depth + self.rng.uniform(-2.3, 3.1),
                self.rng.uniform(0.76, 1.10), self.rng.random() * math.tau,
            ))

    def check_collision(self, obstacle, old_x, old_y, travel, events):
        radius = SHIP_RADIUS + obstacle.radius
        if obstacle.spent or obstacle.z > radius or obstacle.z + travel < -radius:
            return

        # Find the closest point along the ship's relative motion during this frame.
        rx, ry, rz = old_x - obstacle.x, old_y - obstacle.y, -obstacle.z - travel
        dx, dy, dz = self.x - old_x, self.y - old_y, travel
        motion_squared = dx * dx + dy * dy + dz * dz
        fraction = -(rx * dx + ry * dy + rz * dz) / motion_squared if motion_squared else 0.0
        fraction = min(1.0, max(0.0, fraction))
        separation = (rx + dx * fraction) ** 2 + (ry + dy * fraction) ** 2 + (rz + dz * fraction) ** 2
        if separation > radius * radius:
            return

        if obstacle.kind == "crystal":
            obstacle.spent = True
            self.score += 100
            self.message = "crystal"
            self.burst(obstacle.x, obstacle.y, obstacle.z, ("#fff2b1", "#ffce64", "#f09b37"), 18)
            events.append("crystal")
        elif self.invulnerable <= 0:
            obstacle.spent = True
            self.health -= 1
            self.invulnerable = 1.25
            self.message = "hit"
            self.burst(self.x, self.y, 0.0, ("#fff0d0", "#ff9b75", "#e45456"), 34 if self.health == 0 else 22)
            events.append("hit")
        else:
            return
        self.message_until = self.elapsed + 0.95

    def burst(self, x, y, z, colors, count):
        for _ in range(count):
            angle = self.rng.uniform(0.0, math.tau)
            speed = self.rng.uniform(1.5, 6.0)
            life = self.rng.uniform(0.28, 0.7)
            self.particles.append(Particle(
                x, y, z, math.cos(angle) * speed, math.sin(angle) * speed,
                self.rng.uniform(-5.0, 7.0), life, life, self.rng.choice(colors),
            ))

    def update_particles(self, dt):
        for particle in self.particles:
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.z += particle.vz * dt
            particle.life -= dt
        self.particles = [particle for particle in self.particles if particle.life > 0]


def read_settings(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return 0, False, "zh"
    if not isinstance(data, dict):
        return 0, False, "zh"
    best = data.get("best")
    best = best if type(best) is int and best >= 0 else 0
    language = "en" if data.get("language") == "en" else "zh"
    return best, data.get("muted") is True, language


def write_settings(path, best, muted, language):
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        best = max(best, read_settings(path)[0])
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temporary = Path(file.name)
            json.dump({"best": best, "muted": muted, "language": language}, file)
        temporary.replace(path)
    except OSError:
        # The flight still works when the settings directory is unavailable.
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
    return best


class Starway:
    def __init__(self, root, settings_path=SETTINGS_FILE):
        self.root = root
        self.settings_path = settings_path
        self.best, self.muted, self.language = read_settings(settings_path)
        self.update_title()
        root.minsize(800, 520)
        width = max(800, min(1120, int(root.winfo_screenwidth() * 0.82)))
        height = max(520, min(720, int(root.winfo_screenheight() * 0.82)))
        left = max(0, (root.winfo_screenwidth() - width) // 2)
        top = max(0, (root.winfo_screenheight() - height) // 2)
        root.geometry(f"{width}x{height}+{left}+{top}")

        self.canvas = tk.Canvas(root, highlightthickness=0, bg="#050c1b")
        self.canvas.pack(fill="both", expand=True)
        self.scene = Scene(self.canvas)
        self.hud = Hud(self.canvas)
        self.sound = SoundEffects()
        self.flight = Flight()
        self.mode = "title"
        self.painted_mode = None
        self.hovered = None
        self.pressed = None
        self.keys = set()
        self.title_elapsed = 0.0
        self.previous_time = time.perf_counter()
        self.redraw = True
        self.timer = None
        self.title_objects = [
            Obstacle("rock", -5.2, -1.8, 9.0, 1.25, 1.0),
            Obstacle("rock", 6.1, 2.1, 17.0, 1.20, 2.7),
            Obstacle("rock", -5.6, 3.1, 29.0, 0.95, 0.8),
            Obstacle("crystal", 4.3, -1.9, 10.0, 0.68, 0.2),
        ]

        root.bind("<KeyPress>", self.key_down)
        root.bind("<KeyRelease>", self.key_up)
        root.bind("<FocusOut>", self.focus_lost)
        self.canvas.bind("<Configure>", self.resized)
        self.canvas.bind("<ButtonPress-1>", self.button_down)
        self.canvas.bind("<ButtonRelease-1>", self.button_up)
        self.canvas.bind("<Motion>", self.hover)
        self.canvas.bind("<Leave>", self.clear_cursor)
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.timer = root.after(0, self.frame)

    def key_down(self, event):
        key = event.keysym.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if key in ("return", "kp_enter"):
            action = {"title": "start", "paused": "resume", "lost": "restart", "won": "restart"}.get(self.mode)
            self.act(action)
        elif key in ("p", "escape"):
            self.act("resume" if self.mode == "paused" else "pause")
        elif key == "r" and self.mode in ("won", "lost"):
            self.act("restart")
        elif key == "m":
            self.act("mute")
        elif key == "l":
            self.act("language")

    def key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def focus_lost(self, event):
        if event.widget is not self.root:
            return
        self.keys.clear()
        self.pressed = None
        self.clear_cursor(event)
        if self.mode == "playing":
            self.set_mode("paused")

    def resized(self, _event):
        self.painted_mode = None
        self.pressed = None
        self.clear_cursor(None)

    def button_down(self, event):
        self.hover(event)
        self.pressed = self.hovered
        self.redraw = True

    def button_up(self, event):
        self.hover(event)
        action = self.pressed
        self.pressed = None
        if action is not None:
            self.redraw = True
            if action == self.hovered:
                self.act(action)

    def hover(self, event):
        action = None
        if self.mode == self.painted_mode:
            action = self.hud.action_at(event.x, event.y)
        if action != self.hovered:
            self.hovered = action
            self.canvas.configure(cursor="hand2" if action else "")
            self.redraw = True

    def clear_cursor(self, _event):
        self.hovered = None
        self.canvas.configure(cursor="")
        self.redraw = True

    def set_mode(self, mode):
        self.mode = mode
        self.pressed = None
        self.clear_cursor(None)

    def update_title(self):
        self.root.title("Starway Flight" if self.language == "en" else "星轨穿梭 · Starway Flight")

    def save_preferences(self):
        self.best = write_settings(self.settings_path, self.best, self.muted, self.language)

    def act(self, action):
        if action in ("start", "restart"):
            self.flight = Flight()
            self.set_mode("playing")
            self.play_sound("start")
        elif action == "pause" and self.mode == "playing":
            self.set_mode("paused")
            self.play_sound("pause")
        elif action == "resume" and self.mode == "paused":
            self.set_mode("playing")
        elif action == "title":
            self.set_mode("title")
        elif action == "mute":
            self.muted = not self.muted
            if self.muted:
                self.sound.stop()
            self.save_preferences()
        elif action == "language":
            self.language = "en" if self.language == "zh" else "zh"
            self.update_title()
            self.save_preferences()
        else:
            return
        self.redraw = True

    def play_sound(self, event):
        if not self.muted:
            self.sound.play(event)

    def frame(self):
        now = time.perf_counter()
        dt = min(0.055, now - self.previous_time)
        self.previous_time = now
        if self.mode == "title":
            self.title_elapsed += dt
            self.redraw = True
        elif self.mode == "playing":
            horizontal = bool(self.keys & {"d", "right"}) - bool(self.keys & {"a", "left"})
            vertical = bool(self.keys & {"w", "up"}) - bool(self.keys & {"s", "down"})
            events = self.flight.step(dt, horizontal, vertical)
            if self.flight.score > self.best:
                self.best = self.flight.score
                self.save_preferences()
            if events:
                self.play_sound(events[-1])
            if self.flight.outcome:
                self.set_mode(self.flight.outcome)
            self.redraw = True
        elif self.mode == "lost" and self.flight.particles:
            self.flight.update_particles(dt)
            self.redraw = True

        if self.redraw and self.canvas.winfo_width() >= 2:
            self.paint()
            self.redraw = False

        # Account for the cost of drawing so that a fast canvas can reach 60 fps.
        work_ms = (time.perf_counter() - now) * 1000
        self.timer = self.root.after(max(4, round(16.7 - work_ms)), self.frame)

    def paint(self):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        flight = self.flight
        if self.mode == "title":
            tick = self.title_elapsed
            self.scene.draw(
                width, height, player_x=math.sin(tick * 0.8) * 0.35,
                player_y=math.sin(tick * 1.2) * 0.16 - 0.12, player_bank=math.sin(tick) * 0.13,
                distance=tick * 14, elapsed=tick, objects=self.title_objects, particles=[],
            )
        else:
            self.scene.draw(
                width, height, player_x=flight.x, player_y=flight.y, player_bank=flight.bank,
                distance=flight.distance, elapsed=flight.elapsed, objects=flight.objects,
                particles=flight.particles, show_ship=flight.health > 0,
                invulnerable=flight.invulnerable > 0,
            )
        self.hud.draw(
            width, height, mode=self.mode, health=flight.health, score=flight.score, best=self.best,
            distance=flight.distance, target=TARGET, speed=flight.speed, elapsed=flight.elapsed,
            message=flight.message if flight.elapsed < flight.message_until else "", muted=self.muted,
            language=self.language, hovered=self.hovered, pressed=self.pressed,
        )
        self.painted_mode = self.mode

    def close(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
        self.sound.close()
        self.root.destroy()


def main():
    if os.name == "nt":
        from ctypes import windll

        # The canvas uses pixels for layout. Keep Windows from stretching the window.
        windll.user32.SetProcessDPIAware()
    root = tk.Tk()
    Starway(root)
    root.mainloop()


if __name__ == "__main__":
    main()
