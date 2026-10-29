"""A small Clausewitz (HOI4 script) parser that keeps source positions.

Rewrites are done by replacing the source text of individual nodes, so
everything that isn't changed, comments and formatting included, is kept.
"""
import re

TOKEN_RE = re.compile(r'(?P<ws>\s+)|(?P<comment>#[^\n]*)|(?P<str>"(?:[^"\\\n]|\\.)*")'
                      r'|(?P<op>[<>!]=|==|[{}=<>])|(?P<word>[^\s{}=<>!#"]+)')
TYPED_BLOCKS = {'rgb', 'hsv', 'hsv360', 'RGB', 'HSV'}


class Node:
    __slots__ = ('key', 'op', 'value', 'start', 'end', 'open', 'close')

    def __init__(self, key, op, value, start, end, open_=None, close=None):
        self.key, self.op, self.value = key, op, value
        self.start, self.end = start, end          # span of the whole node
        self.open, self.close = open_, close       # span of '{' ... '}' for blocks

    @property
    def is_block(self):
        return isinstance(self.value, list)

    def __repr__(self):
        return f'Node({self.key!r} {self.op} {"{...}" if self.is_block else self.value!r})'


class ParseError(Exception):
    pass


def tokenize(src):
    out = []
    for m in TOKEN_RE.finditer(src):
        kind = m.lastgroup
        if kind in ('ws', 'comment'):
            continue
        out.append((kind, m.group(), m.start(), m.end()))
    return out


def parse(src):
    """Parse a whole file into a list of top-level nodes."""
    toks = tokenize(src)
    pos = 0

    def block(depth):
        nonlocal pos
        items = []
        while pos < len(toks):
            kind, text, s, e = toks[pos]
            if text == '}':
                if depth == 0:
                    raise ParseError(f'unexpected }} at offset {s}')
                return items
            if text == '{':
                pos += 1
                children = block(depth + 1)
                close = closing()
                items.append(Node(None, None, children, s, close, s, close))
                continue
            if kind == 'op':
                raise ParseError(f'unexpected {text!r} at offset {s}')
            pos += 1
            if pos < len(toks) and toks[pos][0] == 'op' and toks[pos][1] not in '{}':
                op = toks[pos][1]
                pos += 1
                if pos >= len(toks):
                    raise ParseError(f'missing value after {text!r} at offset {s}')
                vkind, vtext, vs, ve = toks[pos]
                if vtext == '{':
                    pos += 1
                    children = block(depth + 1)
                    close = closing()
                    items.append(Node(text, op, children, s, close, vs, close))
                elif vkind == 'op':
                    raise ParseError(f'unexpected {vtext!r} at offset {vs}')
                else:
                    pos += 1
                    if vtext in TYPED_BLOCKS and pos < len(toks) and toks[pos][1] == '{':
                        pos += 1
                        block(depth + 1)
                        ve = closing()
                        vtext = src[vs:ve]
                    items.append(Node(text, op, vtext, s, ve))
            else:
                items.append(Node(None, None, text, s, e))
        if depth:
            raise ParseError('missing } at end of file')
        return items

    def closing():
        nonlocal pos
        if pos >= len(toks) or toks[pos][1] != '}':
            raise ParseError('missing } at end of file')
        pos += 1
        return toks[pos - 1][3]

    return block(0)


def walk(nodes):
    for n in nodes:
        yield n
        if n.is_block:
            yield from walk(n.value)
