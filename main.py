import math
import os
import random
import sys
import heapq
import asyncio
from dataclasses import dataclass, field

import pygame

try:
    import nav_mask
    _HAS_NAV_MASK = True
except ImportError:
    _HAS_NAV_MASK = False

# EXTREMELY AGGRESSIVE WEB-PATH HANDLING
def get_web_path(folder, filename):
    """Tries multiple common pygbag/web paths to find an asset."""
    paths_to_try = [
        os.path.join(folder, filename),               # Standard
        os.path.join(".", folder, filename),           # Relative root
        os.path.join("build", "web", folder, filename), # Build path
        filename,                                      # Direct (fallback)
    ]
    for p in paths_to_try:
        if os.path.exists(p):
            return p
    return None

ASSET_DIR = "assets"
SOUND_DIR = "Sounds"

SCREEN_W = 1280
SCREEN_H = 760
TOP_H = 46
BOTTOM_H = 32
SIDEBAR_W = 258
VIEW_W = SCREEN_W - SIDEBAR_W
VIEW_H = SCREEN_H - TOP_H - BOTTOM_H

WORLD_W = 1688
WORLD_H = 932
TILE = 20
NAV_TILE = TILE
BUILD_RADIUS = 220
MINIMAP_W = 214
MINIMAP_H = 118
REPAIR_COST = 10
REPAIR_HP = 20
REPAIR_INTERVAL = 0.45

TEAM_RED = "soviet"
TEAM_BLUE = "allied"

DIFFICULTIES = {
    "easy": {
        "label": "Easy",
        "enemy_hp": 0.7,
        "enemy_atk": 0.6,
        "wave_interval": 90,
        "max_wave_count": 12,
        "start_credits": 5000,
        "enemy_count_base": 2,
        "enemy_count_per_wave": 1,
    },
    "medium": {
        "label": "Medium",
        "enemy_hp": 1.0,
        "enemy_atk": 1.0,
        "wave_interval": 60,
        "max_wave_count": 16,
        "start_credits": 2000,
        "enemy_count_base": 3,
        "enemy_count_per_wave": 2,
    },
    "hard": {
        "label": "Hard",
        "enemy_hp": 1.4,
        "enemy_atk": 1.3,
        "wave_interval": 40,
        "max_wave_count": 99,
        "start_credits": 1000,
        "enemy_count_base": 4,
        "enemy_count_per_wave": 3,
    },
}

UNIT_DEFS = {
    "conscript": {
        "name": "Conscript",
        "hp": 80,
        "spd": 60,
        "atk": 15,
        "range": 80,
        "atk_spd": 1.2,
        "sight": 120,
        "size": 10,
        "cost": 100,
        "color": (205, 45, 30),
        "category": "infantry",
    },
    "dog": {
        "name": "War Dog",
        "hp": 60,
        "spd": 100,
        "atk": 25,
        "range": 40,
        "atk_spd": 1.5,
        "sight": 100,
        "size": 8,
        "cost": 200,
        "color": (150, 75, 36),
        "category": "infantry",
    },
    "tesla_trooper": {
        "name": "Tesla Trooper",
        "hp": 100,
        "spd": 55,
        "atk": 45,
        "range": 70,
        "atk_spd": 1.0,
        "sight": 120,
        "size": 10,
        "cost": 500,
        "color": (40, 150, 255),
        "category": "infantry",
    },
    "rhino": {
        "name": "Rhino Tank",
        "hp": 300,
        "spd": 70,
        "atk": 60,
        "range": 120,
        "atk_spd": 1.8,
        "sight": 160,
        "size": 16,
        "cost": 900,
        "color": (140, 70, 36),
        "category": "vehicle",
    },
    "v3": {
        "name": "V3 Rocket",
        "hp": 150,
        "spd": 60,
        "atk": 100,
        "range": 200,
        "atk_spd": 3.0,
        "sight": 180,
        "size": 18,
        "cost": 1200,
        "color": (110, 70, 26),
        "category": "vehicle",
    },
    "apocalypse": {
        "name": "Apocalypse",
        "hp": 600,
        "spd": 55,
        "atk": 120,
        "range": 140,
        "atk_spd": 2.0,
        "sight": 180,
        "size": 20,
        "cost": 2000,
        "color": (105, 28, 20),
        "category": "vehicle",
    },
    "gi": {
        "name": "GI",
        "hp": 70,
        "spd": 55,
        "atk": 12,
        "range": 80,
        "atk_spd": 1.2,
        "sight": 110,
        "size": 10,
        "cost": 0,
        "color": (45, 100, 220),
        "category": "infantry",
    },
    "grizzly": {
        "name": "Grizzly Tank",
        "hp": 250,
        "spd": 75,
        "atk": 50,
        "range": 120,
        "atk_spd": 1.8,
        "sight": 150,
        "size": 15,
        "cost": 0,
        "color": (45, 80, 170),
        "category": "vehicle",
    },
    "prism": {
        "name": "Prism Tank",
        "hp": 180,
        "spd": 65,
        "atk": 80,
        "range": 180,
        "atk_spd": 2.5,
        "sight": 200,
        "size": 14,
        "cost": 0,
        "color": (80, 125, 235),
        "category": "vehicle",
    },
}

STRUCT_DEFS = {
    "conyard": {
        "name": "Construction Yard",
        "hp": 1000,
        "pw": 0,
        "size": 6,
        "cost": 0,
        "color": (174, 65, 40),
    },
    "barracks": {
        "name": "Barracks",
        "hp": 500,
        "pw": -5,
        "size": 4,
        "cost": 300,
        "color": (198, 75, 48),
    },
    "warfactory": {
        "name": "War Factory",
        "hp": 800,
        "pw": -10,
        "size": 6,
        "cost": 2000,
        "color": (184, 80, 48),
    },
    "refinery": {
        "name": "Ore Refinery",
        "hp": 700,
        "pw": -8,
        "size": 4,
        "w_tiles": 6,
        "h_tiles": 4,
        "cost": 2000,
        "color": (198, 132, 58),
    },
    "turret": {
        "name": "Tesla Turret",
        "hp": 400,
        "pw": -5,
        "size": 2,
        "cost": 600,
        "atk": 70,
        "range": 160,
        "atk_spd": 2.0,
        "color": (150, 55, 55),
    },
    "tesla": {
        "name": "Tesla Coil",
        "hp": 500,
        "pw": -15,
        "size": 4,
        "cost": 1500,
        "atk": 120,
        "range": 200,
        "atk_spd": 2.5,
        "color": (95, 65, 175),
    },
    "wall": {
        "name": "Wall",
        "hp": 250,
        "pw": 0,
        "size": 1,
        "cost": 100,
        "color": (92, 86, 76),
    },
    "radar": {
        "name": "Radar Dome",
        "hp": 400,
        "pw": -8,
        "size": 4,
        "cost": 1000,
        "color": (92, 112, 62),
    },
    "powerplant": {
        "name": "Power Plant",
        "hp": 400,
        "pw": 20,
        "size": 4,
        "cost": 500,
        "color": (132, 90, 54),
    },
}

ENTITY_SPRITE_TYPES = {
    "conyard": "conyard",
    "powerplant": "powerplant",
    "barracks": "barracks",
    "warfactory": "warfactory",
    "refinery": "refinery",
    "turret": "turret",
    "tesla": "tesla",
    "radar": "radar",
    "conscript": "troop",
    "gi": "troop",
    "dog": "dog",
    "tesla_trooper": "tesla_trooper",
    "rhino": "rhino",
    "grizzly": "rhino_0",
    "v3": "v3",
    "apocalypse": "apocalypse",
    "prism": "apocalypse",
}

BUILD_KEYS = {
    pygame.K_1: "powerplant",
    pygame.K_KP_1: "powerplant",
    pygame.K_2: "barracks",
    pygame.K_KP_2: "barracks",
    pygame.K_3: "warfactory",
    pygame.K_KP_3: "warfactory",
    pygame.K_4: "refinery",
    pygame.K_KP_4: "refinery",
    pygame.K_5: "turret",
    pygame.K_KP_5: "turret",
    pygame.K_6: "tesla",
    pygame.K_KP_6: "tesla",
    pygame.K_7: "radar",
    pygame.K_KP_7: "radar",
    pygame.K_8: "wall",
    pygame.K_KP_8: "wall",
}

TRAIN_KEYS = {
    pygame.K_q: "conscript",
    pygame.K_w: "dog",
    pygame.K_e: "tesla_trooper",
    pygame.K_a: "rhino",
    pygame.K_s: "v3",
    pygame.K_d: "apocalypse",
}


