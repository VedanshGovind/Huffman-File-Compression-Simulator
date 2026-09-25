"""File-level compression built on top of ``huffman.py``.

Compressed file layout (``.hcm``)
---------------------------------
::

    +------------------+-------------------------+--------------------------+
    | magic "HUFFSIM1" | header length (4 B,    | pickled (tree, padding)  |
    | (8 bytes)        | big-endian)             | + packed bit payload     |
    +------------------+-------------------------+--------------------------+

* **header** — a pickled ``(tree, padding)`` tuple. Storing the Huffman tree
  itself means any compressed file can be decompressed independently: the
  code table is rebuilt from the stored tree, nothing else is needed.
* **padding** — how many zero bits (0–7) were appended to the bitstream so
  it fills whole bytes; the decoder strips them off again.
* **payload** — the Huffman bitstream packed into real bytes.

Also usable as a tiny CLI:

    python compressor.py compress  in.txt  out.hcm
    python compressor.py decompress in.hcm  out.txt
"""

import pickle
import struct

import huffman

MAGIC = b"HUFFSIM1"
MAX_HEADER = 1 << 20  # 1 MiB sanity cap for the pickled header


def compress_text(text):
    """Compress ``text`` and return ``(compressed_bytes, stats)``.

    ``stats`` holds original/compressed sizes, space saved, and the
    character code table (most frequent characters first) for display.
    """
    freq = huffman.build_frequency_table(text)
    tree = huffman.build_tree(freq)
    codes = huffman.generate_codes(tree)
    bits = huffman.encode(text, codes)

    payload, padding = _bits_to_bytes(bits)
    header = pickle.dumps((tree, padding))
    compressed = MAGIC + struct.pack(">I", len(header)) + header + payload

    original_size = len(text.encode("utf-8"))
    compressed_size = len(compressed)
    stats = {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "bytes_saved": original_size - compressed_size,
        "percent_saved": (
            round((original_size - compressed_size) / original_size * 100, 2)
            if original_size
            else 0.0
        ),
        "total_chars": len(text),
        "unique_chars": len(freq),
        "code_table": [
            {"char": ch, "code": codes[ch], "freq": freq[ch]}
            for ch in sorted(freq, key=lambda c: (-freq[c], c))
        ],
    }
    return compressed, stats


def decompress_bytes(data):
    """Recover the original text from compressed bytes.

    Raises ``ValueError`` with a human-readable message when the file is
    not a valid compressed file.
    """
    if len(data) < len(MAGIC) + 4:
        raise ValueError("File is too small to be a compressed file")
    if data[: len(MAGIC)] != MAGIC:
        raise ValueError("Not a compressed file produced by this app (bad magic)")

    (header_len,) = struct.unpack(">I", data[len(MAGIC):len(MAGIC) + 4])
    if header_len > MAX_HEADER:
        raise ValueError("Header size is unreasonably large; refusing to read")

    start = len(MAGIC) + 4
    end = start + header_len
    if end > len(data):
        raise ValueError("Truncated file: the header is cut off")

    tree, padding = pickle.loads(data[start:end])  # our own files, local tool
    payload = data[end:]

    bits = _bytes_to_bits(payload)
    if padding:
        bits = bits[:-padding]
    return huffman.decode(bits, tree)


def compress_file(src, dst):
    """Compress the text file ``src`` into ``dst``; returns the stats dict."""
    with open(src, "r", encoding="utf-8") as f:
        text = f.read()
    data, stats = compress_text(text)
    with open(dst, "wb") as f:
        f.write(data)
    return stats


def decompress_file(src, dst):
    """Decompress ``src`` back into a text file at ``dst``; returns size in bytes."""
    with open(src, "rb") as f:
        text = decompress_bytes(f.read())
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    return len(text.encode("utf-8"))


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def _bits_to_bytes(bits):
    """Pack a binary string into the smallest possible byte sequence.

    Returns ``(bytes, padding)`` where ``padding`` is the number of zero
    bits appended to reach a whole number of bytes.
    """
    padding = (8 - len(bits) % 8) % 8
    if padding:
        bits += "0" * padding
    if not bits:
        return b"", 0
    return int(bits, 2).to_bytes(len(bits) // 8, "big"), padding


def _bytes_to_bits(payload):
    """Invert ``_bits_to_bytes`` (leading zeros restored from byte count)."""
    if not payload:
        return ""
    return format(int.from_bytes(payload, "big"), f"0{len(payload) * 8}b")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4 or sys.argv[1] not in ("compress", "decompress"):
        print("Usage: python compressor.py <compress|decompress> <input> <output>")
        raise SystemExit(1)

    action, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    if action == "compress":
        stats = compress_file(src, dst)
        delta = "saved" if stats["bytes_saved"] >= 0 else "larger — header overhead"
        print(
            f"{src} -> {dst}: {stats['original_size']} B -> {stats['compressed_size']} B "
            f"({stats['percent_saved']:.2f}% {delta})"
        )
    else:
        size = decompress_file(src, dst)
        print(f"{src} -> {dst}: {size} B recovered")
