#!/usr/bin/env python3
"""
STL to SVG Slicer
=================
Slices a 3D STL mesh into horizontal 2D cross-sections (projections) along the Z-axis
and saves each slice as an SVG file.

Key Features:
- Slice by layer count (-n / --slices) or fixed layer thickness (-s / --step).
- Consistent global bounding box across all SVGs for seamless stacking / laser cutting.
- Displays the outline of the NEXT level in RED on each slice for easy layer alignment.
- Detects and renders WATER bodies (rivers, lakes) on the bottom slice (baseboard).
- Converts Cartesian coordinates to screen/SVG coordinates (positive coords, flip-Y, margin).
- Supports outline strokes, fills (with fill-rule="evenodd" for holes), and precision tuning.
- Optional layer engraving/text labels (--labels).
- Optional combined multi-layer SVG export (--combine).
"""

import os
import sys
import glob
import argparse
import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.ops import unary_union


def parse_args():
    parser = argparse.ArgumentParser(
        description="Slice a 3D STL mesh along the Z-axis into 2D SVG cross-sections."
    )
    parser.add_argument(
        "stl_file",
        nargs="?",
        default=None,
        help="Path to the input STL file. If omitted, uses the first .stl found in current directory.",
    )
    parser.add_argument(
        "-n", "--slices",
        type=int,
        default=10,
        help="Number of slices to generate (default: 10).",
    )
    parser.add_argument(
        "-s", "--step",
        type=float,
        default=None,
        help="Layer thickness / step in Z units (overrides --slices if set).",
    )
    parser.add_argument(
        "-o", "--out-dir",
        type=str,
        default="slices",
        help="Output directory to save SVG files (default: 'slices').",
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Filename prefix for SVG files (default: derived from STL filename).",
    )
    parser.add_argument(
        "--z-min",
        type=float,
        default=None,
        help="Lower Z bound to start slicing (default: mesh minimum Z).",
    )
    parser.add_argument(
        "--z-max",
        type=float,
        default=None,
        help="Upper Z bound to stop slicing (default: mesh maximum Z).",
    )
    parser.add_argument(
        "--spacing",
        choices=["midpoint", "linear"],
        default="midpoint",
        help=(
            "Layer height distribution: 'midpoint' slices through the center of each layer "
            "(best for physical sheet stacking), 'linear' spaces slices evenly across the range."
        ),
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=5.0,
        help="Canvas padding / margin in units around the mesh extents (default: 5.0).",
    )
    parser.add_argument(
        "--stroke",
        type=str,
        default="#000000",
        help="SVG stroke color for the current layer boundary / cut line (default: '#000000').",
    )
    parser.add_argument(
        "--stroke-width",
        type=float,
        default=0.5,
        help="SVG stroke width for current layer (default: 0.5).",
    )
    parser.add_argument(
        "--fill",
        type=str,
        default="none",
        help="SVG fill color for current layer (default: 'none', e.g. '#e0e0e0').",
    )
    parser.add_argument(
        "--next-stroke",
        type=str,
        default="#FF0000",
        help="Stroke color for next level alignment outline (default: '#FF0000' red).",
    )
    parser.add_argument(
        "--next-stroke-width",
        type=float,
        default=0.35,
        help="Stroke width for next level alignment outline (default: 0.35).",
    )
    parser.add_argument(
        "--no-next-outline",
        action="store_true",
        help="Disable drawing the red outline of the next level.",
    )
    parser.add_argument(
        "--water-level",
        type=str,
        default="auto",
        help="Z elevation threshold for water bodies, or 'auto' to detect automatically (default: 'auto').",
    )
    parser.add_argument(
        "--water-stroke",
        type=str,
        default="#0066CC",
        help="Stroke color for water boundaries on bottom slice (default: '#0066CC').",
    )
    parser.add_argument(
        "--water-stroke-width",
        type=float,
        default=0.4,
        help="Stroke width for water boundaries (default: 0.4).",
    )
    parser.add_argument(
        "--water-fill",
        type=str,
        default="none",
        help="Fill color for water bodies (default: 'none', e.g. '#E3F2FD').",
    )
    parser.add_argument(
        "--no-water",
        action="store_true",
        help="Disable showing water on the bottom slice.",
    )
    parser.add_argument(
        "--units",
        type=str,
        default="mm",
        help="Physical unit label for width/height in SVG header (default: 'mm', use '' for none).",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=3,
        help="Coordinate decimal precision in SVG paths (default: 3).",
    )
    parser.add_argument(
        "--labels",
        action="store_true",
        help="Add layer index and Z-height text label in the margin.",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Also export a single combined SVG ('all_slices.svg') containing all stacked layers.",
    )
    parser.add_argument(
        "--no-flip-y",
        action="store_true",
        help="Do not flip the Y-axis (keep raw Cartesian Y instead of SVG top-down).",
    )
    parser.add_argument(
        "--raw-coords",
        action="store_true",
        help="Keep raw 3D mesh X/Y coordinates without shifting to (0, 0) origin.",
    )

    return parser.parse_args()


