"""Chinese and English menus, flight instruments, and results for Starway Flight."""

from tkinter import Canvas


INK = "#f0fbff"
MUTED = "#93b4c3"
PANEL = "#091923"
EDGE = "#285166"
CYAN = "#69edf2"
GOLD = "#ffd681"
CORAL = "#ffa089"
CHINESE = "Microsoft YaHei UI"
ENGLISH = "Segoe UI"
NUMERIC = "Bahnschrift"

TEXT = {
    "zh": {
        "title": "星轨穿梭",
        "goal": "穿过陨石带，收集沿途的能量晶体",
        "controls": "WASD / 方向键  移动     ·     P / Esc  暂停",
        "course": "航道长度",
        "distance": "航程",
        "hull": "机体",
        "score": "得分",
        "best": "最高分",
        "speed": "飞行速度",
        "start": "开始飞行",
        "pause": "暂停",
        "resume": "继续飞行",
        "restart": "重新飞行",
        "title_menu": "返回标题",
        "paused": "飞行暂停",
        "won": "成功穿越",
        "lost": "飞船损毁",
        "sound_on": "声音开",
        "sound_off": "声音关",
        "language": "English",
        "enter": "回车",
        "crystal": "+100  能量晶体",
        "hit": "机体受损",
    },
    "en": {
        "title": "STARWAY FLIGHT",
        "goal": "Dodge asteroids and collect energy crystals",
        "controls": "WASD / Arrow keys to steer     ·     P / Esc to pause",
        "course": "COURSE LENGTH",
        "distance": "DISTANCE",
        "hull": "HULL",
        "score": "SCORE",
        "best": "BEST SCORE",
        "speed": "FLIGHT SPEED",
        "start": "Start flight",
        "pause": "Pause",
        "resume": "Resume flight",
        "restart": "Fly again",
        "title_menu": "Main menu",
        "paused": "Flight paused",
        "won": "Course complete",
        "lost": "Ship destroyed",
        "sound_on": "Sound on",
        "sound_off": "Sound off",
        "language": "简体中文",
        "enter": "Enter",
        "crystal": "+100  Energy crystal",
        "hit": "Hull damaged",
    },
}


