
# BPRESS v1.0.0

Author: Armand Bouillet  
License: Open source with attribution (see License section)

---

## Overview

BPRESS is a Python-based compression engine that performs structural analysis on binary files and compresses them using a custom prefix mapping system. The algorithm uses a combination of bitwise tokenization and flip-flop detection across bitstreams to identify patterns and apply digest encodings.

This project is not meant to compete with production-grade compressors like zstd or Brotli. It's a self-contained, research-driven implementation that helped me explore entropy modeling, bit-level operations, and multi-pass compression logic. It includes entropy testing notebooks, custom test data generators, and full unit tests.

---

## File structure
bpress/
├── bpress_v1_0_0.py           # Main compression engine (class-based)
├── main.py                    # Entry point script for compression + analysis
├── utilities.py               # Timing and test decorators
├── byte_analysis_nb.ipynb     # Jupyter notebook for entropy modeling
├── test_bpressv1_0_0.py       # Unit tests for core functions
├── Pipfile
├── Pipfile.lock

# Data generation scripts
├── gen_test_files.py          # Random data generator (1MB - 500MB)
├── gen_syn_data.py            # Synthetic high-entropy generator with flip-flop control
├── gen_semi_strc_data.py      # Simple repeating pattern file (e.g. ABC123XYZ)
├── gen_encrypted_file.py      # AES-256 encrypted file generator (1MB)

---

## How it works

BPRESS operates in multiple stages:

1. **Scan phase**  
   Computes bit frequencies, transition counts, and 3-bit flip-flop metrics.

2. **Protocol phase**  
   Selects a delimiter bit based on bit statistics and builds a custom digest table that maps token lengths to variable-length binary codes.

3. **Compression phase**  
   Encodes the bitstream using the generated digest protocol, storing the lengths between delimiter bits using the binary digest format.

4. **Finalization**  
   Applies optional bit stuffing or padding, writes out the compressed stream, and appends end flags or metadata.

The result is a bit-aligned binary file with a custom compression header and mapped structure.

---

## Entropy analysis

The included Jupyter notebook analyzes the internal structure of all 256 8-bit values by measuring flip-flop density using a rolling 3-bit window. The results are grouped and used to explore the theoretical entropy contribution of different byte patterns.

The notebook also includes:

- Optimal entropy distribution modeling
- Flip-flop bucketization logic
- Byte structure classification by flip-flop count
- Foundation for testing synthetic data compression

---

## Test data

Included are four generators to test various input conditions:

- `gen_test_files.py` – Random binary blobs for high-entropy input
- `gen_syn_data.py` – Structured entropy streams with flip-flop suppression
- `gen_semi_strc_data.py` – Repeating ASCII pattern files
- `gen_encrypted_file.py` – High-entropy AES-256-CBC encrypted file

Each script can be modified to generate custom datasets of varying size and structure.

---

## Tests

The test script `test_bpress_v1_0_0.py` includes direct unit tests for the following:

- Bit counting
- Transition detection
- Flip-flop counting
- Delimiter configuration (including override behavior)

Tests use basic assertions and are structured to be migrated into pytest or another test runner if needed.

---

## License

Open source with attribution.

You are free to use, modify, or redistribute this project or any portion of it for any purpose, personal or commercial. All I ask is that you credit the original author, Armand Bouillet, in your documentation or project notes if you use the ideas or code structure from this repository.

---

## Setup and usage

Install dependencies using pipenv:
pipenv install
pipenv install bitarray, matplotlib, pytest, cryptography, jupyter notebook
pipenv shell


To run compression on a batch of generated files and view results:


This will compress and analyze a group of structured 1MB test files, output the results to the console, and allow you to inspect the output `.press` files.

---

## Notes

- This project is not optimized for compression ratio and is not meant to replace existing compressors. It's a proof of concept and learning tool.
- The class-based engine is the current final version.
- The project uses `bitarray` for bit-level operations and Python’s type system extensively throughout.

---

## Contact

If you use this, fork it, or build on the ideas here, attribution is appreciated. Feedback or contributions are also welcome.

README was generated using ChatGPT 4o.