def compute_slice_heights(z_min, z_max, num_slices=10, step=None, spacing="midpoint"):
    """
    Computes the array of Z heights to slice at.
    """
    total_height = z_max - z_min
    if total_height <= 0:
        raise ValueError(f"Invalid Z range: z_min={z_min}, z_max={z_max}")

    if step is not None and step > 0:
        num_slices = max(1, int(np.floor(total_height / step)))
        if spacing == "midpoint":
            heights = [z_min + (i + 0.5) * step for i in range(num_slices)]
        else:
            heights = [z_min + (i + 1) * step for i in range(num_slices)]
            heights = [h for h in heights if h < z_max]
        return np.array(heights)

    # Count-based slicing
    if spacing == "midpoint":
        layer_thickness = total_height / num_slices
        heights = np.array([z_min + (i + 0.5) * layer_thickness for i in range(num_slices)])
    else:
        eps = total_height * 0.005
        heights = np.linspace(z_min + eps, z_max - eps, num_slices)

    return heights


def extract_path_strings(path_2d, transform_fn, precision=3):
    """
    Converts entities in a trimesh Path2D into SVG path 'd' commands.
    """
    if path_2d is None or len(path_2d.entities) == 0:
        return []

    d_list = []
    fmt = f"{{:.{precision}f}}"

    for entity in path_2d.entities:
        coords = entity.discrete(path_2d.vertices)
        if len(coords) < 2:
            continue

        # Apply 2D coordinate transform
        tx, ty = transform_fn(coords[:, 0], coords[:, 1])

        # Format SVG path
        pts = " ".join(f"{fmt.format(x)},{fmt.format(y)}" for x, y in zip(tx, ty))
        is_closed = getattr(entity, "closed", False) or np.allclose(coords[0], coords[-1])
        d_list.append(f"M {pts}" + (" Z" if is_closed else ""))

    return d_list


