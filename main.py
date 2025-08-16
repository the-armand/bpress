import bpress_v1_0_0 as bp

def main():

    """
    First we access and then compress and write our gernerated structured entropy data
    Next we access the BPRESS DATA tool to report data on both the original, and compressed files
    """

    #step 1 compress target files
    for i in range(1, 11):
        file_num = i
        in_path = f"./test_files/structured_high_entropy/full_struc_high_ent_1MB_{file_num}.bin"
        out_path = f"./test_outputs/structured_high_entropy/full_struc_high_ent_1MB_{file_num}.press"
        with bp.BPRESS_COMPRESS(in_path, out_path, 2 * 1024) as f:
            print(f)
            print("compression complete\n")

    #step 2 analyze
    for i in range(1,11):
        file_num = i
        original_path = f"./test_files/structured_high_entropy/full_struc_high_ent_1MB_{file_num}.bin"
        compressed_path = f"./test_outputs/structured_high_entropy/full_struc_high_ent_1MB_{file_num}.press"
        file_group = [original_path, compressed_path]
        for file in file_group:
            with bp.BPRESS_DATA(file) as scan:
                print(f"file: {file.strip("_path")} num: {file_num}")
                print(scan)

if __name__ == "__main__":
    main()

    







