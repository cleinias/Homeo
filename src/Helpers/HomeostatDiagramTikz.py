"""
Generate a TikZ/LaTeX topology diagram for a Homeostat.

Supports two modes:
  1. From a live Homeostat instance: generate_tikz_diagram(homeostat, ...)
  2. From a log file: generate_tikz_from_log(log_path, ...)

Usage as CLI:
  python -m Helpers.HomeostatDiagramTikz path/to/file.log --section INITIAL --output topology.tex
"""

import math
import re
import argparse


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_tikz_diagram(homeostat, output_path=None,
                          title=None, show_inactive=False,
                          radius=3.5, node_radius=1.2):
    """
    Generate a TikZ/LaTeX diagram of a Homeostat's topology.

    Args:
        homeostat: a Homeostat instance (or any object with .homeoUnits list)
        output_path: path to write .tex file (if None, returns string only)
        title: optional title string above the diagram
        show_inactive: if True, draw inactive connections as dashed lines
        radius: radius of the circular layout (cm)
        node_radius: radius of each unit circle (cm)

    Returns:
        The LaTeX source as a string.
    """
    units_data = []
    for unit in homeostat.homeoUnits:
        crit_thresh = unit.critThreshold if hasattr(unit, 'critThreshold') else 0.9
        max_dev = unit.maxDeviation
        crit_dev = unit.criticalDeviation
        status = unit.status

        if status != 'Active':
            colour = 'inactive'
        elif abs(crit_dev) >= crit_thresh * max_dev:
            colour = 'saturated'
        else:
            colour = 'active'

        units_data.append({
            'name': unit.name,
            'critDev': crit_dev,
            'output': unit.currentOutput,
            'colour': colour,
        })

    conns_data = []
    for unit in homeostat.homeoUnits:
        for conn in unit.inputConnections:
            active = conn.isActive() if callable(getattr(conn, 'isActive', None)) else conn.status
            if not active and not show_inactive:
                continue
            incoming_name = conn.incomingUnit.name
            is_self = (incoming_name == unit.name)
            eff_weight = conn.switch * conn.weight
            conns_data.append({
                'to': unit.name,
                'from': incoming_name,
                'eff_weight': eff_weight,
                'state': conn.state,
                'active': active,
                'is_self': is_self,
            })

    return _build_tikz(units_data, conns_data, title, show_inactive,
                       radius, node_radius, output_path)


def generate_tikz_from_log(log_path, output_path=None, section='INITIAL',
                           title=None, show_inactive=False,
                           radius=3.5, node_radius=1.2):
    """
    Generate a TikZ/LaTeX diagram by parsing a Homeostat .log file.

    Args:
        log_path: path to the .log file
        output_path: path to write .tex file (if None, returns string only)
        section: 'INITIAL' or 'FINAL' to select which snapshot
        title: optional title (defaults to section name)
        show_inactive: if True, draw inactive connections as dashed lines
        radius: radius of the circular layout (cm)
        node_radius: radius of each unit circle (cm)

    Returns:
        The LaTeX source as a string.
    """
    with open(log_path, 'r') as f:
        text = f.read()

    units_data, conns_data = _parse_log_section(text, section, show_inactive)

    if title is None:
        # Derive title from log header + section
        first_line = text.split('\n')[0].strip()
        title = f"{first_line} --- {section} conditions"

    return _build_tikz(units_data, conns_data, title, show_inactive,
                       radius, node_radius, output_path)


# ---------------------------------------------------------------------------
# Log parser
# ---------------------------------------------------------------------------

def _parse_log_section(text, section, show_inactive):
    """Parse a section (INITIAL or FINAL) from a log file."""
    # Find section boundaries
    if section.upper() == 'INITIAL':
        marker = 'INITIAL CONDITIONS'
    elif section.upper() == 'FINAL':
        marker = 'FINAL CONDITIONS'
    else:
        raise ValueError(f"Unknown section: {section!r}. Use 'INITIAL' or 'FINAL'.")

    # Split on the section header
    parts = text.split(marker)
    if len(parts) < 2:
        raise ValueError(f"Section {marker!r} not found in log file.")
    section_text = parts[1]

    # If there's another section after this one, truncate
    for next_marker in ['INITIAL CONDITIONS', 'FINAL CONDITIONS']:
        if next_marker != marker and next_marker in section_text:
            section_text = section_text[:section_text.index(next_marker)]

    # Parse units table
    units_data = _parse_units_table(section_text)

    # Parse connections table
    conns_data = _parse_connections_table(section_text, show_inactive)

    return units_data, conns_data