def extract_water_paths(mesh, water_level_param, transform_fn, precision=3, min_area=15.0):
    """
    Detects flat/low water surfaces on the terrain and extracts their 2D boundary paths.
    """
    try:
        v = mesh.vertices
        fn = mesh.face_normals
        faces_z = v[mesh.faces, 2].mean(axis=1)

        # Consider top-surface faces (normal pointing roughly upwards, above bottom baseplate)
        top_mask = (fn[:, 2] > 0.05) & (faces_z > 1.0)
        if not np.any(top_mask):
            return [], None

        # Determine water level threshold
        if water_level_param == "auto":
            flat_mask = top_mask & (fn[:, 2] > 0.99) & (faces_z < 10.0)
            if np.any(flat_mask):
                flat_z = faces_z[flat_mask]
                counts, bins = np.histogram(flat_z, bins=np.arange(np.min(flat_z), min(np.max(flat_z) + 0.2, 12.0), 0.1))
                if len(counts) > 0:
                    peak_idx = int(np.argmax(counts))
                    # Pick upper edge of the water peak
                    water_threshold = float(bins[min(peak_idx + 3, len(bins) - 1)])
                else:
                    water_threshold = float(np.min(faces_z[top_mask]) + 0.5)
            else:
                water_threshold = float(np.min(faces_z[top_mask]) + 0.5)
        else:
            water_threshold = float(water_level_param)

        water_face_mask = top_mask & (faces_z <= water_threshold)
        if not np.any(water_face_mask):
            return [], water_threshold

        water_faces = mesh.faces[water_face_mask]
        v2d = v[:, :2]

        # Convert 2D triangle projections to shapely polygons
        polys = [Polygon(v2d[f]) for f in water_faces if Polygon(v2d[f]).is_valid]
        if not polys:
            return [], water_threshold

        # Union and smooth boundaries (buffer + simplify removes interior triangle seams)
        merged = unary_union(polys).buffer(0.2).buffer(-0.2).simplify(0.2)
        geoms = merged.geoms if merged.geom_type == "MultiPolygon" else [merged]
        big_polys = [p for p in geoms if p.area >= min_area]

        fmt = f"{{:.{precision}f}}"
        water_d_list = []

        for p in big_polys:
            # Exterior shoreline
            ext = np.array(p.exterior.coords)
            tx, ty = transform_fn(ext[:, 0], ext[:, 1])
            pts = " ".join(f"{fmt.format(x)},{fmt.format(y)}" for x, y in zip(tx, ty))
            water_d_list.append(f"M {pts} Z")

            # Interior islands
            for interior in p.interiors:
                if Polygon(interior).area >= min_area * 0.3:
                    inte = np.array(interior.coords)
                    itx, ity = transform_fn(inte[:, 0], inte[:, 1])
                    ipts = " ".join(f"{fmt.format(x)},{fmt.format(y)}" for x, y in zip(itx, ity))
                    water_d_list.append(f"M {ipts} Z")

        return water_d_list, water_threshold
    except Exception as e:
        print(f"Warning: Water extraction failed ({e}). Proceeding without water.", file=sys.stderr)
        return [], None