@dataclass
class Camera:
    x: float = 360
    y: float = 620
    zoom: float = 1.0


@dataclass
class Entity:
    id: int
    kind: str
    type: str
    team: str
    x: float
    y: float
    w: float = 0
    h: float = 0
    hp: float = 1
    max_hp: float = 1
    atk: float = 0
    atk_spd: float = 99
    atk_timer: float = 0
    range: float = 0
    sight: float = 100
    spd: float = 0
    size: float = 10
    color: tuple = (220, 60, 40)
    pw: int = 0
    tx: float = 0
    ty: float = 0
    target_id: int | None = None
    selected: bool = False
    attack_move: bool = False
    state: str = "idle"
    facing: float = 0
    rally_x: float = 0
    rally_y: float = 0
    path: list[tuple[float, float]] = field(default_factory=list)
    path_goal: tuple[float, float] | None = None

    def center(self):
        return self.x + self.w / 2, self.y + self.h / 2

    def rect(self):
        return pygame.Rect(round(self.x), round(self.y), round(self.w), round(self.h))


@dataclass
class Ore:
    x: float
    y: float
    available: bool = True
    respawn: float = 0


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    ttl: float
    color: tuple
    size: float = 3
    text: str | None = None


@dataclass
class TeslaZap:
    points: list[tuple[float, float]]
    ttl: float
    max_ttl: float
    color: tuple
    width: float = 3


@dataclass
class Button:
    rect: pygame.Rect
    label: str
    action: str
    kind: str


