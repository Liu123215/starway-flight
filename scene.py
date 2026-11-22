"""Perspective renderer for the game's original low-poly spacecraft and flight path."""

from math import ceil, cos, pi, sin, sqrt
from random import Random
from tkinter import PhotoImage


CAMERA_OFFSET = 9.0
NEAR = 0.75
STAR_COLORS = ("#15304c", "#23445e", "#345575", "#4c7592", "#91b9cc")
RAIL_COLORS = ("#0b1a2f", "#10243b", "#152e47", "#1a3a52", "#234c62", "#34637a")
FRAME_TAGS = ("scene", "scene_frame")
SKY_TAGS = ("scene", "scene_sky")
SHIP_FACES = (
    # The wings slope down from the body so their lit surfaces show from behind.
    ("#187c92", ((0.22, 0.11, 0.45), (1.06, -0.22, -0.76), (0.48, -0.20, -0.49))),
    ("#239eb2", ((-0.22, 0.11, 0.45), (-1.06, -0.22, -0.76), (-0.48, -0.20, -0.49))),
    ("#16475e", ((0.24, -0.21, -0.74), (1.06, -0.22, -0.76), (0.48, -0.20, -0.49))),
    ("#1b556d", ((-0.24, -0.21, -0.74), (-1.06, -0.22, -0.76), (-0.48, -0.20, -0.49))),
    ("#73e6eb", ((0.24, 0.10, 0.37), (1.06, -0.22, -0.76), (0.93, -0.15, -0.63))),
    ("#9ff8f7", ((-0.24, 0.10, 0.37), (-1.06, -0.22, -0.76), (-0.93, -0.15, -0.63))),
    ("#7de1e7", ((0, 0.47, 1.23), (0, 0.35, -0.22), (-0.31, -0.03, -0.47))),
    ("#3db3c6", ((0, 0.47, 1.23), (0.31, -0.03, -0.47), (0, 0.35, -0.22))),
    ("#24849e", ((0, 0.47, 1.23), (-0.31, -0.03, -0.47), (0, -0.29, -0.65))),
    ("#165571", ((0, 0.47, 1.23), (0, -0.29, -0.65), (0.31, -0.03, -0.47))),
    ("#133149", ((0, 0.35, -0.22), (0.31, -0.03, -0.47), (0, -0.29, -0.65), (-0.31, -0.03, -0.47))),
    ("#466c86", ((0, 0.24, -0.46), (0.24, -0.02, -0.59), (0, -0.24, -0.72), (-0.24, -0.02, -0.59))),
    ("#114563", ((0, 0.12, -0.68), (0.17, -0.02, -0.72), (0, -0.17, -0.78), (-0.17, -0.02, -0.72))),
    ("#64edfa", ((0, 0.065, -0.76), (0.125, -0.02, -0.82), (0, -0.11, -0.88), (-0.125, -0.02, -0.82))),
    ("#e1ffff", ((0, 0.02, -0.84), (0.075, -0.02, -0.86), (0, -0.065, -0.90), (-0.075, -0.02, -0.86))),
    ("#123451", ((0, 0.38, 0.68), (-0.145, 0.20, 0.28), (0, 0.32, -0.12), (0.145, 0.20, 0.28))),
    ("#3095bb", ((0, 0.37, 0.59), (-0.10, 0.21, 0.25), (0, 0.32, 0.08))),
)

CRYSTAL_VERTICES = (
    (0, 1.22, 0), (0, -1.22, 0), (0.69, 0, 0), (0, 0, 0.69),
    (-0.69, 0, 0), (0, 0, -0.69),
)
CRYSTAL_FACES = tuple(
    face for index in range(2, 6)
    for face in ((0, (index - 1) % 4 + 2, index), (1, index, (index - 1) % 4 + 2))
)
CRYSTAL_COLORS = ("#99551d", "#c57928", "#eb9b37", "#ffb745", "#ffd14e", "#fff0a6")
ROCK_COLORS = ("#492638", "#653141", "#823e48", "#9f4f50", "#bf6458", "#db7d65", "#eda085")


def rock_mesh():
    vertices = [(0.08, 1, -0.05), (-0.24, -0.87, 0.1)]
    rng = Random(176)
    for ring, height in enumerate((0.44, -0.43)):
        for index in range(5):
            angle = (index + ring * 0.5) * 2 * pi / 5
            radius = rng.uniform(0.77, 0.98)
            vertices.append((radius * cos(angle), height + rng.uniform(-0.18, 0.18), radius * sin(angle)))
    faces = []
    for index in range(5):
        upper, upper_next = 2 + index, 2 + (index + 1) % 5
        lower, lower_next = 7 + index, 7 + (index + 1) % 5
        faces.extend(((0, upper, upper_next), (1, lower_next, lower),
                      (upper, lower, upper_next), (upper_next, lower, lower_next)))
    return vertices, faces


ROCK_VERTICES, ROCK_FACES = rock_mesh()