def build_svg(
    current_path_strings,
    next_path_strings,
    water_path_strings,
    view_box,
    width_str,
    height_str,
    layer_id,
    z_height,
    next_z_height=None,
    stroke="#000000",
    stroke_width=0.5,
    fill="none",
    next_stroke="#FF0000",
    next_stroke_width=0.35,
    water_stroke="#0066CC",
    water_stroke_width=0.4,
    water_fill="none",
    label=None,
    label_pos=(10, 15),
):
    """
    Builds a standalone SVG XML string for a single slice, including:
    - Optional water bodies (for bottom slice)
    - Next level alignment outline in red
    - Current level cut-line in black
    """
    vb_x, vb_y, vb_w, vb_h = view_box
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg"',
        f'     viewBox="{vb_x:.3f} {vb_y:.3f} {vb_w:.3f} {vb_h:.3f}"',
        f'     width="{width_str}"',
        f'     height="{height_str}">',
        f'  <desc>Layer {layer_id} at z = {z_height:.3f}</desc>',
    ]

    if label:
        lx, ly = label_pos
        svg_lines.append(
            f'  <text x="{lx:.2f}" y="{ly:.2f}" font-family="sans-serif" font-size="6" '
            f'fill="#555555">{label}</text>'
        )

    # 1. Water bodies (shown on bottom slice)
    if water_path_strings:
        water_d = " ".join(water_path_strings)
        svg_lines.extend([
            '  <!-- Water bodies (rivers, lakes) -->',
            '  <g id="water_bodies" class="water-body">',
            f'    <path d="{water_d}"',
            f'          fill="{water_fill}"',
            f'          stroke="{water_stroke}"',
            f'          stroke-width="{water_stroke_width}"',
            '          stroke-linecap="round"',
            '          stroke-linejoin="round"',
            '          fill-rule="evenodd" />',
            '  </g>',
        ])

    # 2. Next level alignment outline (in red for stacking guide)
    if next_path_strings:
        next_d = " ".join(next_path_strings)
        next_desc = f"Next layer guide at z = {next_z_height:.3f}" if next_z_height is not None else "Next layer guide"
        svg_lines.extend([
            f'  <!-- Alignment guide: outline of the NEXT level above ({next_desc}) -->',
            '  <g id="next_layer_guide" class="alignment-guide">',
            f'    <path d="{next_d}"',
            '          fill="none"',
            f'          stroke="{next_stroke}"',
            f'          stroke-width="{next_stroke_width}"',
            '          stroke-linecap="round"',
            '          stroke-linejoin="round"',
            '          fill-rule="evenodd" />',
            '  </g>',
        ])

    # 3. Current level boundary (cut line)
    if current_path_strings:
        current_d = " ".join(current_path_strings)
        svg_lines.extend([
            f'  <!-- Current level outline (cut line) -->',
            f'  <g id="{layer_id}" data-z="{z_height:.3f}" class="cut-line">',
            f'    <path d="{current_d}"',
            f'          fill="{fill}"',
            f'          stroke="{stroke}"',
            f'          stroke-width="{stroke_width}"',
            '          stroke-linecap="round"',
            '          stroke-linejoin="round"',
            '          fill-rule="evenodd" />',
            '  </g>',
        ])
    else:
        svg_lines.append('  <!-- Empty slice: no intersections found at this height -->')

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def build_combined_svg(
    all_layers_data,
    water_path_strings,
    view_box,
    width_str,
    height_str,
    stroke_width=0.5,
    water_stroke="#0066CC",
    water_fill="none",
):
    """
    Builds a single combined SVG containing all slices as layered groups,
    with water at the bottom and layers colored by elevation.
    """
    vb_x, vb_y, vb_w, vb_h = view_box
    svg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg"',
        f'     viewBox="{vb_x:.3f} {vb_y:.3f} {vb_w:.3f} {vb_h:.3f}"',
        f'     width="{width_str}"',
        f'     height="{height_str}">',
        '  <desc>Combined Z-axis slices</desc>',
        '  <style>',
        '    .layer-path { stroke-linecap: round; stroke-linejoin: round; fill-rule: evenodd; }',
        '    .water-path { stroke-linecap: round; stroke-linejoin: round; fill-rule: evenodd; }',
        '  </style>',
    ]

    # Water layer
    if water_path_strings:
        water_d = " ".join(water_path_strings)
        svg_lines.extend([
            '  <g id="combined_water" class="water-body">',
            '    <title>Water Bodies</title>',
            f'    <path class="water-path" d="{water_d}" fill="{water_fill}" stroke="{water_stroke}" stroke-width="{stroke_width}" />',
            '  </g>',
        ])

    n_layers = len(all_layers_data)
    for i, (layer_id, z_h, path_strings) in enumerate(all_layers_data):
        if not path_strings:
            continue
        # Elevation color ramp (dark blue -> cyan -> green -> yellow -> red)
        t = i / max(1, n_layers - 1)
        r = int(255 * min(1.0, max(0.0, 1.5 - abs(t * 4 - 3))))
        g = int(255 * min(1.0, max(0.0, 2.0 - abs(t * 4 - 2))))
        b = int(255 * min(1.0, max(0.0, 2.0 - abs(t * 4 - 1))))
        color = f"#{r:02x}{g:02x}{b:02x}"

        combined_d = " ".join(path_strings)
        svg_lines.extend([
            f'  <g id="{layer_id}" data-z="{z_h:.3f}">',
            f'    <title>{layer_id} (z={z_h:.2f})</title>',
            f'    <path class="layer-path" d="{combined_d}" fill="none" stroke="{color}" stroke-width="{stroke_width}" />',
            '  </g>',
        ])

    svg_lines.append('</svg>')
    return "\n".join(svg_lines)


