# STL to SVG Terrain Slicer — User Guide

A high-performance Python tool for slicing 3D STL models (such as digital elevation models, mountain terrains, and architectural models) into 2D horizontal cross-sections exported as layered SVG vector files.

Designed especially for **laser cutting**, **CNC routing**, **stacked topographic models** (plywood, cardboard, acrylic), and **cartographic vector design**.

---

## Table of Contents

1. [Key Features](#key-features)
2. [Installation & Requirements](#installation--requirements)
3. [Quick Start](#quick-start)
4. [How Layer Stacking Works](#how-layer-stacking-works)
   - [Next-Level Alignment Guides (Red)](#1-next-level-alignment-guides-red)
   - [Water Surface Detection (Blue)](#2-water-surface-detection-blue)
   - [Cut Lines (Black)](#3-cut-lines-black)
5. [CLI Options Reference](#cli-options-reference)
6. [Practical Usage Examples](#practical-usage-examples)
   - [Example 1: Fixed Sheet Thickness (Laser Cutting)](#example-1-fixed-sheet-thickness-laser-cutting)
   - [Example 2: Fixed Layer Count with Labels & Combined Preview](#example-2-fixed-layer-count-with-labels--combined-preview)
   - [Example 3: Custom Water Level & Styling](#example-3-custom-water-level--styling)
   - [Example 4: Preparing for Laser Cutter CAM (LightBurn, Glowforge, etc.)](#example-4-preparing-for-laser-cutter-cam-lightburn-glowforge-etc)
7. [Using as a Python Module](#using-as-a-python-module)
8. [Tips & Troubleshooting](#tips--troubleshooting)

---

## Key Features

- **Unified Global Coordinate System**: All generated SVG files share the identical `viewBox` and dimensions. Stacked sheets line up with 100% precision without manual repositioning.
- **Red Alignment Guides on Every Slice**: Every layer automatically has the outline of the layer *above* it rendered in red (`#FF0000`), allowing you to score or engrave the exact placement marks on the physical sheet before assembly.
- **Water Body Extraction**: Automatically detects flat water surfaces (rivers, lakes, sea) and draws their outlines/islands on the bottom baseboard slice in blue (`#0066CC`).
- **Laser-Cutter Ready Color Mapping**:
  - **Black (`#000000`)**: Current layer cut line.
  - **Red (`#FF0000`)**: Alignment score line for the next layer.
  - **Blue (`#0066CC`)**: Waterline engrave/score line.
- **Flexible Slicing Modes**: Slice by count (`-n 10`) or by physical material thickness (`-s 3.0` for 3 mm sheets).
- **Even-Odd Fill Handling**: Proper handling of hollow terrain, valleys, multi-peak islands, and lake boundaries.
- **Combined Visualization**: Option to export an `all_slices.svg` file with all layers stacked and colored along an elevation gradient.

---

## Installation & Requirements

The slicer runs on **Python 3.10+** and relies on three standard libraries:

```powershell
pip install trimesh shapely numpy
```

---

## Quick Start

Navigate to the directory containing `stl_slicer.py` and your STL file:

```powershell
# Basic 10-layer slice (automatically finds any STL in current folder)
python stl_slicer.py -n 10

# Generate 15 layers with labels and a combined all_slices.svg preview
python stl_slicer.py -n 15 --labels --combine
```

Output files will be saved in the `./slices/` folder.

---

## How Layer Stacking Works

When fabricating stacked 3D topography models, each SVG slice is structured into semantic SVG groups with distinct colors:

```
┌────────────────────────────────────────────────────────┐
│ SVG Canvas (viewBox matches entire model bounding box) │
│                                                        │
│   [Blue #0066CC]  Water / Shoreline (Layer 1 only)     │
│   [Red  #FF0000]  Next Layer Guide (Where L+1 sits)    │
│   [Black #000000] Cut Line (Perimeter of current layer)│
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 1. Next-Level Alignment Guides (Red)
- On Slice 1, a red outline shows exactly where Slice 2 should be glued.
- On Slice 2, a red outline shows where Slice 3 should be glued, and so on.
- The top layer automatically omits the guide since nothing goes above it.
- **Laser workflow**: Set the red stroke to low-power **Vector Engrave / Score**.

### 2. Water Surface Detection (Blue)
- Digital elevation models (DEMs) typically flatten water bodies (e.g. the Danube river in `terrain-184734.stl`) to a uniform plateau at the lowest elevations.
- The script analyzes the surface face normals and elevation histogram to detect water bodies.
- On the **bottom slice (baseboard)**, shorelines and internal islands (e.g. Szentendre Island) are rendered in blue.
- **Laser workflow**: Set the blue stroke to **Engrave** or light **Score**.

### 3. Cut Lines (Black)
- The actual outer boundary of the current slice.
- **Laser workflow**: Set the black stroke to full-power **Cut**.

---

## CLI Options Reference

```powershell
python stl_slicer.py [stl_file] [options]
```

### General & Input/Output

| Argument | Default | Description |
| :--- | :--- | :--- |
| `stl_file` | First `.stl` in dir | Path to input STL file. If omitted, uses first `.stl` found. |
| `-o`, `--out-dir` | `slices` | Output folder to store generated SVG files. |
| `--prefix` | STL filename | Custom prefix for exported files. |
| `--combine` | `False` | Also export `*_all_slices.svg` containing all layers stacked. |
| `--labels` | `False` | Print layer index & Z height text in the top-left margin. |
| `--precision` | `3` | Coordinate decimal places in SVG `d="..."` paths (keeps files compact). |
| `--units` | `mm` | Unit suffix in SVG header (`width="...mm" height="...mm"`). |

### Slicing Parameters

| Option | Default | Description |
| :--- | :--- | :--- |
| `-n`, `--slices` | `10` | Total number of slices to generate. |
| `-s`, `--step` | `None` | Fixed layer thickness in Z units (e.g., `3.0` mm). Overrides `-n`. |
| `--z-min` | Mesh min Z | Lowest Z coordinate to start slicing. |
| `--z-max` | Mesh max Z | Highest Z coordinate to stop slicing. |
| `--spacing` | `midpoint` | `midpoint`: Slices through layer centers (best for physical stacking).<br>`linear`: Evenly spaced samples across the range. |
| `--margin` | `5.0` | Outer padding in mm added around the mesh bounding box. |

### Alignment Guide (Next Level) Styling

| Option | Default | Description |
| :--- | :--- | :--- |
| `--next-stroke` | `#FF0000` | Stroke color for next level alignment outline (hex or name). |
| `--next-stroke-width` | `0.35` | Stroke width for next level alignment outline. |
| `--no-next-outline` | `False` | Disable the red next-level outline entirely. |

### Water Body Styling

| Option | Default | Description |
| :--- | :--- | :--- |
| `--water-level` | `auto` | Height threshold for water. Can be `'auto'` or float (e.g. `5.5`). |
| `--water-stroke` | `#0066CC` | Outline stroke color for water bodies. |
| `--water-stroke-width` | `0.4` | Stroke width for water outlines. |
| `--water-fill` | `none` | Fill color for water bodies (e.g. `"#E3F2FD"` for subtle blue). |
| `--no-water` | `False` | Disable water detection and rendering on the bottom slice. |

### Cut Line & Canvas Styling

| Option | Default | Description |
| :--- | :--- | :--- |
| `--stroke` | `#000000` | Stroke color for the current layer boundary (cut line). |
| `--stroke-width` | `0.5` | Stroke width for the current layer boundary. |
| `--fill` | `none` | Fill color for the current layer. |
| `--no-flip-y` | `False` | Do not invert Y-axis (preserves raw 3D Cartesian coordinates). |
| `--raw-coords` | `False` | Do not shift origin to `(0, 0)`; keeps original STL coordinates. |

---

## Practical Usage Examples

### Example 1: Fixed Sheet Thickness (Laser Cutting)
If you are using **3.0 mm plywood or MDF sheets**, slice by exact thickness:

```powershell
python stl_slicer.py terrain-184734.stl -s 3.0 --labels -o slices_3mm
```

### Example 2: Fixed Layer Count with Labels & Combined Preview
Create 12 evenly distributed layers with embedded layer text and an `all_slices.svg` preview:

```powershell
python stl_slicer.py -n 12 --labels --combine -o output_12layers
```

### Example 3: Custom Water Level & Styling
Fill the water on the bottom slice with a light blue shade and make the river outline cyan:

```powershell
python stl_slicer.py -n 10 --water-fill "#D0E8FF" --water-stroke "#0088DD" --combine
```

### Example 4: Preparing for Laser Cutter CAM (LightBurn, Glowforge, etc.)
Laser software assigns cut settings by stroke color:
- **Black `#000000`** $\rightarrow$ Layer Cut (High power, slow speed)
- **Red `#FF0000`** $\rightarrow$ Alignment Score (Low power, high speed)
- **Blue `#0066CC`** $\rightarrow$ Water Engrave / Score (Medium power)

Use fine hairline strokes for laser cutting:

```powershell
python stl_slicer.py -n 15 --stroke-width 0.1 --next-stroke-width 0.1 --water-stroke-width 0.1
```

---

## Using as a Python Module

You can also import `slice_stl` directly into your own Python scripts or automated workflows:

```python
from stl_slicer import slice_stl

saved_files = slice_stl(
    stl_path="terrain-184734.stl",
    num_slices=10,
    out_dir="my_slices",
    labels=True,
    combine=True,
    stroke="#000000",
    next_stroke="#FF0000",
    water_stroke="#0066CC",
    water_fill="#E3F2FD"
)

print(f"Generated {len(saved_files)} slice files.")
```

---

## Tips & Troubleshooting

1. **Why does the bottom slice (Layer 1) look rectangular?**
   - In 3D terrain STL files, there is a flat solid pedestal / base plate underneath the terrain. Layer 1 cuts through this solid baseplate, giving you the solid baseboard for your stacked model. On this baseboard, the Danube water body and the red outline for Layer 2 are drawn.
2. **How to slice only the mountain relief (skipping the pedestal)?**
   - Check the mesh info printed by the script. For `terrain-184734.stl`, terrain begins at $Z \approx 5.1\,\text{mm}$.
   - To slice only above the baseplate:
     ```powershell
     python stl_slicer.py --z-min 5.2 -n 10
     ```
3. **Opening SVGs in Vector Software (Inkscape / Illustrator)**:
   - Each SVG contains grouped elements with `id="layer_XX"`, `id="next_layer_guide"`, and `id="water_bodies"`.
   - In the **Layers & Objects panel**, you can toggle or lock the alignment guide or water layer with a single click.
4. **File Sizes**:
   - The `--precision 3` default formats coordinates to 3 decimal places (1 micron precision in mm), reducing SVG file sizes by up to 70% compared to raw float exports while preserving full detail.