class NavigationGrid:
    def __init__(self, world_w, world_h, tile_size):
        self.world_w = world_w
        self.world_h = world_h
        self.tile_size = tile_size
        self.cols = math.ceil(world_w / tile_size)
        self.rows = math.ceil(world_h / tile_size)
        self.static_blocked = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.building_occupied = [[False for _ in range(self.cols)] for _ in range(self.rows)]

    def reset_building_occupancy(self):
        self.building_occupied = [[False for _ in range(self.cols)] for _ in range(self.rows)]

    def is_blocked_pixel(self, r, g, b):
        if r > 170 and g > 80 and g < 140 and b < 140 and (r - b) > 70 and (g - b) > 20:
            return True
        if r > 145 and g > 50 and g < 130 and b < 60 and (r - g) > 35:
            return True
        if r < 30 and g < 30 and b < 20:
            return True
        return False

    def generate_from_map(self, map_surface):
        stride = max(1, self.tile_size // 2)
        for gy in range(self.rows):
            for gx in range(self.cols):
                px = gx * self.tile_size
                py = gy * self.tile_size
                blocked_count = 0
                total = 0
                for dy in range(0, self.tile_size, stride):
                    for dx in range(0, self.tile_size, stride):
                        wx = px + dx
                        wy = py + dy
                        if wx >= self.world_w or wy >= self.world_h:
                            continue
                        c = map_surface.get_at((wx, wy))
                        if c.a < 128:
                            continue
                        total += 1
                        if self.is_blocked_pixel(c.r, c.g, c.b):
                            blocked_count += 1
                if total > 0 and blocked_count / total > 0.50:
                    self.static_blocked[gy][gx] = True

    def rebuild_building_occupancy(self, entities):
        self.reset_building_occupancy()
        for entity in entities:
            if entity.kind == "structure" and entity.hp > 0:
                self.occupy_rect(entity.rect().inflate(8, 8))

    def occupy_rect(self, rect):
        start_gx = max(0, rect.left // self.tile_size)
        end_gx = min(self.cols - 1, (rect.right - 1) // self.tile_size)
        start_gy = max(0, rect.top // self.tile_size)
        end_gy = min(self.rows - 1, (rect.bottom - 1) // self.tile_size)
        for gy in range(start_gy, end_gy + 1):
            for gx in range(start_gx, end_gx + 1):
                self.building_occupied[gy][gx] = True

    def cell(self, wx, wy):
        return int(wx // self.tile_size), int(wy // self.tile_size)

    def cell_center(self, gx, gy):
        return (
            gx * self.tile_size + self.tile_size / 2,
            gy * self.tile_size + self.tile_size / 2,
        )

    def in_bounds(self, gx, gy):
        return 0 <= gx < self.cols and 0 <= gy < self.rows

    def is_static_walkable(self, gx, gy):
        return self.in_bounds(gx, gy) and not self.static_blocked[gy][gx]

    def is_walkable_cell(self, gx, gy, ignore_buildings=False):
        if not self.is_static_walkable(gx, gy):
            return False
        return ignore_buildings or not self.building_occupied[gy][gx]

    def is_walkable_world(self, wx, wy, ignore_buildings=False):
        if wx < 0 or wy < 0 or wx >= self.world_w or wy >= self.world_h:
            return False
        return self.is_walkable_cell(*self.cell(wx, wy), ignore_buildings)

    def rect_walkable_for_building(self, rect):
        start_gx = max(0, rect.left // self.tile_size)
        end_gx = min(self.cols - 1, (rect.right - 1) // self.tile_size)
        start_gy = max(0, rect.top // self.tile_size)
        end_gy = min(self.rows - 1, (rect.bottom - 1) // self.tile_size)
        for gy in range(start_gy, end_gy + 1):
            for gx in range(start_gx, end_gx + 1):
                if not self.is_walkable_cell(gx, gy):
                    return False
        return True

    def nearest_walkable_cell(self, gx, gy, max_radius=18):
        if self.is_walkable_cell(gx, gy):
            return gx, gy
        for radius in range(1, max_radius + 1):
            candidates = []
            for x in range(gx - radius, gx + radius + 1):
                candidates.append((x, gy - radius))
                candidates.append((x, gy + radius))
            for y in range(gy - radius + 1, gy + radius):
                candidates.append((gx - radius, y))
                candidates.append((gx + radius, y))
            for cx, cy in candidates:
                if self.is_walkable_cell(cx, cy):
                    return cx, cy
        return None

    def find_path(self, start_world, goal_world):
        start = self.nearest_walkable_cell(*self.cell(*start_world))
        goal = self.nearest_walkable_cell(*self.cell(*goal_world))
        if not start or not goal:
            return []
        if start == goal:
            return [self.cell_center(*goal)]

        open_heap = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        closed = set()

        while open_heap:
            _, current = heapq.heappop(open_heap)
            if current in closed:
                continue
            if current == goal:
                return self.reconstruct_path(came_from, current)
            closed.add(current)
            for neighbor, step_cost in self.neighbors(current):
                if neighbor in closed:
                    continue
                score = g_score[current] + step_cost
                if score < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = score
                    priority = score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_heap, (priority, neighbor))
        return []

    def neighbors(self, cell):
        gx, gy = cell
        for dx, dy, cost in [
            (1, 0, 1),
            (-1, 0, 1),
            (0, 1, 1),
            (0, -1, 1),
            (1, 1, 1.414),
            (1, -1, 1.414),
            (-1, 1, 1.414),
            (-1, -1, 1.414),
        ]:
            nx, ny = gx + dx, gy + dy
            if not self.is_walkable_cell(nx, ny):
                continue
            if dx and dy:
                if not self.is_walkable_cell(gx + dx, gy) or not self.is_walkable_cell(gx, gy + dy):
                    continue
            yield (nx, ny), cost

    def reconstruct_path(self, came_from, current):
        cells = [current]
        while current in came_from:
            current = came_from[current]
            cells.append(current)
        cells.reverse()
        return [self.cell_center(gx, gy) for gx, gy in cells[1:]]

    def heuristic(self, a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])


@dataclass
class Game:
    screen: pygame.Surface
    clock: pygame.time.Clock
    font: pygame.font.Font
    small: pygame.font.Font
    big: pygame.font.Font
    assets: dict = field(default_factory=dict)
    scaled_assets: dict[tuple[int, int, int], pygame.Surface] = field(default_factory=dict)
    sounds: dict = field(default_factory=dict)
    entities: list[Entity] = field(default_factory=list)
    ore: list[Ore] = field(default_factory=list)
    particles: list[Particle] = field(default_factory=list)
    tesla_zaps: list[TeslaZap] = field(default_factory=list)
    buttons: list[Button] = field(default_factory=list)
    selected_ids: list[int] = field(default_factory=list)
    training_queue: list[str] = field(default_factory=list)
    camera: Camera = field(default_factory=Camera)
    next_id: int = 1
    credits: int = 2000
    power: int = 10
    wave: int = 1
    wave_timer: float = 0
    refinery_timer: float = 0
    training_timer: float = 0
    radar_timer: float = 0
    difficulty: str | None = None
    paused: bool = False
    game_over: bool = False
    winner: str | None = None
    placing: str | None = None
    repair_mode: bool = False
    repair_target_id: int | None = None
    repair_timer: float = 0
    sell_mode: bool = False
    message: str = "Select a difficulty."
    message_timer: float = 0
    drag_start: tuple | None = None
    drag_pos: tuple | None = None
    panning: bool = False
    pan_start: tuple = (0, 0)
    pan_cam: tuple = (0, 0)
    map_surface: pygame.Surface | None = None
    nav_grid: NavigationGrid = field(default_factory=lambda: NavigationGrid(WORLD_W, WORLD_H, NAV_TILE))
    debug_nav: bool = False
    music_mode: str | None = None
    music_channel: pygame.mixer.Channel | None = None
    command_voice_timer: float = 0
    base_warning_timer: float = 0
    active_tab: str = "bldg"
    paused_buttons: list[Button] = field(default_factory=list)
    difficulty_buttons: list[Button] = field(default_factory=list)
    muted: bool = False
    sfx_volume: float = 1.0
    cheat_buffer: str = ""
    menu_hover_key: str | None = None
    nav_vis_surface: pygame.Surface | None = None
    show_nav_vis: bool = False
    _menu_was_pressed: bool = False

    def uid(self):
        value = self.next_id
        self.next_id += 1
        return value

    def load_assets(self):
        names = {
            "map": "Map.png",
            "red_conyard": "Red_Motherhall.png",
            "blue_conyard": "Blue_Motherhall.png",
            "red_powerplant": "Red_Power_Plant.png",
            "blue_powerplant": "Blue_Power_Plant.png",
            "red_refinery": "Red_Refinery.png",
            "blue_refinery": "Blue_Refinery.png",
            "red_barracks": "Red_Infantry.png",
            "blue_barracks": "Blue_Infantry.png",
            "red_warfactory": "Red_Barrack.png",
            "blue_warfactory": "Blue_Barrack.png",
            "red_radar": "Red_Radar.png",
            "blue_radar": "Blue_Radar.png",
            "red_tesla": "Red_Tesla_Coil.png",
            "blue_tesla": "Blue_Tesla_Coil.png",
            "red_turret": "Red_Turret.png",
            "blue_turret": "Blue_Turret.png",
            "red_apocalypse": "Red_Apocalypse.png",
            "red_v3": "Red_V3.png",
            "red_dog": "Red_War_Dog.png",
            "red_tesla_trooper": "Red_Tesla_Trooper.png",
            "red_troop": "red_troop_logo.png",
            "blue_troop": "blue_troop_logo.png",
            "red_rhino": "Red_Rhino.png",
            "blue_apocalypse": "Blue_Apocalypse.png",
        }
        for i in range(8):
            names[f"red_rhino_{i}"] = f"Rhino_Red_{i}.png"
            names[f"blue_rhino_{i}"] = f"Rhino_Blue_{i}.png"
        for key, filename in names.items():
            path = get_web_path(ASSET_DIR, filename)
            if path and os.path.exists(path):
                try:
                    self.assets[key] = pygame.image.load(path).convert_alpha()
                except pygame.error:
                    pass
        if "map" in self.assets:
            self.map_surface = pygame.transform.smoothscale(
                self.assets["map"], (WORLD_W, WORLD_H)
            )
        else:
            self.map_surface = self.create_fallback_map()

    def create_fallback_map(self):
        surf = pygame.Surface((WORLD_W, WORLD_H))
        surf.fill((50, 120, 50))
        return surf

    def load_sounds(self):
        if not pygame.mixer.get_init():
            return
        pygame.mixer.set_reserved(1)
        self.music_channel = pygame.mixer.Channel(0)
        names = {
            "click": "web_audio/Clicking_Sound.ogg",
            "menu_music": "web_audio/Landing_Page_Song.ogg",
            "theme": "web_audio/Theme_Song.ogg",
            "build_start": "web_audio/building.ogg",
            "construction_done": "web_audio/construction-completed.ogg",
            "new_options": "web_audio/new-construction-options.ogg",
            "insufficient": "web_audio/insufficient-balance.ogg",
            "unit_ready": "web_audio/unit-ready.ogg",
            "move": "web_audio/moving-out.ogg",
            "affirmative": "web_audio/affirmative.ogg",
            "yes_commander": "web_audio/yes-commander.ogg",
            "yes_sir": "web_audio/yes-sir.ogg",
            "absolutely": "web_audio/absolutely.ogg",
            "cancel": "web_audio/cancel.ogg",
            "hold": "web_audio/on-hold.ogg",
            "base_danger": "web_audio/our-base-is-in-danger.ogg",
            "dog": "web_audio/dog_sound.ogg",
            "victory": "web_audio/congratulations.ogg",
            "defeat": "web_audio/Loosing_Sound.ogg",
        }
        for key, filename in names.items():
            path = get_web_path(SOUND_DIR, filename)
            if not path:
                print(f"Warning: Sound file not found: {filename}")
                continue
            try:
                self.sounds[key] = pygame.mixer.Sound(path)
            except pygame.error as exc:
                print(f"Warning: Could not load sound {filename}: {exc}")

    def play_sfx(self, key):
        if not self.muted and key in self.sounds:
            self.sounds[key].set_volume(self.sfx_volume)
            self.sounds[key].play()

    def play_music(self, key):
        if key == "menu_music" and "menu_music" in self.sounds:
            self.music_mode = "menu"
            self.music_channel.play(self.sounds["menu_music"], loops=-1)
        elif key == "theme" and "theme" in self.sounds:
            self.music_mode = "battle"
            self.music_channel.play(self.sounds["theme"], loops=-1)
        elif key == "none":
            self.music_mode = None
            self.music_channel.stop()

    def selected(self):
        return [e for e in self.entities if e.id in self.selected_ids and e.hp > 0]

    def closest_visible_enemy(self, unit):
        return min(
            (
                target
                for target in self.entities
                if target.team != unit.team
                and target.hp > 0
                and entity_distance(unit, target) <= unit.sight
            ),
            key=lambda target: entity_distance(unit, target),
            default=None,
        )

    def event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset_game()
            return

        if self.difficulty is None:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP_1):
                    self.start_game("easy")
                elif event.key in (pygame.K_2, pygame.K_KP_2):
                    self.start_game("medium")
                elif event.key in (pygame.K_3, pygame.K_KP_3):
                    self.start_game("hard")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button in self.difficulty_buttons:
                    if button.rect.collidepoint(event.pos):
                        self.start_game(button.action)
                        break
            return

        if self.paused:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                self.paused = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in self.paused_buttons:
                    if btn.rect.collidepoint(event.pos):
                        if btn.action == "resume":
                            self.paused = False
                        elif btn.action == "mute":
                            self.muted = not self.muted
            return

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.paused = True
            elif event.key == pygame.K_ESCAPE:
                self.placing = None
                self.repair_mode = False
                self.sell_mode = False
                self.selected_ids = []
            elif event.key == pygame.K_g:
                self.debug_nav = not self.debug_nav
            elif event.key == pygame.K_DELETE:
                self.sell_selected()
            elif event.key == pygame.K_h:
                self.placing = None
                self.sell_mode = False
                self.repair_mode = not self.repair_mode
            elif event.key == pygame.K_x:
                self.placing = None
                self.repair_mode = False
                self.sell_mode = not self.sell_mode
            elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.camera.zoom = min(2.0, self.camera.zoom + 0.1)
            elif event.key == pygame.K_MINUS:
                self.camera.zoom = max(0.5, self.camera.zoom - 0.1)
            elif event.key in BUILD_KEYS:
                self.placing = BUILD_KEYS[event.key]
                self.repair_mode = False
                self.sell_mode = False
            elif event.key in TRAIN_KEYS:
                self.train_unit(TRAIN_KEYS[event.key])

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left
                if event.pos[0] >= VIEW_W:
                    for button in self.buttons:
                        if not button.rect.collidepoint(event.pos):
                            continue
                        if button.kind == "tab":
                            self.active_tab = button.action
                        elif button.kind == "build":
                            self.placing = button.action
                            self.repair_mode = False
                            self.sell_mode = False
                        elif button.kind == "train":
                            self.train_unit(button.action)
                        elif button.kind == "tool":
                            if button.action == "repair":
                                self.repair_mode = not self.repair_mode
                                self.sell_mode = False
                            elif button.action == "sell":
                                self.sell_mode = not self.sell_mode
                                self.repair_mode = False
                            self.placing = None
                        return
                    return
                if self.placing:
                    self.place_building(event.pos)
                elif self.repair_mode:
                    self.start_repair(event.pos)
                elif self.sell_mode:
                    self.start_sell(event.pos)
                else:
                    self.drag_start = event.pos
                    self.drag_pos = event.pos
            elif event.button == 3: # Right
                if event.pos[0] < VIEW_W:
                    self.handle_right_click(event.pos)
            elif event.button == 2: # Middle
                self.panning = True
                self.pan_start = event.pos
                self.pan_cam = (self.camera.x, self.camera.y)

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                if not self.placing and not self.repair_mode and not self.sell_mode:
                    self.finish_selection()
                self.drag_start = None
                self.drag_pos = None
            elif event.button == 2:
                self.panning = False

        if event.type == pygame.MOUSEMOTION:
            if self.drag_start:
                self.drag_pos = event.pos
            if self.panning:
                dx = (event.pos[0] - self.pan_start[0]) / self.camera.zoom
                dy = (event.pos[1] - self.pan_start[1]) / self.camera.zoom
                self.camera.x = self.pan_cam[0] - dx
                self.camera.y = self.pan_cam[1] - dy

    def handle_right_click(self, pos):
        if self.placing or self.repair_mode or self.sell_mode:
            self.placing = None
            self.repair_mode = False
            self.sell_mode = False
            return

        # Convert screen pos to world pos
        wx = (pos[0] - VIEW_W / 2) / self.camera.zoom + self.camera.x
        wy = (pos[1] - TOP_H - VIEW_H / 2) / self.camera.zoom + self.camera.y

        selected = self.selected()
        if not selected:
            return

        # Check if we clicked an enemy entity
        target = None
        for e in self.entities:
            if e.team != TEAM_RED and e.hp > 0:
                if e.rect().collidepoint(wx, wy):
                    target = e
                    break

        if target:
            # Attack target
            for e in selected:
                if e.kind == "unit":
                    e.state = "attack"
                    e.target_id = target.id
                    e.path = []
                    e.path_goal = (target.x + target.w / 2, target.y + target.h / 2)
                    self.play_sfx("move")
        else:
            units = [e for e in selected if e.kind == "unit"]
            columns = math.ceil(math.sqrt(len(units)))
            rows = math.ceil(len(units) / columns) if units else 0
            for index, e in enumerate(units):
                row, column = divmod(index, columns)
                goal = (
                    clamp(wx + (column - (columns - 1) / 2) * TILE * 2, TILE, WORLD_W - TILE),
                    clamp(wy + (row - (rows - 1) / 2) * TILE * 2, TILE, WORLD_H - TILE),
                )
                e.state = "move"
                e.target_id = None
                e.path = self.nav_grid.find_path((e.x + e.w / 2, e.y + e.h / 2), goal)
                e.path_goal = goal
            if units:
                self.play_sfx("move")

    def finish_selection(self):
        if not self.drag_start:
            return
        
        x1, y1 = self.drag_start
        x2, y2 = self.drag_pos or self.drag_start
        
        rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x1-x2), abs(y1-y2))
        is_click = abs(x2 - x1) <= 4 and abs(y2 - y1) <= 4
        
        self.selected_ids = []
        for entity in self.entities:
            entity.selected = False
        closest = None
        closest_distance = 14
        for e in self.entities:
            if e.kind == "unit" and e.team == TEAM_RED:
                sx = (e.x + e.w/2 - self.camera.x) * self.camera.zoom + VIEW_W / 2
                sy = (e.y + e.h/2 - self.camera.y) * self.camera.zoom + TOP_H + VIEW_H / 2
                if is_click:
                    distance = math.hypot(sx - x2, sy - y2)
                    if distance < closest_distance:
                        closest = e
                        closest_distance = distance
                elif rect.collidepoint(sx, sy):
                    self.selected_ids.append(e.id)
                    e.selected = True
        if closest:
            self.selected_ids.append(closest.id)
            closest.selected = True

    def place_building(self, pos):
        # Convert screen pos to world pos
        wx = (pos[0] - VIEW_W / 2) / self.camera.zoom + self.camera.x
        wy = (pos[1] - TOP_H - VIEW_H / 2) / self.camera.zoom + self.camera.y
        
        # Snap to grid
        gx, gy = wx // TILE, wy // TILE
        bx, by = gx * TILE, gy * TILE
        
        data = STRUCT_DEFS[self.placing]
        bw = data.get("w_tiles", data["size"]) * TILE
        bh = data.get("h_tiles", data["size"]) * TILE
        rect = pygame.Rect(bx, by, bw, bh)
        
        if self.credits < data["cost"]:
            self.play_sfx("insufficient")
            return

        if not self.nav_grid.rect_walkable_for_building(rect):
            return

        # Create structure
        e = Entity(
            id=self.uid(),
            kind="structure",
            type=self.placing,
            team=TEAM_RED,
            x=float(bx),
            y=float(by),
            w=float(bw),
            h=float(bh),
            hp=float(data["hp"]),
            max_hp=float(data["hp"]),
            pw=data["pw"],
            color=data["color"]
        )
        self.entities.append(e)
        self.credits -= data["cost"]
        self.nav_grid.rebuild_building_occupancy(self.entities)
        self.play_sfx("build_start")
        self.placing = None

    def train_unit(self, unit_type):
        data = UNIT_DEFS[unit_type]
        if self.credits < data["cost"]:
            self.play_sfx("insufficient")
            return
        
        # Check requirements
        if unit_type in ("conscript", "dog", "tesla_trooper"):
            if not any(e.type == "barracks" for e in self.entities if e.team == TEAM_RED):
                return
        if unit_type in ("rhino", "v3", "apocalypse"):
            if not any(e.type == "warfactory" for e in self.entities if e.team == TEAM_RED):
                return

        self.credits -= data["cost"]
        self.training_queue.append(unit_type)
        self.play_sfx("click")

    def start_repair(self, pos):
        wx = (pos[0] - VIEW_W / 2) / self.camera.zoom + self.camera.x
        wy = (pos[1] - TOP_H - VIEW_H / 2) / self.camera.zoom + self.camera.y
        for e in self.entities:
            if e.kind == "structure" and e.team == TEAM_RED and e.rect().collidepoint(wx, wy):
                self.repair_target_id = e.id
                self.repair_mode = False
                self.repair_timer = 0
                return
        self.repair_mode = False

    def start_sell(self, pos):
        wx = (pos[0] - VIEW_W / 2) / self.camera.zoom + self.camera.x
        wy = (pos[1] - TOP_H - VIEW_H / 2) / self.camera.zoom + self.camera.y
        for e in self.entities:
            if e.kind == "structure" and e.team == TEAM_RED and e.rect().collidepoint(wx, wy):
                self.sell_entity(e)
                self.sell_mode = False
                return
        self.sell_mode = False

    def sell_selected(self):
        for eid in self.selected_ids:
            for e in self.entities:
                if e.id == eid and e.kind == "structure" and e.team == TEAM_RED:
                    self.sell_entity(e)
        self.selected_ids = []

    def sell_entity(self, e):
        data = STRUCT_DEFS[e.type]
        self.credits += int(data["cost"] * 0.5)
        e.hp = 0
        self.nav_grid.rebuild_building_occupancy(self.entities)
        self.play_sfx("cancel")

    def reset_game(self):
        self.difficulty = None
        self.entities = []
        self.ore = []
        self.selected_ids = []
        self.training_queue = []
        self.training_timer = 0
        self.wave_timer = 0
        self.paused = False
        self.placing = None
        self.repair_mode = False
        self.repair_target_id = None
        self.sell_mode = False
        self.credits = 2000
        self.game_over = False
        self.winner = None
        self.next_id = 1
        self.wave = 1
        self.nav_grid.rebuild_building_occupancy(self.entities)

    def start_game(self, diff_key):
        self.difficulty = diff_key
        diff = DIFFICULTIES[diff_key]
        self.credits = diff["start_credits"]

        self.entities = []
        self.ore = []
        self.selected_ids = []
        self.training_queue = []
        self.training_timer = 0
        self.wave = 1
        self.wave_timer = 0
        self.paused = False
        self.game_over = False
        self.winner = None
        self.placing = None
        self.repair_mode = False
        self.repair_target_id = None
        self.sell_mode = False
        self.next_id = 1
        self.camera = Camera(x=WORLD_W / 2, y=WORLD_H / 2, zoom=0.72)

        self.add_structure("barracks", TEAM_RED, 200, 480)
        self.add_structure("conyard", TEAM_RED, 300, 600)
        self.add_structure("powerplant", TEAM_RED, 200, 640)
        self.add_structure("warfactory", TEAM_RED, 500, 480)
        for unit_type, x, y in (
            ("conscript", 440, 590),
            ("conscript", 450, 630),
            ("rhino", 500, 650),
        ):
            self.add_unit(unit_type, TEAM_RED, x, y)

        self.add_structure("barracks", TEAM_BLUE, 1120, 140)
        self.add_structure("conyard", TEAM_BLUE, 1240, 120)
        self.add_structure("powerplant", TEAM_BLUE, 1400, 140)
        self.add_structure("warfactory", TEAM_BLUE, 1240, 280)
        for unit_type, x, y in (
            ("gi", 1160, 260),
            ("gi", 1370, 250),
            ("grizzly", 1300, 440),
        ):
            self.add_unit(unit_type, TEAM_BLUE, x, y)

        self.nav_grid.rebuild_building_occupancy(self.entities)
        
        # Spawn some ore
        for _ in range(15):
            self.ore.append(Ore(random.randint(100, WORLD_W-100), random.randint(100, WORLD_H-100)))
            
        self.play_music("theme")
        self.message = f"Battle Started: {diff['label']} Difficulty"
        self.message_timer = 3.0

    def add_structure(self, structure_type, team, x, y):
        data = STRUCT_DEFS[structure_type]
        entity = Entity(
            id=self.uid(),
            kind="structure",
            type=structure_type,
            team=team,
            x=x,
            y=y,
            w=data.get("w_tiles", data["size"]) * TILE,
            h=data.get("h_tiles", data["size"]) * TILE,
            hp=data["hp"],
            max_hp=data["hp"],
            pw=data["pw"],
            color=data["color"],
        )
        self.entities.append(entity)

    def update(self, dt):
        if self.difficulty is None or self.paused:
            return

        # 1. Training
        if self.training_queue:
            self.training_timer += dt
            unit_type = self.training_queue[0]
            data = UNIT_DEFS[unit_type]
            train_time = max(3, data["cost"] / 200)
            if self.training_timer >= train_time:
                if self.spawn_unit(unit_type):
                    self.training_queue.pop(0)
                    self.training_timer = 0
                    self.play_sfx("unit_ready")

        # 2. Wave System
        self.wave_timer += dt
        diff = DIFFICULTIES[self.difficulty]
        if self.wave_timer >= diff["wave_interval"]:
            self.spawn_wave()
            self.wave_timer = 0
            self.wave += 1
            self.play_sfx("base_danger")

        # 3. Entity Updates
        for e in self.entities[:]:
            if e.hp <= 0:
                if e.kind == "structure" and e.type == "conyard":
                    if e.team == TEAM_RED:
                        self.game_over = True
                        self.winner = TEAM_BLUE
                    else:
                        self.game_over = True
                        self.winner = TEAM_RED
                self.entities.remove(e)
                self.nav_grid.rebuild_building_occupancy(self.entities)
                continue

            if e.kind == "unit":
                # Simple AI for enemies
                if e.team == TEAM_BLUE:
                    if e.state == "idle":
                        target = self.closest_visible_enemy(e)
                        if target is None:
                            target = next((s for s in self.entities if s.type == "conyard" and s.team == TEAM_RED), None)
                        if target:
                            e.state = "attack"
                            e.target_id = target.id
                            e.path_goal = (target.x + target.w/2, target.y + target.h/2)
                            e.path = self.nav_grid.find_path((e.x + e.w/2, e.y + e.h/2), e.path_goal)
                    elif e.state == "attack":
                        current_target = next((t for t in self.entities if t.id == e.target_id), None)
                        threat = self.closest_visible_enemy(e)
                        if current_target and current_target.kind == "structure" and threat and threat.kind == "unit":
                            e.target_id = threat.id
                            e.path_goal = (threat.x + threat.w/2, threat.y + threat.h/2)
                            e.path = []
                    
                    if e.state == "attack" and e.target_id:
                        target = next((t for t in self.entities if t.id == e.target_id), None)
                        if not target or target.hp <= 0:
                            e.state = "idle"
                        elif entity_distance(e, target) < e.range:
                            e.atk_timer += dt
                            if e.atk_timer >= e.atk_spd:
                                target.hp -= e.atk
                                e.atk_timer = 0
                                self.particles.append(Particle(target.x + target.w/2, target.y + target.h/2, 0, 0, 0.5, (255, 255, 255)))
                        else:
                            # Move towards target
                            if not e.path:
                                e.path = self.nav_grid.find_path((e.x + e.w/2, e.y + e.h/2), (target.x + target.w/2, target.y + target.h/2))
                            self.advance_unit(e, dt)

                # Red units
                if e.team == TEAM_RED:
                    if e.state == "idle":
                        target = self.closest_visible_enemy(e)
                        if target:
                            e.state = "attack"
                            e.target_id = target.id
                            e.path_goal = (target.x + target.w/2, target.y + target.h/2)
                            e.path = []
                            if self.message_timer <= 0 or self.message != "ENEMY CONTACT - UNITS ENGAGING":
                                self.message = "ENEMY CONTACT - UNITS ENGAGING"
                                self.message_timer = 3.0
                                self.play_sfx("base_danger")

                    if e.state == "move" and e.path:
                        self.advance_unit(e, dt)
                        if not e.path:
                            e.state = "idle"
                    
                    if e.state == "attack" and e.target_id:
                        target = next((t for t in self.entities if t.id == e.target_id), None)
                        if not target or target.hp <= 0:
                            e.state = "idle"
                        elif entity_distance(e, target) < e.range:
                            e.atk_timer += dt
                            if e.atk_timer >= e.atk_spd:
                                target.hp -= e.atk
                                e.atk_timer = 0
                                self.particles.append(Particle(target.x + target.w/2, target.y + target.h/2, 0, 0, 0.5, (255, 255, 255)))
                        else:
                            if not e.path:
                                e.path = self.nav_grid.find_path((e.x + e.w/2, e.y + e.h/2), (target.x + target.w/2, target.y + target.h/2))
                            self.advance_unit(e, dt)

        # 4. Auto-defenses (Tesla)
        for e in self.entities:
            if e.type in ("tesla", "turret") and e.hp > 0:
                # Find closest enemy
                closest = None
                min_dist = e.range
                for target in self.entities:
                    if target.team == TEAM_BLUE and target.hp > 0:
                        dist = entity_distance(e, target)
                        if dist < min_dist:
                            min_dist = dist
                            closest = target
                if closest:
                    e.atk_timer += dt
                    if e.atk_timer >= e.atk_spd:
                        closest.hp -= e.atk
                        e.atk_timer = 0
                        self.tesla_zaps.append(TeslaZap([e.center(), closest.center()], 0.2, 0.2, (100, 200, 255)))

        # Update particles
        for p in self.particles[:]:
            p.ttl -= dt
            if p.ttl <= 0:
                self.particles.remove(p)
        for z in self.tesla_zaps[:]:
            z.ttl -= dt
            if z.ttl <= 0:
                self.tesla_zaps.remove(z)

        if self.message_timer > 0:
            self.message_timer -= dt

    def spawn_unit(self, unit_type):
        # Spawn near conyard
        cy = next((e for e in self.entities if e.type == "conyard" and e.team == TEAM_RED), None)
        if not cy:
            return False
        
        # Find random walkable spot near cy
        for _ in range(10):
            rx = cy.x + random.randint(-100, 100)
            ry = cy.y + random.randint(-100, 100)
            if self.nav_grid.is_walkable_world(rx, ry):
                self.add_unit(unit_type, TEAM_RED, rx, ry)
                return True
        return False

    def advance_unit(self, entity, dt):
        if not entity.path:
            return
        gx, gy = entity.path[0]
        dx, dy = gx - (entity.x + entity.w / 2), gy - (entity.y + entity.h / 2)
        distance = math.hypot(dx, dy)
        if distance <= 2:
            entity.x = gx - entity.w / 2
            entity.y = gy - entity.h / 2
            entity.path.pop(0)
            return
        entity.facing = round(
            (math.atan2(dy, dx) + math.pi / 2) / (math.pi / 4)
        ) % 8
        step = min(entity.spd * dt, distance)
        entity.x += dx / distance * step
        entity.y += dy / distance * step
        if step == distance:
            entity.x = gx - entity.w / 2
            entity.y = gy - entity.h / 2
            entity.path.pop(0)

    def add_unit(self, unit_type, team, x, y):
        data = UNIT_DEFS[unit_type]
        entity = Entity(
            id=self.uid(),
            kind="unit",
            type=unit_type,
            team=team,
            x=x,
            y=y,
            w=data["size"],
            h=data["size"],
            hp=data["hp"],
            max_hp=data["hp"],
            atk=data["atk"],
            atk_spd=data["atk_spd"],
            range=data["range"],
            sight=data["sight"],
            spd=data["spd"],
            size=data["size"],
            color=data["color"],
        )
        self.entities.append(entity)

    def spawn_wave(self):
        diff = DIFFICULTIES[self.difficulty]
        count = diff["enemy_count_base"] + (self.wave * diff["enemy_count_per_wave"])
        
        # Spawn enemies at the edge
        for _ in range(count):
            u_type = random.choice(["gi", "grizzly", "prism"])
            data = UNIT_DEFS[u_type]
            ex = random.randint(0, WORLD_W)
            ey = random.randint(0, 200) # Top area
            if self.nav_grid.is_walkable_world(ex, ey):
                e = Entity(
                    id=self.uid(),
                    kind="unit",
                    type=u_type,
                    team=TEAM_BLUE,
                    x=ex, y=ey,
                    w=data["size"], h=data["size"],
                    hp=data["hp"] * diff["enemy_hp"],
                    max_hp=data["hp"] * diff["enemy_hp"],
                    atk=data["atk"] * diff["enemy_atk"],
                    atk_spd=data["atk_spd"],
                    range=data["range"], sight=data["sight"],
                    spd=data["spd"], size=data["size"],
                    color=data["color"]
                )
                self.entities.append(e)

    def draw(self):
        self.screen.fill((20, 20, 20))
        
        # 1. World View
        view_rect = pygame.Rect(0, TOP_H, VIEW_W, VIEW_H)
        pygame.draw.rect(self.screen, (0, 0, 0), view_rect)
        
        # Render Map
        if self.map_surface:
            # Simple camera transform
            scaled_map = pygame.transform.scale(self.map_surface, (int(WORLD_W * self.camera.zoom), int(WORLD_H * self.camera.zoom)))
            off_x = VIEW_W / 2 - self.camera.x * self.camera.zoom
            off_y = TOP_H + VIEW_H / 2 - self.camera.y * self.camera.zoom
            self.screen.blit(scaled_map, (off_x, off_y))
        
        # Render Entities
        for e in self.entities:
            if e.hp <= 0: continue
            # Project to screen
            sx = (e.x + e.w/2 - self.camera.x) * self.camera.zoom + VIEW_W / 2
            sy = (e.y + e.h/2 - self.camera.y) * self.camera.zoom + TOP_H + VIEW_H / 2
            
            sw, sh = e.w * self.camera.zoom, e.h * self.camera.zoom
            rect = pygame.Rect(sx - sw/2, sy - sh/2, sw, sh)
            draw_rect = rect
            if e.kind == "unit":
                min_size = TILE * (1.5 if e.type in ("conscript", "gi", "dog", "tesla_trooper") else 2)
                sprite_size = max(e.w, min_size) * self.camera.zoom
                draw_rect = pygame.Rect(0, 0, round(sprite_size), round(sprite_size))
                draw_rect.center = (round(sx), round(sy))
            
            # Only draw if on screen
            if view_rect.colliderect(draw_rect):
                team_name = "red" if e.team == TEAM_RED else "blue"
                sprite_type = ENTITY_SPRITE_TYPES.get(e.type, e.type)
                if e.type in ("rhino", "grizzly"):
                    sprite = self.assets.get(
                        f"{team_name}_rhino_{int(e.facing) % 8}"
                    )
                    if sprite is None:
                        sprite = self.assets.get(f"{team_name}_rhino")
                else:
                    sprite = self.assets.get(f"{team_name}_{sprite_type}")
                if sprite:
                    self.blit_fit(sprite, draw_rect, 1.0)
                else:
                    pygame.draw.rect(self.screen, e.color, draw_rect)
                if e.selected:
                    pygame.draw.rect(self.screen, (255, 255, 255), draw_rect, 2)
                
                # HP bar
                hp_w = draw_rect.width * (e.hp / e.max_hp)
                pygame.draw.rect(self.screen, (200, 0, 0), (draw_rect.left, draw_rect.top - 6, draw_rect.width, 4))
                pygame.draw.rect(self.screen, (0, 200, 0), (draw_rect.left, draw_rect.top - 6, hp_w, 4))

        # Particles and Zaps
        for p in self.particles:
            sx = (p.x - self.camera.x) * self.camera.zoom + VIEW_W / 2
            sy = (p.y - self.camera.y) * self.camera.zoom + TOP_H + VIEW_H / 2
            pygame.draw.circle(self.screen, p.color, (round(sx), round(sy)), round(p.size * self.camera.zoom))
        for z in self.tesla_zaps:
            pts = []
            for px, py in z.points:
                sx = (px - self.camera.x) * self.camera.zoom + VIEW_W / 2
                sy = (py - self.camera.y) * self.camera.zoom + TOP_H + VIEW_H / 2
                pts.append((sx, sy))
            if len(pts) >= 2:
                pygame.draw.lines(self.screen, z.color, False, pts, round(z.width * self.camera.zoom))

        # 2. UI
        self.draw_topbar()
        self.draw_sidebar()
        self.draw_bottombar()
        
        if self.game_over:
            self.draw_center_banner("GAME OVER", f"Winner: {self.winner.upper()}")
        elif self.difficulty is None:
            self.draw_difficulty_menu()
        elif self.paused:
            self.draw_pause_panel()
        
        if self.message_timer > 0:
            msg_surf = self.font.render(self.message, True, (255, 255, 255))
            self.screen.blit(msg_surf, (VIEW_W // 2 - msg_surf.get_width() // 2, TOP_H + 20))

    def draw_topbar(self):
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, SCREEN_W, TOP_H))
        title = self.font.render("Soviets vs Allies", True, (200, 200, 200))
        self.screen.blit(title, (20, TOP_H // 2 - title.get_height() // 2))

    def draw_pause_panel(self):
        self.paused_buttons = []
        panel = pygame.Rect(VIEW_W // 4, TOP_H + 100, VIEW_W // 2, VIEW_H - 200)
        pygame.draw.rect(self.screen, (40, 20, 60), panel, border_radius=10)
        pygame.draw.rect(self.screen, (120, 40, 175), panel, 3, border_radius=10)
        
        title = self.big.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 40)))
        
        # Resume button
        res_rect = pygame.Rect(panel.centerx - 60, panel.centery, 120, 40)
        pygame.draw.rect(self.screen, (80, 40, 120), res_rect, border_radius=5)
        res_txt = self.font.render("RESUME", True, (255, 255, 255))
        self.screen.blit(res_txt, res_txt.get_rect(center=res_rect.center))
        self.paused_buttons.append(Button(res_rect, "Resume", "resume", "pause"))
        
        # Mute button
        mute_rect = pygame.Rect(panel.centerx - 60, panel.centery + 50, 120, 40)
        pygame.draw.rect(self.screen, (80, 40, 120), mute_rect, border_radius=5)
        mute_txt = self.font.render("MUTE" if not self.muted else "UNMUTE", True, (255, 255, 255))
        self.screen.blit(mute_txt, mute_txt.get_rect(center=mute_rect.center))
        self.paused_buttons.append(Button(mute_rect, "Mute", "mute", "pause"))

    def blit_fit(self, surf, rect, scale):
        w, h = rect.width, rect.height
        sw, sh = surf.get_size()
        aspect = sw / sh
        if aspect > (w / h):
            nw, nh = w, w / aspect
        else:
            nw, nh = h * aspect, h
        size = (max(1, round(nw)), max(1, round(nh)))
        cache_key = (id(surf), *size)
        scaled = self.scaled_assets.get(cache_key)
        if scaled is None:
            scaled = pygame.transform.smoothscale(surf, size)
            self.scaled_assets[cache_key] = scaled
        self.screen.blit(scaled, scaled.get_rect(center=rect.center))

    def draw_hammer_icon(self, rect):
        pygame.draw.rect(self.screen, (100, 150, 255), rect, border_radius=2)
        pygame.draw.line(self.screen, (255, 255, 255), rect.topleft, rect.bottomright, 3)

    def draw_sell_icon(self, rect):
        pygame.draw.rect(self.screen, (200, 100, 50), rect, border_radius=2)
        pygame.draw.line(self.screen, (255, 255, 255), rect.topleft, rect.bottomright, 3)

    def draw_sidebar(self):
        x = VIEW_W
        pygame.draw.rect(self.screen, (22, 10, 30), (x, TOP_H, SIDEBAR_W, VIEW_H))
        pygame.draw.line(self.screen, (120, 40, 175), (x, TOP_H), (x, TOP_H + VIEW_H), 3)
        
        title = self.font.render("YURI'S COMMAND", True, (245, 185, 45))
        self.screen.blit(title, (x + 22, TOP_H + 12))
        
        credit_label = self.small.render("CREDITS", True, (185, 145, 85))
        self.screen.blit(credit_label, (x + 22, TOP_H + 36))
        credit_val = self.font.render(f"${self.credits}", True, (255, 220, 90))
        self.screen.blit(credit_val, (x + 22, TOP_H + 52))
        
        self.draw_minimap(x + 22, TOP_H + 80)
        self.buttons = []
        
        tabs = [("bldg", "BLDG"), ("defn", "DEFN"), ("inf", "INF"), ("veh", "VEH")]
        tab_w, tab_h, tab_gap = 50, 24, 6
        start_tx, tab_y = x + 22, TOP_H + 206
        for idx, (tab_id, label_str) in enumerate(tabs):
            tx = start_tx + idx * (tab_w + tab_gap)
            rect = pygame.Rect(tx, tab_y, tab_w, tab_h)
            is_active = (self.active_tab == tab_id)
            bg_color = (130, 45, 185) if is_active else (35, 15, 50)
            border_color = (245, 185, 45) if is_active else (85, 45, 115)
            text_color = (255, 255, 255) if is_active else (155, 120, 175)
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
            pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=4)
            tab_lbl = self.small.render(label_str, True, text_color)
            self.screen.blit(tab_lbl, tab_lbl.get_rect(center=rect.center))
            self.buttons.append(Button(rect, label_str, tab_id, "tab"))

        power_y, power_h, power_w, power_x = TOP_H + 238, 320, 10, x + 8
        pygame.draw.rect(self.screen, (12, 5, 20), (power_x - 2, power_y - 2, power_w + 4, power_h + 4), border_radius=3)
        
        produced = 10 + sum(e.pw for e in self.entities if e.kind == "structure" and e.team == TEAM_RED and e.pw > 0)
        consumed = sum(abs(e.pw) for e in self.entities if e.kind == "structure" and e.team == TEAM_RED and e.pw < 0)
        
        segments = 32
        seg_h = power_h / segments
        for s in range(segments):
            sy = power_y + power_h - (s + 1) * seg_h
            ratio = s / segments
            color = (205, 35, 20) if ratio < 0.3 else (235, 185, 35) if ratio < 0.5 else (35, 195, 40)
            pygame.draw.rect(self.screen, color, (power_x, sy + 1, power_w, seg_h - 2))
            
        if produced > 0:
            ptr_ratio = clamp(consumed / produced, 0.05, 0.95)
            ptr_y = power_y + power_h - ptr_ratio * power_h
        else:
            ptr_y = power_y + power_h - 10
        pygame.draw.polygon(self.screen, (245, 185, 45), [(power_x - 7, ptr_y - 5), (power_x - 1, ptr_y), (power_x - 7, ptr_y + 5)])
        pygame.draw.line(self.screen, (245, 185, 45), (power_x - 2, ptr_y), (power_x + power_w + 2, ptr_y), 2)

        if self.active_tab == "bldg":
            active_items = [("powerplant", "1", "Build"), ("barracks", "2", "Build"), ("warfactory", "3", "Build"), ("refinery", "4", "Build"), ("radar", "7", "Build"), ("repair", "H", "Tool"), ("sell", "X", "Tool")]
        elif self.active_tab == "defn":
            active_items = [("turret", "5", "Build"), ("tesla", "6", "Build"), ("wall", "8", "Build")]
        elif self.active_tab == "inf":
            active_items = [("conscript", "Q", "Train"), ("dog", "W", "Train"), ("tesla_trooper", "E", "Train")]
        else:
            active_items = [("rhino", "A", "Train"), ("v3", "S", "Train"), ("apocalypse", "D", "Train")]
            
        grid_start_x, grid_start_y, card_w, card_h, gap_x, gap_y = x + 24, TOP_H + 238, 104, 74, 8, 8
        for idx, (item_id, hotkey, item_kind) in enumerate(active_items):
            col, row = idx % 2, idx // 2
            cx, cy = grid_start_x + col * (card_w + gap_x), grid_start_y + row * (card_h + gap_y)
            card_rect = pygame.Rect(cx, cy, card_w, card_h)
            
            locked = False
            if item_kind == "Train":
                if item_id in ("conscript", "dog", "tesla_trooper") and not any(e.type == "barracks" for e in self.entities if e.team == TEAM_RED): locked = True
                if item_id in ("rhino", "v3", "apocalypse") and not any(e.type == "warfactory" for e in self.entities if e.team == TEAM_RED): locked = True
                        
            data = STRUCT_DEFS[item_id] if item_kind == "Build" else UNIT_DEFS[item_id] if item_kind == "Train" else {"repair": {"name": "Repair", "cost": REPAIR_COST}, "sell": {"name": "Sell", "cost": 0}}[item_id]
            cost = data["cost"]
            
            mouse_pos = pygame.mouse.get_pos()
            hovered = card_rect.collidepoint(mouse_pos)
            is_active_placing = (self.placing == item_id) or (item_id == "repair" and self.repair_mode) or (item_id == "sell" and self.sell_mode)
            
            bg_color = (15, 8, 22) if locked else (25, 12, 38)
            border_color = (245, 185, 45) if is_active_placing else (165, 80, 220) if hovered and not locked else (90, 50, 115)
            pygame.draw.rect(self.screen, bg_color, card_rect, border_radius=4)
            pygame.draw.rect(self.screen, border_color, card_rect, 2, border_radius=4)
            
            icon_key = f"red_{item_id}"
            if item_id == "conscript": icon_key = "red_troop"
            elif item_id == "tesla_trooper": icon_key = "red_tesla_trooper"
            icon_rect = pygame.Rect(cx + 12, cy + 6, card_w - 24, 46)
            
            asset = self.assets.get(icon_key)
            if item_id == "repair": self.draw_hammer_icon(icon_rect)
            elif item_id == "sell": self.draw_sell_icon(icon_rect)
            elif asset: self.blit_fit(asset, icon_rect, 1.0)
            else: pygame.draw.rect(self.screen, (120, 60, 160), icon_rect.inflate(-4, -4), border_radius=2)
            
            if locked or self.credits < cost:
                shade = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                shade.fill((0, 0, 0, 120) if locked else (200, 30, 20, 60))
                self.screen.blit(shade, (cx, cy))
                
            hk_lbl = self.small.render(f"[{hotkey}]", True, (80, 200, 240))
            self.screen.blit(hk_lbl, (cx + 6, cy + 4))
            name_lbl = self.small.render(data["name"].upper().split()[0], True, (255, 255, 255))
            self.screen.blit(name_lbl, (cx + 6, cy + 54))
            cost_text = f"${cost}" if cost else "50%"
            cost_lbl = self.small.render(cost_text, True, (245, 185, 45))
            self.screen.blit(cost_lbl, (cx + card_w - cost_lbl.get_width() - 6, cy + 54))
            
            if locked:
                lock_lbl = self.small.render("LOCKED", True, (255, 50, 50))
                pygame.draw.rect(self.screen, (10, 5, 15), (cx + 6, cy + 24, card_w - 12, 18), border_radius=2)
                self.screen.blit(lock_lbl, lock_lbl.get_rect(center=(cx + card_w // 2, cy + 33)))
            elif is_active_placing:
                if int(pygame.time.get_ticks() / 300) % 2 == 0:
                    pygame.draw.rect(self.screen, (12, 5, 20), (cx + 12, cy + 24, card_w - 24, 18), border_radius=2)
                    active_label = "REPAIR" if item_id == "repair" else "SELL" if item_id == "sell" else "READY"
                    ready_lbl = self.small.render(active_label, True, (245, 185, 45))
                    self.screen.blit(ready_lbl, ready_lbl.get_rect(center=(cx + card_w // 2, cy + 33)))
            elif item_kind == "Train" and self.training_queue:
                queue_count = sum(1 for q in self.training_queue if q == item_id)
                if queue_count > 0:
                    if self.training_queue[0] == item_id:
                        train_time = max(3, data["cost"] / 200)
                        pct = clamp(self.training_timer / train_time, 0, 1)
                        wipe_h = round(card_h * (1.0 - pct))
                        if wipe_h > 0:
                            wipe_surf = pygame.Surface((card_w, wipe_h), pygame.SRCALPHA)
                            wipe_surf.fill((0, 0, 0, 150))
                            self.screen.blit(wipe_surf, (cx, cy))
                        pct_lbl = self.small.render(f"{round(pct * 100)}%", True, (255, 255, 255))
                        pygame.draw.rect(self.screen, (12, 5, 20), (cx + card_w - 36, cy + 4, 30, 15), border_radius=2)
                        self.screen.blit(pct_lbl, pct_lbl.get_rect(center=(cx + card_w - 21, cy + 11)))
                    else:
                        hold_lbl = self.small.render(f"Q: {queue_count}", True, (215, 175, 120))
                        pygame.draw.rect(self.screen, (12, 5, 20), (cx + card_w - 36, cy + 4, 30, 15), border_radius=2)
                        self.screen.blit(hold_lbl, hold_lbl.get_rect(center=(cx + card_w - 21, cy + 11)))
                        
            button_kind = "build" if item_kind == "Build" else "train" if item_kind == "Train" else "tool"
            self.buttons.append(Button(card_rect, data["name"], item_id, button_kind))
            
        info_y = TOP_H + VIEW_H - 104
        pygame.draw.rect(self.screen, (12, 6, 20), (x + 16, info_y, SIDEBAR_W - 32, 82), border_radius=5)
        pygame.draw.rect(self.screen, (120, 45, 175), (x + 16, info_y, SIDEBAR_W - 32, 82), 1, border_radius=5)
        
        selected = self.selected()
        if selected:
            first = selected[0]
            name = STRUCT_DEFS[first.type]["name"] if first.kind == "structure" else UNIT_DEFS[first.type]["name"]
            lines = [f">> COMMAND: {name.upper()}", f">> INTEGRITY: {round(first.hp)} / {round(first.max_hp)} HP", f">> SECTOR CODES: LOCKED ({len(selected)} UNIT)"]
        else:
            lines = [">> COMMUNICATIONS ACTIVE", ">> AWAITING FIELD SELECTION", ">> USSR TACTICAL GRID LINKED"]
        for i, line in enumerate(lines):
            surf = self.small.render(line, True, (245, 160, 40) if selected else (145, 210, 80))
            self.screen.blit(surf, (x + 24, info_y + 10 + i * 22))

    def draw_minimap(self, x, y):
        rect = pygame.Rect(x, y, MINIMAP_W, MINIMAP_H)
        pygame.draw.rect(self.screen, (8, 18, 16), rect)
        pygame.draw.rect(self.screen, (245, 185, 45), rect.inflate(4, 4), 2, border_radius=4)
        pygame.draw.rect(self.screen, (120, 45, 175), rect.inflate(8, 8), 2, border_radius=6)
        if self.map_surface:
            mini = pygame.transform.smoothscale(self.map_surface, (MINIMAP_W, MINIMAP_H))
            mini.set_alpha(125)
            self.screen.blit(mini, rect)
        for ore in self.ore:
            if ore.available:
                px, py = x + ore.x / WORLD_W * MINIMAP_W, y + ore.y / WORLD_H * MINIMAP_H
                pygame.draw.circle(self.screen, (245, 195, 45), (round(px), round(py)), 2)
        for entity in self.entities:
            px, py = x + entity.center()[0] / WORLD_W * MINIMAP_W, y + entity.center()[1] / WORLD_H * MINIMAP_H
            color = (245, 40, 35) if entity.team == TEAM_RED else (50, 130, 245)
            pygame.draw.circle(self.screen, color, (round(px), round(py)), 2 if entity.kind == "unit" else 3)
        half_w, half_h = VIEW_W / 2 / self.camera.zoom / WORLD_W * MINIMAP_W, VIEW_H / 2 / self.camera.zoom / WORLD_H * MINIMAP_H
        cx, cy = x + self.camera.x / WORLD_W * MINIMAP_W, y + self.camera.y / WORLD_H * MINIMAP_H
        pygame.draw.rect(self.screen, (245, 215, 90), (cx - half_w, cy - half_h, half_w * 2, half_h * 2), 1)

    def draw_bottombar(self):
        y = SCREEN_H - BOTTOM_H
        pygame.draw.rect(self.screen, (18, 16, 14), (0, y, SCREEN_W, BOTTOM_H))
        text = "Left drag: select   Right click: move/attack/cancel tool   H: repair   X/Sell: sell building   Delete: sell selected building"
        surf = self.small.render(text, True, (190, 170, 140))
        self.screen.blit(surf, (18, y + 9))
        queue = ", ".join(self.training_queue[:5]) if self.training_queue else "empty"
        qsurf = self.small.render(f"Queue: {queue}", True, (220, 180, 110))
        self.screen.blit(qsurf, (SCREEN_W - 360, y + 9))

    def draw_center_banner(self, title, subtitle):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 115))
        self.screen.blit(overlay, (0, 0))
        rect = pygame.Rect(0, 0, 430, 140)
        rect.center = (SCREEN_W // 2, SCREEN_H // 2)
        pygame.draw.rect(self.screen, (25, 18, 14), rect, border_radius=6)
        pygame.draw.rect(self.screen, (210, 55, 35), rect, 2, border_radius=6)
        title_s = self.big.render(title, True, (250, 70, 45))
        sub_s = self.font.render(subtitle, True, (230, 190, 135))
        self.screen.blit(title_s, title_s.get_rect(center=(rect.centerx, rect.y + 48)))
        self.screen.blit(sub_s, sub_s.get_rect(center=(rect.centerx, rect.y + 96)))

    def draw_difficulty_menu(self):
        self.difficulty_buttons = []
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(0, 0, 520, 250)
        panel.center = (SCREEN_W // 2, SCREEN_H // 2)
        pygame.draw.rect(self.screen, (25, 18, 14), panel, border_radius=8)
        pygame.draw.rect(self.screen, (210, 55, 35), panel, 2, border_radius=8)

        title = self.big.render("RED ALERT MINI", True, (250, 70, 45))
        self.screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 48)))
        subtitle = self.font.render("Select your difficulty", True, (230, 190, 135))
        self.screen.blit(subtitle, subtitle.get_rect(center=(panel.centerx, panel.y + 94)))

        choices = (
            ("easy", "EASY", "1", "90 sec waves"),
            ("medium", "MEDIUM", "2", "60 sec waves"),
            ("hard", "HARD", "3", "40 sec waves"),
        )
        button_width, button_height, gap = 142, 76, 16
        total_width = button_width * len(choices) + gap * (len(choices) - 1)
        start_x = panel.centerx - total_width // 2
        button_y = panel.y + 132

        for index, (difficulty, label, hotkey, detail) in enumerate(choices):
            rect = pygame.Rect(
                start_x + index * (button_width + gap),
                button_y,
                button_width,
                button_height,
            )
            pygame.draw.rect(self.screen, (45, 24, 32), rect, border_radius=5)
            pygame.draw.rect(self.screen, (245, 185, 45), rect, 2, border_radius=5)
            label_surf = self.font.render(f"{label} [{hotkey}]", True, (255, 220, 120))
            detail_surf = self.small.render(detail, True, (220, 195, 165))
            self.screen.blit(label_surf, label_surf.get_rect(center=(rect.centerx, rect.y + 25)))
            self.screen.blit(detail_surf, detail_surf.get_rect(center=(rect.centerx, rect.y + 52)))
            self.difficulty_buttons.append(Button(rect, label, difficulty, "difficulty"))

    def on_view(self, sx, sy, pad=0):
        return -pad <= sx <= VIEW_W + pad and TOP_H - pad <= sy <= TOP_H + VIEW_H + pad


def distance_xy(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def entity_distance(a, b):
    ax, ay = a.center()
    bx, by = b.center()
    return distance_xy(ax, ay, bx, by)


def clamp(value, low, high):
    return max(low, min(high, value))


async def main():
    pygame.init()
    pygame.display.set_caption("Red Alert Mini - Pygame")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 18, bold=True)
    small = pygame.font.SysFont("arial", 14)
    big = pygame.font.SysFont("arial", 42, bold=True)
    game = Game(screen, clock, font, small, big)
    try:
        game.load_assets()
    except Exception:
        import traceback
        traceback.print_exc()
    try:
        game.load_sounds()
    except Exception:
        import traceback
        traceback.print_exc()

    while True:
        try:
            dt = clock.tick(60) / 1000
            for event in pygame.event.get():
                game.event(event)
            game.update(min(dt, 0.05))
            game.draw()
            pygame.display.flip()
            await asyncio.sleep(0)
        except Exception:
            import traceback
            traceback.print_exc()
            pygame.display.flip()
            await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