def slice_stl(
    stl_path,
    num_slices=10,
    step=None,
    out_dir="slices",
    prefix=None,
    z_min=None,
    z_max=None,
    spacing="midpoint",
    margin=5.0,
    stroke="#000000",
    stroke_width=0.5,
    fill="none",
    next_stroke="#FF0000",
    next_stroke_width=0.35,
    no_next_outline=False,
    water_level="auto",
    water_stroke="#0066CC",
    water_stroke_width=0.4,
    water_fill="none",
    no_water=False,
    units="mm",
    precision=3,
    labels=False,
    combine=False,
    no_flip_y=False,
    raw_coords=False,
):
    """
    Main function to slice an STL mesh and write SVG files.
    """
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"STL file not found: {stl_path}")

    print(f"Loading mesh: {stl_path}")
    mesh = trimesh.load(stl_path)

    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"Loaded geometry is not a Trimesh object (got {type(mesh)}).")

    bounds = mesh.bounds
    extents = mesh.extents
    x_min, y_min, mesh_z_min = bounds[0]
    x_max, y_max, mesh_z_max = bounds[1]

    print(f"Mesh Bounding Box:")
    print(f"  X: [{x_min:.2f}, {x_max:.2f}] (width:  {extents[0]:.2f})")
    print(f"  Y: [{y_min:.2f}, {y_max:.2f}] (height: {extents[1]:.2f})")
    print(f"  Z: [{mesh_z_min:.2f}, {mesh_z_max:.2f}] (depth:  {extents[2]:.2f})")

    # Determine Z range
    eff_z_min = mesh_z_min if z_min is None else z_min
    eff_z_max = mesh_z_max if z_max is None else z_max

    heights = compute_slice_heights(
        eff_z_min, eff_z_max, num_slices=num_slices, step=step, spacing=spacing
    )
    num_actual_slices = len(heights)
    print(f"Generating {num_actual_slices} slices (Z from {heights[0]:.2f} to {heights[-1]:.2f})...")

    # Determine canvas coordinate transformation
    if raw_coords:
        transform_fn = lambda x, y: (x, y)
        vb_x = x_min - margin
        vb_y = y_min - margin
        vb_w = extents[0] + 2 * margin
        vb_h = extents[1] + 2 * margin
    else:
        # Normalized coordinates: (0, 0) is top-left
        if no_flip_y:
            transform_fn = lambda x, y: (x - x_min + margin, y - y_min + margin)
        else:
            transform_fn = lambda x, y: (x - x_min + margin, (y_max - y) + margin)

        vb_x = 0.0
        vb_y = 0.0
        vb_w = extents[0] + 2 * margin
        vb_h = extents[1] + 2 * margin

    view_box = (vb_x, vb_y, vb_w, vb_h)
    u_suffix = units if units else ""
    width_str = f"{vb_w:.2f}{u_suffix}"
    height_str = f"{vb_h:.2f}{u_suffix}"

    os.makedirs(out_dir, exist_ok=True)
    base_prefix = prefix or os.path.splitext(os.path.basename(stl_path))[0]

    # Extract water geometry for bottom slice
    water_path_strings = []
    if not no_water:
        print("Analyzing terrain water bodies...")
        water_path_strings, detected_threshold = extract_water_paths(
            mesh, water_level, transform_fn, precision=precision
        )
        if water_path_strings:
            thresh_info = f"at z <= {detected_threshold:.2f}{u_suffix}" if detected_threshold else ""
            print(f"  Detected water surface {thresh_info} ({len(water_path_strings)} shoreline/island paths).")
        else:
            print("  No water surface detected.")

    # Slice the mesh along the Z axis (normal [0, 0, 1])
    sections = mesh.section_multiplane(
        plane_origin=[0, 0, 0],
        plane_normal=[0, 0, 1],
        heights=heights,
    )

    pad_width = max(2, len(str(num_actual_slices)))
    all_path_strings = [
        extract_path_strings(sec, transform_fn, precision=precision)
        for sec in sections
    ]

    saved_files = []
    all_layers_data = []

    print("-" * 75)
    print(f"{'Layer':<8} {'Z (' + units + ')':<10} {'Features':<22} {'Filename'}")
    print("-" * 75)

    for idx, (z_h, path_strings) in enumerate(zip(heights, all_path_strings), start=1):
        layer_id = f"layer_{idx:0{pad_width}d}"
        is_bottom = (idx == 1)
        has_next = (idx < num_actual_slices) and not no_next_outline

        # Next layer outline in red
        next_paths = all_path_strings[idx] if has_next else []
        next_z = heights[idx] if has_next else None

        # Water on bottom slice
        layer_water = water_path_strings if is_bottom else []

        label_text = f"Layer {idx}/{num_actual_slices} | Z={z_h:.2f}{u_suffix}" if labels else None
        svg_content = build_svg(
            current_path_strings=path_strings,
            next_path_strings=next_paths,
            water_path_strings=layer_water,
            view_box=view_box,
            width_str=width_str,
            height_str=height_str,
            layer_id=layer_id,
            z_height=z_h,
            next_z_height=next_z,
            stroke=stroke,
            stroke_width=stroke_width,
            fill=fill,
            next_stroke=next_stroke,
            next_stroke_width=next_stroke_width,
            water_stroke=water_stroke,
            water_stroke_width=water_stroke_width,
            water_fill=water_fill,
            label=label_text,
            label_pos=(margin, margin + 4 if margin >= 4 else 5),
        )

        filename = f"{base_prefix}_slice_{idx:0{pad_width}d}_z{z_h:.2f}.svg"
        out_path = os.path.join(out_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        saved_files.append(out_path)
        all_layers_data.append((layer_id, z_h, path_strings))

        feat_desc = []
        if is_bottom and layer_water:
            feat_desc.append("Water")
        if next_paths:
            feat_desc.append("Red Next Outline")
        feat_str = " + ".join(feat_desc) if feat_desc else "Top Layer"

        print(f"{idx:<8} {z_h:<10.2f} {feat_str:<22} {filename}")

    print("-" * 75)
    print(f"Successfully exported {len(saved_files)} SVG slice files to '{out_dir}/'.")

    # Export combined SVG if requested
    if combine:
        comb_svg = build_combined_svg(
            all_layers_data=all_layers_data,
            water_path_strings=water_path_strings,
            view_box=view_box,
            width_str=width_str,
            height_str=height_str,
            stroke_width=stroke_width,
            water_stroke=water_stroke,
            water_fill=water_fill,
        )
        comb_path = os.path.join(out_dir, f"{base_prefix}_all_slices.svg")
        with open(comb_path, "w", encoding="utf-8") as f:
            f.write(comb_svg)
        print(f"Exported combined visualization to '{comb_path}'.")

    return saved_files


def main():
    args = parse_args()

    # Find STL file if not explicitly provided
    stl_path = args.stl_file
    if stl_path is None:
        stl_candidates = glob.glob("*.stl") + glob.glob("*.STL")
        if not stl_candidates:
            print("Error: No STL file specified and none found in the current directory.", file=sys.stderr)
            sys.exit(1)
        stl_path = stl_candidates[0]
        print(f"No file specified. Using found STL file: '{stl_path}'")

    try:
        slice_stl(
            stl_path=stl_path,
            num_slices=args.slices,
            step=args.step,
            out_dir=args.out_dir,
            prefix=args.prefix,
            z_min=args.z_min,
            z_max=args.z_max,
            spacing=args.spacing,
            margin=args.margin,
            stroke=args.stroke,
            stroke_width=args.stroke_width,
            fill=args.fill,
            next_stroke=args.next_stroke,
            next_stroke_width=args.next_stroke_width,
            no_next_outline=args.no_next_outline,
            water_level=args.water_level,
            water_stroke=args.water_stroke,
            water_stroke_width=args.water_stroke_width,
            water_fill=args.water_fill,
            no_water=args.no_water,
            units=args.units,
            precision=args.precision,
            labels=args.labels,
            combine=args.combine,
            no_flip_y=args.no_flip_y,
            raw_coords=args.raw_coords,
        )
    except Exception as e:
        print(f"Error during slicing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