def _parse_tabulate_table(text, table_header_keyword):
    """Parse a tabulate grid-format table. Returns list of dicts."""
    lines = text.split('\n')
    in_table = False
    header_cols = None
    rows = []

    for line in lines:
        stripped = line.strip()

        # Look for the "Units:" or "Connections:" label
        if stripped == table_header_keyword:
            in_table = True
            continue

        if not in_table:
            continue

        # Skip separator lines
        if stripped.startswith('+') and stripped.endswith('+'):
            continue

        # Empty line after table ends it
        if not stripped:
            if header_cols is not None:
                break
            continue

        # Parse pipe-delimited row
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if header_cols is None:
                header_cols = cells
            else:
                row = {}
                for i, col in enumerate(header_cols):
                    row[col] = cells[i] if i < len(cells) else ''
                rows.append(row)

    return rows


def _parse_units_table(section_text):
    """Extract unit data from the Units: table."""
    rows = _parse_tabulate_table(section_text, 'Units:')
    units = []
    for row in rows:
        name = row['Name']
        crit_dev = float(row['CritDev'])
        output = float(row['Output'])
        max_dev = float(row['MaxDev'])
        crit_thresh = float(row['CritThresh'])
        status = row['Status']

        if status != 'Active':
            colour = 'inactive'
        elif abs(crit_dev) >= crit_thresh * max_dev:
            colour = 'saturated'
        else:
            colour = 'active'

        units.append({
            'name': name,
            'critDev': crit_dev,
            'output': output,
            'colour': colour,
        })
    return units


def _parse_connections_table(section_text, show_inactive):
    """Extract connection data from the Connections: table."""
    rows = _parse_tabulate_table(section_text, 'Connections:')
    conns = []
    for row in rows:
        active = row['Active'].strip() == 'True'
        if not active and not show_inactive:
            continue
        to_unit = row['Unit']
        from_unit = row['From']
        weight = float(row['Weight'])
        switch = int(row['Switch'])
        state = row['State'].strip()
        eff_weight = switch * weight
        is_self = (to_unit == from_unit)

        conns.append({
            'to': to_unit,
            'from': from_unit,
            'eff_weight': eff_weight,
            'state': state,
            'active': active,
            'is_self': is_self,
        })
    return conns


# ---------------------------------------------------------------------------
# TikZ generation internals
# ---------------------------------------------------------------------------

def _unit_positions(units, radius):
    """Compute (x, y) for each unit in a regular polygon, clockwise from top."""
    n = len(units)
    positions = {}
    for i, unit in enumerate(units):
        angle = math.pi / 2 - (2 * math.pi * i / n)  # start at top, go clockwise
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        positions[unit['name']] = (x, y)
    return positions


def _sanitize_node_id(name):
    """Convert a unit name to a valid TikZ node identifier."""
    return name.replace(' ', '').replace('-', '').replace('_', '')


def _tikz_preamble(title):
    """Return the LaTeX document preamble."""
    lines = [
        r'\documentclass[border=10pt]{standalone}',
        r'\usepackage{tikz}',
        r'\usetikzlibrary{arrows.meta, calc}',
        r'\begin{document}',
    ]
    if title:
        # Use a minipage to add the title above the tikzpicture
        lines.append(r'\begin{minipage}{\textwidth}')
        lines.append(r'\centering')
        safe_title = title.replace('_', r'\_').replace('&', r'\&')
        lines.append(r'\textbf{' + safe_title + r'}')
        lines.append(r'\vspace{0.5cm}')
        lines.append('')
    return '\n'.join(lines)


def _tikz_postamble(title):
    """Return the closing LaTeX commands."""
    lines = [r'\end{tikzpicture}']
    if title:
        lines.append(r'\end{minipage}')
    lines.append(r'\end{document}')
    return '\n'.join(lines)


def _format_weight(w):
    """Format effective weight with sign."""
    return f"{w:+.3f}"


def _loop_direction(index, n):
    """Choose loop direction for self-connections based on node position."""
    angle_deg = 90 - (360 * index / n)
    # Point the loop outward from the centre
    if angle_deg > 45:
        return 'above'
    elif angle_deg > -45:
        return 'right'
    elif angle_deg > -135:
        return 'below'
    else:
        return 'left'


