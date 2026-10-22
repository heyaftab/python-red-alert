<!-- markdownlint-disable MD041 -->
![Navigation mask and pathfinding banner](assets/nav-banner.svg)

**Automatic collision detection and A* pathfinding for your game.** This system analyzes the map image, detects orange and brown cliffs, and generates a binary collision map for fast pathfinding.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) ![A star algorithm](https://img.shields.io/badge/Algorithm-A*-dc2626?style=for-the-badge) ![85 by 47 grid](https://img.shields.io/badge/Grid-85%C3%9747-f59e0b?style=for-the-badge) ![20 pixel tiles](https://img.shields.io/badge/Tile-20px-0ea5e9?style=for-the-badge) ![Approximately 4 KB mask](https://img.shields.io/badge/Mask-~4KB-22c55e?style=for-the-badge)

[How it works](#how-it-works) · [Integration](#integration) · [API reference](#api-reference) · [Thresholds](#thresholds) · [Performance](#performance) · [Troubleshooting](#troubleshooting)

![Section divider](assets/nav-divider.svg)

## Overview

The navigation pipeline reads `assets/Map.png`, classifies terrain pixels, reduces the map to a tile grid, then uses A* to find paths around obstacles.

### Project files

| File | Role |
| :--- | :--- |
| `nav_mask.py` | Analyzes the map image and generates the navigation mask |
| `pathfinding.py` | A* pathfinding algorithm with collision detection |
| `pathfinding_example.py` | Usage examples and integration guide |
| `nav_mask.pkl` | Generated, pickled binary collision map |
| `nav_mask_vis.png` | Visual representation of the collision map |

![Section divider](assets/nav-divider.svg)

## How It Works

```text
  Map.png           Color classification       20×20 tiles            A* search
 ┌───────────┐      ┌────────────────┐      ┌──────────────┐      ┌────────────┐
 │ 1688×932  │ ───► │ blocked / open │ ───► │ 85×47 grid   │ ───► │ unit path  │
 │  pixels   │      │ / unknown      │      │ 0=open 1=blocked │   │ (x, y) ... │
 └───────────┘      └────────────────┘      └──────────────┘      └────────────┘
```

### 1. Map analysis

`nav_mask.py` analyzes `assets/Map.png` and assigns each pixel a terrain category:

| Pixel color | Meaning | Result |
| :--- | :--- | :--- |
| Orange or brown | Cliffs and walls | Blocked |
| Green | Open ground | Walkable |
| Sandy or tan | Open ground | Walkable |
| Other colors | Unclassified | Treated as walkable |

### 2. Collision map generation

The map is divided into **20×20 pixel tiles**. Each tile is marked as follows:

| Value | State | Rule |
| :---: | :--- | :--- |
| `1` | Blocked | More than 50% of sampled opaque pixels match obstacle colors |
| `0` | Walkable | At most 50% of sampled opaque pixels match obstacle colors |

| Map size | Tile grid | Blocked tiles | Walkable tiles |
| :---: | :---: | :---: | :---: |
| 1688×932 px | 85×47 (20 px per tile) | 83 | 3912 |

### 3. Pathfinding algorithm

The `Pathfinder` class implements A* pathfinding. It finds routes around obstacles, supports validated diagonal movement, caches recently computed paths, and handles unreachable destinations gracefully.

Example search (diagonal movement is allowed):

```text
  S ● ● ● ● · · · ·        S = start      G = goal
  · █ █ █ ● · · · ·        █ = blocked    · = walkable
  · █ █ █ · ● · · ·        ● = path
  · · · · · · ● ● G
```

![Section divider](assets/nav-divider.svg)

## Integration

Add pathfinding to `main.py` in three steps.

### 1. Basic setup

```python
from pathfinding import initialize_pathfinder, find_path
from nav_mask import is_walkable

# In game initialization:
pathfinder = initialize_pathfinder()
```

### 2. Find paths for units

```python
# When a unit needs to move:
path = find_path(unit.x, unit.y, target_x, target_y)

if path:
    unit.set_path(path)  # Path is a list of (x, y) tuples
    unit.path_index = 0
else:
    print("No path available!")
```

### 3. Move units along a path

```python
def update_unit(unit, dt):
    if unit.path and unit.path_index < len(unit.path):
        waypoint = unit.path[unit.path_index]
        dx = waypoint[0] - unit.x
        dy = waypoint[1] - unit.y
        dist = (dx**2 + dy**2) ** 0.5

        if dist < unit.speed * dt:
            unit.path_index += 1
        else:
            unit.x += (dx / dist) * unit.speed * dt
            unit.y += (dy / dist) * unit.speed * dt
```

### Collision checks

```python
from pathfinding import get_pathfinder

pathfinder = get_pathfinder()

if pathfinder.is_tile_blocked(tile_x, tile_y):
    print("Can't build here!")

valid_pos = pathfinder.get_nearest_walkable_point(x, y)
if valid_pos:
    print(f"Move to: {valid_pos}")
```

![Section divider](assets/nav-divider.svg)

## API Reference

### Pathfinder class

```python
pathfinder = Pathfinder(nav_mask_path="nav_mask.pkl", tile_size=20)

# Find a path
path = pathfinder.find_path(start_x, start_y, goal_x, goal_y, allow_diagonals=True)

# Convert between pixel and tile coordinates
tile_x, tile_y = pathfinder.pixel_to_tile(pixel_x, pixel_y)
pixel_x, pixel_y = pathfinder.tile_to_pixel_center(tile_x, tile_y)

# Check walkability
if not pathfinder.is_tile_blocked(tile_x, tile_y):
    print("Walkable!")

# Find a nearby walkable point
valid_pos = pathfinder.get_nearest_walkable_point(x, y, search_radius=5)

# Clear cached paths
pathfinder.clear_cache()
```

### Convenience functions

```python
from pathfinding import initialize_pathfinder, find_path, get_pathfinder

pathfinder = initialize_pathfinder()
path = find_path(start_x, start_y, goal_x, goal_y)
pf = get_pathfinder()
```

### Navigation mask functions

```python
from nav_mask import load_nav_mask, is_walkable, get_walkable_neighbors, save_nav_mask

nav_mask = load_nav_mask("nav_mask.pkl")

if is_walkable(nav_mask, tile_x, tile_y):
    print("Can walk here")

neighbors = get_walkable_neighbors(
    nav_mask, tile_x, tile_y, include_diagonals=True
)
```

![Section divider](assets/nav-divider.svg)

## Thresholds

Terrain is detected with RGB color thresholds:

| Terrain | Rules | Result |
| :--- | :--- | :---: |
| Orange or brown | `R > 150`, `G < 150`, `B < 100`; `R > G` and `R > B` | Blocked |
| Green | `G > 100`, `R < 150`, `B < 120`; `G > R` and `G > B` | Walkable |
| Sandy or tan | `R > 150`, `G > 120`, `B < 100`; adjusted R-G difference and `G > B` | Walkable |

To tune detection, edit `get_color_category()` in `nav_mask.py`, then regenerate the mask.

![Section divider](assets/nav-divider.svg)

## Performance

| Feature | Details |
| :--- | :--- |
| Path caching | Reuses recently computed paths instead of recomputing them |
| Tile size | Larger tiles improve speed but reduce precision; the current size is 20 px |
| Grid size | The 85×47 tile grid is suitable for typical queries |
| Memory | The mask uses about 4 KB (47×85 bytes) |

![Section divider](assets/nav-divider.svg)

## Troubleshooting

### No path found

- Verify that the destination is walkable: `is_walkable(nav_mask, goal_tx, goal_ty)`.
- Try `get_nearest_walkable_point()` to find a valid destination.
- Check whether the start and goal are in different isolated regions.

### Units get stuck in obstacles

- Make sure buildings are added to the collision map or handled separately.
- Verify pathfinding initialization: `pathfinder = initialize_pathfinder()`.
- Check that tile coordinates are within bounds: `0 ≤ tx < 85`, `0 ≤ ty < 47`.

### Performance issues

- Clear the cache periodically: `pathfinder.clear_cache()`.
- Consider precomputing paths during idle time.
- Use shorter search paths or waypoint networks for large distances.

![Section divider](assets/nav-divider.svg)

## Regenerating the Navigation Mask

If you change the map image, rebuild the collision map:

```bash
python3 nav_mask.py
```

This creates:

| Output | Description |
| :--- | :--- |
| `nav_mask.pkl` | Updated collision map |
| `nav_mask_vis.png` | Updated visualization |

## Visualization

`nav_mask_vis.png` shows the result at a glance. Use it to verify that collision detection is working correctly.

| Color | Meaning |
| :---: | :--- |
| Green | Walkable terrain (open ground) |
| Red | Blocked terrain (cliffs and obstacles) |

![Navigation system footer](assets/nav-divider.svg)
