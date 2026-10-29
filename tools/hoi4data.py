"""Readers for the HOI4 game data the compatibility tools need."""
import glob
import os
import re


def read_text(path):
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        return f.read()


def strip_comments(text):
    return re.sub(r'#[^\n]*', '', text)


def read_definitions(root):
    """Province id -> (rgb, kind, continent index) from map/definition.csv."""
    out = {}
    with open(os.path.join(root, 'map', 'definition.csv'), encoding='utf-8', errors='replace') as f:
        for line in f:
            c = line.strip().split(';')
            if len(c) < 8 or not c[0].isdigit() or c[0] == '0':
                continue
            cont = re.match(r'\d+', c[7])
            out[int(c[0])] = ((int(c[1]), int(c[2]), int(c[3])), c[4], int(cont.group()) if cont else 0)
    return out


def read_continents(root):
    """Continent names in index order (index 1 is the first entry)."""
    text = strip_comments(read_text(os.path.join(root, 'map', 'continent.txt')))
    body = re.search(r'continents\s*=\s*\{([^}]*)\}', text).group(1)
    return [None] + body.split()


def read_state_names(root):
    names = {}
    for path in glob.glob(os.path.join(root, 'localisation', 'english', '*state*_l_english.yml')):
        for m in re.finditer(r'^\s*STATE_(\d+):\d*\s*"([^"]*)"', read_text(path), re.M):
            names.setdefault(int(m.group(1)), m.group(2))
    return names


def read_states(root):
    """State id -> {name, provinces, vps (province, value), cores, owner}.

    Some copies of the game carry stale state files from older versions next to
    the current ones; when an id is defined twice, the file named after the
    state's current localised name wins.
    """
    found = {}
    for path in sorted(glob.glob(os.path.join(root, 'history', 'states', '*.txt'))):
        text = strip_comments(read_text(path))
        m = re.search(r'\bid\s*=\s*(\d+)', text)
        if not m:
            continue
        provs = re.search(r'provinces\s*=\s*\{([^}]*)\}', text)
        name = re.sub(r'^\d+\s*-?\s*', '', os.path.basename(path)[:-4]).strip()
        found.setdefault(int(m.group(1)), []).append(dict(
            name=name,
            provinces=[int(x) for x in provs.group(1).split()] if provs else [],
            vps=[(int(p), float(v)) for p, v in re.findall(r'victory_points\s*=\s*\{\s*(\d+)\s+([\d.]+)\s*\}', text)],
            cores=set(re.findall(r'add_core_of\s*=\s*([A-Z][A-Z0-9]{2})\b', text)),
            owner=(re.search(r'\bowner\s*=\s*([A-Z][A-Z0-9]{2})\b', text) or [None, None])[1],
        ))
    names = read_state_names(root) if any(len(v) > 1 for v in found.values()) else {}
    out = {}
    for sid, candidates in found.items():
        if len(candidates) > 1:
            current = [c for c in candidates if c['name'].lower() == names.get(sid, '').lower()]
            if len(current) != 1:
                print(f'warning: state {sid} is defined by several files in {root}; using "{candidates[0]["name"]}"')
            candidates = current or candidates
        out[sid] = candidates[0]
    return out


def read_country_tags(root):
    tags = set()
    for path in glob.glob(os.path.join(root, 'common', 'country_tags', '*.txt')):
        text = strip_comments(read_text(path))
        tags |= set(re.findall(r'^\s*([A-Z][A-Z0-9]{2})\s*=', text, re.M))
    return tags


def read_capitals(root):
    out = {}
    for path in glob.glob(os.path.join(root, 'history', 'countries', '*.txt')):
        tag = os.path.basename(path)[:3]
        m = re.search(r'\bcapital\s*=\s*(\d+)', strip_comments(read_text(path)))
        if m:
            out[tag] = int(m.group(1))
    return out


def read_province_bitmap(root):
    """map/provinces.bmp as a flat array of packed 0xRRGGBB colours."""
    import numpy as np
    from PIL import Image
    img = np.asarray(Image.open(os.path.join(root, 'map', 'provinces.bmp')).convert('RGB'), dtype=np.uint32)
    return (img[..., 0] << 16 | img[..., 1] << 8 | img[..., 2]).ravel()
