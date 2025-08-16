import os

# Sizes in bytes
FILE_SIZES = {
    '1MB': 1 * 1024 * 1024,
    '10MB': 10 * 1024 * 1024,
    '100MB': 100 * 1024 * 1024,
    '500MB': 500 * 1024 * 1024
}

# Directory to store files
OUTPUT_DIR = "test_files"

def generate_random_file(filename, size_bytes):
    with open(filename, 'wb') as f:
        f.write(os.urandom(size_bytes))

def main():
    # Create directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for label, size in FILE_SIZES.items():
        for i in range(0,10): 
            filename = f"test_file_{label}_{i}.bin"
            filepath = os.path.join(OUTPUT_DIR, filename)
            print(f"Creating {filepath} ({size // (1024 * 1024)}MB)...")
            generate_random_file(filepath, size)

    print("All test files created successfully.")

if __name__ == "__main__":
    main()
