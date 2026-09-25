"""Huffman coding implemented from scratch — standard library only.

Pipeline
--------
1. ``build_frequency_table(text)`` -> ``{char: count}``
2. ``build_tree(freq)``            -> Huffman tree (min-heap via ``heapq``)
3. ``generate_codes(tree)``        -> ``{char: '0101...'}`` (tree traversal)
4. ``encode(text, codes)``         -> binary string
5. ``decode(bitstring, tree)``     -> original text (walk the tree)

Edge cases
----------
* empty text            -> ``None`` tree, ``{}`` codes, ``''`` bitstring
* one unique character  -> degenerate single-leaf tree; that character gets
                           the 1-bit code ``"0"`` so encode/decode still work
"""

import heapq
import itertools

# Monotonic tie-breaker so heapq never has to compare two Nodes with equal
# frequency directly (keeps output deterministic and avoids TypeError).
_order = itertools.count()


class Node:
    """A node in the Huffman tree; leaf nodes carry the character."""

    __slots__ = ("char", "freq", "left", "right", "_order")

    def __init__(self, char=None, freq=0, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right
        self._order = next(_order)

    def __lt__(self, other):
        # heapq pops the "smallest" first: lower freq wins, ties broken by
        # creation order so the tree (and the codes) are deterministic.
        return (self.freq, self._order) < (other.freq, other._order)

    @property
    def is_leaf(self):
        return self.left is None and self.right is None

    def __getstate__(self):
        # Compact pickled form (plain tuple instead of per-slot dict state),
        # which roughly halves the size of the tree stored in the file header.
        return (self.char, self.freq, self.left, self.right, self._order)

    def __setstate__(self, state):
        self.char, self.freq, self.left, self.right, self._order = state


def build_frequency_table(text):
    """Count how often each character occurs in ``text``."""
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    return freq


def build_tree(freq):
    """Build the Huffman tree using a min-heap (``heapq``).

    Repeatedly pop the two least-frequent nodes and push a new parent that
    holds both. When one node remains, it is the root of the tree.
    Returns ``None`` for an empty frequency table.
    """
    if not freq:
        return None

    heap = [Node(char=ch, freq=n) for ch, n in freq.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        heapq.heappush(
            heap, Node(freq=left.freq + right.freq, left=left, right=right)
        )

    return heap[0]


def generate_codes(tree):
    """Assign a binary code to every character by traversing the tree.

    Left edge = ``"0"``, right edge = ``"1"``. Characters closer to the root
    (the frequent ones) end up with shorter codes. A degenerate single-leaf
    tree (only one unique character) gets the 1-bit code ``"0"``.
    """
    if tree is None:
        return {}
    if tree.is_leaf:
        return {tree.char: "0"}

    codes = {}
    stack = [(tree, "")]
    while stack:
        node, prefix = stack.pop()
        if node.is_leaf:
            codes[node.char] = prefix
        else:
            stack.append((node.left, prefix + "0"))
            stack.append((node.right, prefix + "1"))
    return codes


def encode(text, codes):
    """Translate ``text`` into a flat binary string using ``codes``."""
    return "".join(codes[ch] for ch in text)


def decode(bitstring, tree):
    """Walk ``tree`` bit by bit to recover the original text.

    Raises ``ValueError`` if the bitstream references a code that does not
    exist in the tree (i.e. the file is corrupt).
    """
    if tree is None or not bitstring:
        return ""
    if tree.is_leaf:  # degenerate tree: every bit is the same character
        return tree.char * len(bitstring)

    out = []
    node = tree
    for bit in bitstring:
        node = node.left if bit == "0" else node.right
        if node is None:
            raise ValueError("Corrupted bitstream: code is not in the tree")
        if node.is_leaf:
            out.append(node.char)
            node = tree
    return "".join(out)
