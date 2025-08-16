# gen_structured_file.py
from pathlib import Path

# 2MB = 2 * 1024 * 1024 = 2,097,152 bytes
# We'll fill it with a repeating structured pattern
PATTERN = b"ABC123XYZ"  # 9 bytes
REPEAT_COUNT = (2 * 1024 * 1024) // len(PATTERN)

structured_data = PATTERN * REPEAT_COUNT

# Output path
base_dir = Path(__file__).resolve().parent
out_path = base_dir / "test_files" / "test_file_2MB_structured.bin"

# Ensure directory exists
out_path.parent.mkdir(parents=True, exist_ok=True)

# Write the file
with open(out_path, "wb") as f:
    f.write(structured_data)

print(f"Structured 2MB test file created at: {out_path}")