class Scene:
    """Draw scenery and depth-sorted models onto a Tkinter canvas."""

    def __init__(self, canvas):
        self.canvas = canvas
        rng = Random(6127)
        self.stars = [
            (rng.random(), rng.random(), rng.choices(range(5), weights=(35, 34, 20, 9, 2))[0])
            for _ in range(170)
        ]
        self.dust = [
            (rng.uniform(-26, 26), rng.uniform(-17, 17), rng.uniform(0, 115))
            for _ in range(50)
        ]
        self.background = None
        self.background_size = (0, 0)
        self.background_item = None

    def draw(self, width, height, *, player_x, player_y, player_bank, distance, elapsed,
             objects, particles, show_ship=True, invulnerable=False):
        self.canvas.delete("scene_frame")
        if width < 2 or height < 2:
            return
        self.center_x = width * 0.5
        self.center_y = height * 0.49
        self.focal = min(height * 0.84, width * 0.72)
        self._sky(width, height, elapsed)
        self._tunnel(distance)

        for obj in sorted(objects, key=lambda item: item.z, reverse=True):
            if obj.z < -CAMERA_OFFSET + NEAR + obj.radius * 1.3:
                continue
            if obj.kind == "rock":
                self._mesh(obj, elapsed, ROCK_VERTICES, ROCK_FACES, ROCK_COLORS, 0.71)
            elif obj.kind == "crystal":
                self._crystal(obj, elapsed)

        if show_ship and (not invulnerable or int(elapsed * 13) % 3 != 1):
            self._ship(player_x, player_y, player_bank, elapsed, distance)
        self._particles(particles)

    def _project(self, x, y, z):
        scale = self.focal / max(NEAR, z + CAMERA_OFFSET)
        return self.center_x + x * scale, self.center_y - y * scale

    def _polygon(self, points, fill):
        coords = [coord for point in points for coord in self._project(*point)]
        self.canvas.create_polygon(coords, fill=fill, tags=FRAME_TAGS)

    def _line(self, points, fill, width=1):
        coords = [coord for point in points for coord in self._project(*point)]
        self.canvas.create_line(coords, fill=fill, width=width, tags=FRAME_TAGS)

    def _dot(self, x, y, radius, color):
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                fill=color, outline="", tags=FRAME_TAGS)

    def _sky(self, width, height, elapsed):
        if self.background_size != (width, height):
            self._build_background(width, height)
        if self.background_item is None or self.canvas.type(self.background_item) is None:
            self.background_item = self.canvas.create_image(
                0, 0, image=self.background, anchor="nw", tags=SKY_TAGS,
            )
            for u, v, tone in self.stars:
                x, y = u * width, v * height
                radius = 0.65 + tone * 0.24
                self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                                        fill=STAR_COLORS[tone], outline="", tags=SKY_TAGS)
            self.canvas.tag_lower("scene_sky")
        for index, (u, v, tone) in enumerate(self.stars):
            if tone == 4:
                x, y = u * width, v * height
                length = 2.5 + sin(elapsed * 1.8 + index) * 0.75
                self.canvas.create_line(x - length, y, x + length, y, fill=STAR_COLORS[2], tags=FRAME_TAGS)
                self.canvas.create_line(x, y - length, x, y + length, fill=STAR_COLORS[3], tags=FRAME_TAGS)
        self._dust(elapsed * 17)

    def _build_background(self, width, height):
        # Cache the diffuse sky at a lower resolution, then scale it once per resize.
        tile = 6
        columns, rows = ceil(width / tile), ceil(height / tile)
        pixels = bytearray()
        for row in range(rows):
            v = row / rows - 0.49
            for column in range(columns):
                u = column / columns - 0.50
                central_glow = max(0, 1 - sqrt((u * 1.75) ** 2 + (v * 2.9) ** 2)) ** 2
                band = v + u * 0.43 + 0.05
                cloud = max(0, 1 - sqrt(((u - 0.12) * 1.65) ** 2 + (band * 5.6) ** 2)) ** 3
                violet = max(0, 1 - sqrt(((u + 0.25) * 2.9) ** 2 + ((v - 0.16) * 3.9) ** 2)) ** 3
                grain = ((column * 31 ^ row * 67) % 3) - 1
                pixels.extend((int(4 + central_glow * 7 + cloud * 6 + violet * 12),
                               int(8 + central_glow * 17 + cloud * 12 + violet * 4 + grain),
                               int(20 + central_glow * 29 + cloud * 25 + violet * 28 + grain)))
        data = f"P6\n{columns} {rows}\n255\n".encode("ascii") + pixels
        self.canvas.delete("scene_sky")
        self.background = PhotoImage(master=self.canvas, data=data, format="PPM").zoom(tile, tile)
        self.background_size = width, height

    def _dust(self, travel):
        for x, y, start in self.dust:
            z = (start - travel) % 115 - 2
            first = self._project(x, y, z)
            second = self._project(x, y, z + 1.2 + max(0, 45 - z) * 0.042)
            tone = 1 + int(z < 44) + int(z < 13)
            self.canvas.create_line(first, second, fill=STAR_COLORS[tone], tags=FRAME_TAGS)

    def _tunnel(self, distance):
        ceiling, floor, side = 3.52, -3.52, 5.50
        far, near = 125, -1.25
        for sign in (-1, 1):
            x = sign * side
            for y in (ceiling, floor):
                self._line(((x, y, far), (x, y, near)), RAIL_COLORS[4])
                self._line(((x + sign * 0.13, y, far), (x + sign * 0.13, y, near)), RAIL_COLORS[1])
        for x in (-3.6, -1.8, 0, 1.8, 3.6):
            self._line(((x, floor, far), (x, floor, near)), RAIL_COLORS[1])

        for index in range(11, -1, -1):
            z = index * 11 - (distance % 11) + 7.5
            if z < near:
                continue
            color = RAIL_COLORS[min(4, max(0, int((75 - z) / 16)))]
            self._line(((-side, floor, z), (side, floor, z)), color)
            for sign in (-1, 1):
                x = side * sign
                self._line(((x, floor, z), (x, ceiling, z), (x - sign * 0.8, ceiling, z)), color)
                if z < 65:
                    start = (x, floor, z)
                    end = (x, floor, z + 1.65)
                    self._line((start, end), RAIL_COLORS[5], width=2)
                    self._line(((x, ceiling, z), (x, ceiling, z + 1.65)), RAIL_COLORS[5], width=2)

    def _mesh(self, obj, elapsed, vertices, faces, colors, turn_rate):
        yaw = obj.phase + elapsed * turn_rate
        tilt = 0.20 * sin(obj.phase + elapsed * turn_rate * 0.67)
        cy, sy, ct, st = cos(yaw), sin(yaw), cos(tilt), sin(tilt)
        points = []
        for x, y, z in vertices:
            x, z = x * cy - z * sy, x * sy + z * cy
            x, y = x * ct - y * st, x * st + y * ct
            points.append((obj.x + x * obj.radius, obj.y + y * obj.radius, obj.z + z * obj.radius))

        for i, j, k in faces:
            a, b, c = points[i], points[j], points[k]
            u, v, w = (b[axis] - a[axis] for axis in range(3))
            x, y, z = (c[axis] - a[axis] for axis in range(3))
            nx, ny, nz = v * z - w * y, w * x - u * z, u * y - v * x
            if nx * (a[0] - obj.x) + ny * (a[1] - obj.y) + nz * (a[2] - obj.z) < 0:
                nx, ny, nz = -nx, -ny, -nz
            if nx * a[0] + ny * a[1] + nz * (a[2] + CAMERA_OFFSET) > 0:
                continue
            length = sqrt(nx * nx + ny * ny + nz * nz)
            light = (-0.48 * nx + 0.74 * ny - 0.47 * nz) / length
            shade = round((0.25 + 0.75 * max(0, light)) * (len(colors) - 1))
            self._polygon((a, b, c), colors[shade])

    def _crystal(self, obj, elapsed):
        x, y = self._project(obj.x, obj.y, obj.z)
        radius = obj.radius * self.focal / (obj.z + CAMERA_OFFSET)
        size = radius * 1.45
        pulse = 0.68 + 0.20 * sin(elapsed * 4 + obj.phase)
        self.canvas.create_oval(x - size, y - size, x + size, y + size,
                                outline="#65502e", width=1, tags=FRAME_TAGS)
        self._mesh(obj, elapsed, CRYSTAL_VERTICES, CRYSTAL_FACES, CRYSTAL_COLORS, 1.32)
        sparkle = self._project(obj.x - 0.26 * obj.radius,
                                obj.y + (0.88 + pulse * 0.27) * obj.radius, obj.z - 0.30)
        self._dot(*sparkle, max(0.8, radius * pulse * 0.105), "#fff3bd")

    def _ship(self, x, y, bank, elapsed, distance):
        cb, sb = cos(bank), sin(bank)

        def world(point):
            px, py, pz = point
            return x + px * cb - py * sb, y + px * sb + py * cb, pz

        pulse = 0.78 + 0.22 * sin(elapsed * 29)
        boost = 1 + min(0.5, distance / 2600)
        for sign in (-1, 1):
            center = 0.52 * sign
            self._polygon((world((center - 0.055, -0.2, -0.64)),
                           world((center + 0.055, -0.2, -0.64)),
                           world((center * 1.09, -0.30, -2.45 * boost))), "#175676")
        for color, face in SHIP_FACES:
            self._polygon(tuple(world(point) for point in face), color)
        self._polygon((world((-0.083, -0.058, -0.91)), world((0.083, -0.058, -0.91)),
                       world((0, -0.185 * pulse * boost, -2))), "#83edff")

    def _particles(self, particles):
        for particle in particles:
            if particle.z < -CAMERA_OFFSET + NEAR or particle.life <= 0:
                continue
            x, y = self._project(particle.x, particle.y, particle.z)
            scale = self.focal / (particle.z + CAMERA_OFFSET)
            radius = max(0.7, scale * 0.067 * particle.life / particle.duration)
            self._dot(x, y, radius, particle.color)