class Hud:
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.scale = 1.0
        self.buttons: dict[str, tuple[float, float, float, float]] = {}
        self.copy = TEXT["zh"]
        self.family = CHINESE
        self.hovered = None
        self.pressed = None

    def draw(
        self, width, height, *, mode, health, score, best, distance, target,
        speed, elapsed, message="", muted=False, language="zh", hovered=None, pressed=None,
    ):
        self.canvas.delete("hud")
        self.buttons.clear()
        self.scale = max(0.75, min(1.25, width / 1100, height / 700))
        self.copy = TEXT.get(language, TEXT["zh"])
        self.family = ENGLISH if language == "en" else CHINESE
        self.hovered = hovered
        self.pressed = pressed
        s = self.scale
        margin = 28 * s

        for x, dx in ((margin, 1), (width - margin, -1)):
            for y, dy in ((margin, 1), (height - margin, -1)):
                self.canvas.create_line(
                    x, y + dy * 12 * s, x, y, x + dx * 12 * s, y,
                    fill=EDGE, width=1, tags="hud",
                )

        if mode == "title":
            self._title(width, height, best, target)
        elif mode == "playing":
            self._instruments(width, height, health, score, best, distance, target, speed)
            if message:
                self._notice(width / 2, height - 107 * s, message)
        else:
            self._dialog(width, height, mode, score, best, distance)

        self._toolbar(width, height, mode, muted)

    def action_at(self, x, y) -> str | None:
        for action, (left, top, right, bottom) in self.buttons.items():
            if left <= x <= right and top <= y <= bottom:
                return action
        return None

    def _label(self, x, y, text, size, *, color=INK, anchor="center", bold=False, family=None):
        style = "bold" if bold else "normal"
        self.canvas.create_text(
            x, y, text=text, fill=color, anchor=anchor,
            font=(family or self.family, -max(9, round(size * self.scale)), style), tags="hud",
        )

    def _panel(self, left, top, right, bottom, *, fill=PANEL, outline=EDGE, cut=8):
        c = cut * self.scale
        self.canvas.create_polygon(
            left, top + c, left + c, top, right, top, right, bottom - c,
            right - c, bottom, left, bottom, fill=fill, outline=outline,
            width=1, tags="hud",
        )

    def _button(self, x, y, width, height, label, action, *, shortcut=None, primary=False, family=None):
        s = self.scale
        left, right = x - width * s / 2, x + width * s / 2
        top, bottom = y - height * s / 2, y + height * s / 2
        self.buttons[action] = (left, top, right, bottom)
        hovered = self.hovered == action
        pressed = self.pressed == action and hovered
        shift = 2 * s if pressed else 0
        top += shift
        bottom += shift
        y += shift

        if primary:
            fill = "#45becb" if pressed else "#a0fcfa" if hovered else CYAN
            outline = "#b2fbfc"
            ink = "#071a25"
            key_edge = "#39868b"
            halo = CYAN if hovered else "#338993"
            self._panel(left - 4 * s, top - 4 * s, right + 4 * s, bottom + 4 * s, fill="", outline=halo)
        else:
            fill = "#174451" if pressed else "#163545" if hovered else "#0d2330"
            outline = CYAN if hovered else "#416f81"
            ink = INK
            key_edge = "#507d8d"

        self._panel(left, top, right, bottom, fill=fill, outline=outline)
        if shortcut:
            key_width = (40 if shortcut in ("回车", "Enter") else 25) * s
            key_right = right - 9 * s
            key_left = key_right - key_width
            self._panel(key_left, y - 11 * s, key_right, y + 11 * s, fill="", outline=key_edge, cut=3)
            key_family = CHINESE if shortcut == "回车" else ENGLISH
            self._label((key_left + key_right) / 2, y, shortcut, 11, color=ink, family=key_family, bold=True)
            x = (left + key_left) / 2
        self._label(x, y, label, 20 if primary else 14, color=ink, bold=True, family=family)

    def _toolbar(self, width, height, mode, muted):
        s = self.scale
        y = height - 56 * s
        self._button(width - 109 * s, y, 136, 39, self.copy["language"], "language", shortcut="L", family=CHINESE)
        sound = self.copy["sound_off" if muted else "sound_on"]
        self._button(width - 251 * s, y, 124, 39, sound, "mute", shortcut="M")
        if mode == "playing":
            self._button(width - 376 * s, y, 102, 39, self.copy["pause"], "pause", shortcut="P")

    def _title(self, width, height, best, target):
        s = self.scale
        center = width / 2
        self._label(46 * s, 48 * s, self.copy["course"], 12, color=MUTED, anchor="w", bold=True)
        self._label(46 * s, 77 * s, f"{target:,.0f} m", 24, anchor="w", family=NUMERIC, bold=True)
        self._label(width - 46 * s, 48 * s, self.copy["best"], 12, color=MUTED, anchor="e", bold=True)
        self._label(width - 46 * s, 77 * s, f"{best:04d}", 24, color=GOLD, anchor="e", family=NUMERIC, bold=True)

        title_y = height * 0.175
        title_size, title_family = (72, NUMERIC) if self.family == ENGLISH else (78, CHINESE)
        self._label(
            center + 2 * s, title_y + 4 * s, self.copy["title"], title_size,
            color="#07141d", family=title_family, bold=True,
        )
        self._label(center, title_y, self.copy["title"], title_size, family=title_family, bold=True)
        rule_y = title_y + 55 * s
        self.canvas.create_line(
            center - 53 * s, rule_y, center + 53 * s, rule_y,
            fill=CYAN, width=max(1, round(2 * s)), tags="hud",
        )
        self._label(center, rule_y + 26 * s, self.copy["goal"], 17, color=INK)

        button_y = height * 0.743
        self._button(center, button_y, 268, 54, self.copy["start"], "start", shortcut=self.copy["enter"], primary=True)
        self._label(center, button_y + 51 * s, self.copy["controls"], 14, color=MUTED)

    def _instruments(self, width, height, health, score, best, distance, target, speed):
        s = self.scale
        center = width / 2
        self._panel(37 * s, 36 * s, 188 * s, 109 * s)
        self._label(53 * s, 57 * s, self.copy["hull"], 13, color=MUTED, anchor="w", bold=True)
        self._label(171 * s, 57 * s, f"{health} / 3", 15, anchor="e", family=NUMERIC, bold=True)
        for index in range(3):
            left = (53 + index * 41) * s
            fill = (CYAN if health > 1 else CORAL) if index < health else "#142c38"
            self._panel(left, 75 * s, left + 34 * s, 91 * s, fill=fill, cut=4)

        self._panel(center - 132 * s, 36 * s, center + 132 * s, 109 * s)
        self._label(center - 115 * s, 57 * s, self.copy["distance"], 13, color=MUTED, anchor="w", bold=True)
        self._label(
            center + 115 * s, 58 * s, f"{distance:,.0f} / {target:,.0f} m", 17,
            anchor="e", family=NUMERIC, bold=True,
        )
        left, right = center - 115 * s, center + 115 * s
        self.canvas.create_rectangle(left, 80 * s, right, 88 * s, fill="#143140", width=0, tags="hud")
        progress = max(0, min(distance / target, 1))
        if progress > 0:
            self.canvas.create_rectangle(
                left, 80 * s, left + progress * (right - left), 88 * s,
                fill=CYAN, width=0, tags="hud",
            )

        self._panel(width - 188 * s, 36 * s, width - 37 * s, 109 * s)
        self._label(width - 171 * s, 57 * s, self.copy["score"], 13, color=MUTED, anchor="w", bold=True)
        self._label(width - 53 * s, 59 * s, f"{score:04d}", 25, color=GOLD, anchor="e", family=NUMERIC, bold=True)
        self._label(width - 171 * s, 86 * s, self.copy["best"], 11, color=MUTED, anchor="w")
        self._label(width - 53 * s, 86 * s, f"{best:04d}", 15, anchor="e", family=NUMERIC)

        self._label(46 * s, height - 69 * s, self.copy["speed"], 11, color=MUTED, anchor="w", bold=True)
        self._label(46 * s, height - 44 * s, f"{speed:.0f} m/s", 24, anchor="w", family=NUMERIC, bold=True)

    def _notice(self, x, y, message):
        s = self.scale
        color = GOLD if message == "crystal" else CORAL
        self._panel(x - 108 * s, y - 19 * s, x + 108 * s, y + 19 * s, outline=color)
        self._label(x, y, self.copy.get(message, message), 16, color=color, bold=True)

    def _dialog(self, width, height, mode, score, best, distance):
        s = self.scale
        x, y = width / 2, height * 0.51
        color = CORAL if mode == "lost" else CYAN
        action = "resume" if mode == "paused" else "restart"
        self._panel(x - 254 * s, y - 149 * s, x + 254 * s, y + 149 * s, fill="#0a1d2a", outline="#416f81", cut=16)
        self.canvas.create_line(
            x - 49 * s, y - 149 * s, x + 49 * s, y - 149 * s,
            fill=color, width=max(1, round(2 * s)), tags="hud",
        )
        self._label(x, y - 92 * s, self.copy[mode], 42, color=color, bold=True)
        for offset, label, value, number_color in (
            (-144, "distance", f"{distance:,.0f} m", INK),
            (0, "score", f"{score:04d}", GOLD),
            (144, "best", f"{best:04d}", INK),
        ):
            left = x + (offset - 64) * s
            right = x + (offset + 64) * s
            self._panel(left, y - 37 * s, right, y + 36 * s, outline="#254858", cut=5)
            self._label(x + offset * s, y - 17 * s, self.copy[label], 12, color=MUTED, bold=True)
            self._label(x + offset * s, y + 12 * s, value, 25, color=number_color, family=NUMERIC, bold=True)
        self._button(
            x - 80 * s, y + 87 * s, 236, 51, self.copy[action], action,
            shortcut=self.copy["enter"], primary=True,
        )
        self._button(x + 126 * s, y + 87 * s, 148, 51, self.copy["title_menu"], "title")
