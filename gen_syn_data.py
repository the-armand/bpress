#generate syntehtically structured data for testing 
import os
from bitarray import bitarray
from typing import *

file_sizes = {
    "1MB": 1 * 1024 * 1024,
    "2MB": 2 * 1024 * 1024,
    "3MB": 3 * 1024 * 1024,
    "5MB": 5 * 1024 * 1024
}

base_path = "./test_files/structured_high_entropy"


#utilities

def generate_structured_stream(
    buffer_size: int = 4 * 1024,
    scrub_rate: str = "full",
    trailing_bits: Optional[bitarray] = None
) -> Tuple[bytes, bitarray]:
    if scrub_rate not in {"half", "full"}:
        raise ValueError("Invalid scrub_rate — must be 'half' or 'full'")

    bits_ran = bitarray()
    bits_ran.frombytes(os.urandom(buffer_size))

    # Handle cross-boundary flip-flops using last 2 + current first 2 bits
    if trailing_bits and len(trailing_bits) == 2 and len(bits_ran) >= 2:
        edge = trailing_bits + bits_ran[:2]  # 4 bits

        # There are two 3-bit windows here: [0:3] and [1:4]
        for offset in [0, 1]:
            a, b, c = edge[offset], edge[offset + 1], edge[offset + 2]
            if a != b and a == c:
                if scrub_rate == "full" or (scrub_rate == "half" and int.from_bytes(os.urandom(1), "big") % 2 == 0):
                    # Flip middle bit in bits_ran to kill the flip-flop
                    index_to_flip = offset  # 0 or 1, which corresponds to bits_ran[0] or [1]
                    bits_ran[index_to_flip] ^= 1

    # Internal scrub
    i = 0
    while i < len(bits_ran) - 2:
        a, b, c = bits_ran[i], bits_ran[i + 1], bits_ran[i + 2]
        if a != b and a == c:
            if scrub_rate == "full" or (scrub_rate == "half" and i % 2 == 0):
                bits_ran[i + 2] ^= 1
                i += 3
                continue
        i += 1

    return bits_ran.tobytes(), bits_ran[-2:]



def generate_files(
    path: str, 
    num_files: int, 
    sizes: List[str], 
    structure_level: str, 
    buffer_size: int = 4 * 1024
):
    if structure_level not in ["half", "full"]:
        raise ValueError("please enter a valid structure level")
    
    path = path.strip("/")
    os.makedirs(path, exist_ok=True)

    output_sizes: Optional[List[Tuple[str,int]]] = []

    for size in sizes:
        if size in file_sizes:
            output_sizes.append((size, file_sizes[size]))
     
    for file_size in output_sizes:
        for i in range(num_files):
            file_path: str = f"{path}/{structure_level}_struc_high_ent_{file_size[0]}_{i+1}.bin"

            with open(file_path, "wb") as f:
                num_of_calls = round(file_size[1] / buffer_size)
                trailing_bits = None

                for _ in range(num_of_calls):
                    stream, trailing_bits = generate_structured_stream(buffer_size, structure_level, trailing_bits)
                    f.write(stream)

    print("files created")

def main():
    generate_files(base_path, 10, ["1MB"], "full")

if __name__ == "__main__":
    main()
    

    








