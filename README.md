# 🗜️ Huffman File Compression Simulator

A from-scratch implementation of **Huffman coding** wrapped in a simple Flask web app. Upload any text file, compress it losslessly, inspect the generated code table, and decompress it back to the exact original — byte for byte.

No compression libraries used. The tree, the codes, and the bit-packing are all built by hand in pure Python.

---

## ✨ Features

- **Lossless compression** — the recovered file matches the original exactly, including whitespace, unicode, and emoji
- **Live stats** — original size, compressed size, bytes saved, and percentage saved
- **Code table view** — see the actual binary code assigned to every character, sorted by frequency
- **Self-contained `.hcm` files** — the Huffman tree is stored in the file header, so any `.hcm` file can be decompressed on its own
- **Simple web UI** — drag, drop, compress, decompress
- **CLI mode** — run compression from the command line without the web server

---

## 🧠 How It Works

1. **Frequency table** — count how often each character appears in the file
2. **Build the tree** — repeatedly merge the two least-frequent nodes using a min-heap, until one root remains
3. **Generate codes** — walk the tree; frequent characters end up with short codes, rare ones with long codes
4. **Encode** — replace every character with its binary code and pack the bits into bytes
5. **Decode** — walk the tree bit by bit to reconstruct the original text

```
+------------------+--------------------------+---------------------------+
| magic "HUFFSIM1" | header length (4 bytes)  | pickled (tree, padding)  |
| (8 bytes)        |                          | + packed bit payload     |
+------------------+--------------------------+---------------------------+
```

---

## 🚀 Getting Started

### Requirements
- Python 3.11+
- Flask

```bash
pip install flask
```

### Run the web app

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

### Use the CLI

```bash
# Compress
python compressor.py compress input.txt output.hcm

# Decompress
python compressor.py decompress output.hcm restored.txt
```

---

## 📁 Project Structure

```
├── app.py               # Flask routes (upload, compress, decompress)
├── compressor.py         # File-level compression, .hcm format, CLI
├── huffman.py            # Core Huffman algorithm (tree, codes, encode/decode)
├── templates/
│   └── index.html        # Upload UI
└── compression_test.txt  # Sample file for round-trip testing
```

---

## 🧪 Testing a Round Trip

`compression_test.txt` is included specifically to stress-test the codec — it mixes prose, numbers, code snippets, punctuation, and unicode (including an emoji). Compress it, decompress the result, and diff against the original to confirm a perfect round trip.

---

## ⚠️ Notes

- Max upload size is capped at 32 MB (configurable in `app.py`)
- Text is decoded as UTF-8 with a Latin-1 fallback for non-UTF-8 files
- `.hcm` files are only valid when read back by this project's own decompressor