def _build_tikz(units_data, conns_data, title, show_inactive,
                radius, node_radius, output_path):
    """Assemble the full TikZ document."""
    positions = _unit_positions(units_data, radius)
    n = len(units_data)

    parts = [_tikz_preamble(title)]

    # Begin tikzpicture with styles
    min_size = f"{node_radius * 2:.1f}cm"
    parts.append(r'\begin{tikzpicture}[')
    parts.append(r'    unit/.style={circle, draw, thick, minimum size=' + min_size + r', align=center, font=\small},')
    parts.append(r'    active/.style={unit, fill=green!10},')
    parts.append(r'    saturated/.style={unit, fill=red!15},')
    parts.append(r'    inactive/.style={unit, fill=gray!20},')
    parts.append(r'    manual conn/.style={-{Latex[length=3mm]}, blue!70!black, thick},')
    parts.append(r'    unisel conn/.style={-{Latex[length=3mm]}, orange!80!black, thick},')
    parts.append(r'    inactive conn/.style={-{Latex[length=2mm]}, gray!50, thin, dashed},')
    parts.append(r'    every edge quotes/.style={font=\footnotesize, auto},')
    parts.append(r']')

    # Nodes
    parts.append(r'  % Nodes')
    for i, unit in enumerate(units_data):
        node_id = _sanitize_node_id(unit['name'])
        x, y = positions[unit['name']]
        style = unit['colour']
        safe_name = unit['name'].replace('_', r'\_')
        crit_dev_str = f"{unit['critDev']:.3f}"
        output_str = f"{unit['output']:.3f}"
        label = (r'\textbf{' + safe_name + r'}' + r'\\' +
                 r'critDev: ' + crit_dev_str + r'\\' +
                 r'out: ' + output_str)
        parts.append(f'  \\node[{style}] ({node_id}) at ({x:.3f},{y:.3f}) {{{label}}};')

    parts.append('')

    # Connections
    parts.append(r'  % Connections')

    # Build index for unit ordering (to determine bend direction)
    unit_index = {u['name']: i for i, u in enumerate(units_data)}

    # Track pairs to alternate bend direction for bidirectional connections
    seen_pairs = set()

    for conn in conns_data:
        from_id = _sanitize_node_id(conn['from'])
        to_id = _sanitize_node_id(conn['to'])
        weight_label = _format_weight(conn['eff_weight'])

        if not conn['active']:
            style = 'inactive conn'
        elif conn['state'] == 'manual':
            style = 'manual conn'
        else:
            style = 'unisel conn'

        if conn['is_self']:
            # Self-connection loop
            idx = unit_index.get(conn['to'], 0)
            loop_dir = _loop_direction(idx, n)
            parts.append(
                f'  \\draw[{style}] ({to_id}) to[loop {loop_dir}] '
                f'node[{loop_dir}, font=\\footnotesize] {{{weight_label}}} ({to_id});'
            )
        else:
            # Inter-unit connection
            pair = (conn['from'], conn['to'])
            reverse_pair = (conn['to'], conn['from'])

            if reverse_pair in seen_pairs:
                bend = 'bend left=15'
            else:
                bend = 'bend left=15'
            seen_pairs.add(pair)

            parts.append(
                f'  \\draw[{style}] ({from_id}) to[{bend}] '
                f'node[font=\\footnotesize, auto] {{{weight_label}}} ({to_id});'
            )

    parts.append('')
    parts.append(_tikz_postamble(title))

    tex = '\n'.join(parts)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(tex)

    return tex


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate a TikZ topology diagram from a Homeostat log file.')
    parser.add_argument('log_path', help='Path to the .log file')
    parser.add_argument('--section', default='INITIAL', choices=['INITIAL', 'FINAL'],
                        help='Which section to use (default: INITIAL)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output .tex file path (prints to stdout if omitted)')
    parser.add_argument('--title', default=None,
                        help='Title for the diagram')
    parser.add_argument('--show-inactive', action='store_true',
                        help='Show inactive connections as dashed lines')
    parser.add_argument('--radius', type=float, default=3.5,
                        help='Circular layout radius in cm (default: 3.5)')
    parser.add_argument('--node-radius', type=float, default=1.2,
                        help='Node circle radius in cm (default: 1.2)')

    args = parser.parse_args()

    tex = generate_tikz_from_log(
        args.log_path,
        output_path=args.output,
        section=args.section,
        title=args.title,
        show_inactive=args.show_inactive,
        radius=args.radius,
        node_radius=args.node_radius,
    )

    if not args.output:
        print(tex)
