# bpress version 1.0.0. armand bouillet 2025

import os
from typing import (
    Any, Callable, Dict, List, Optional, Tuple, Union, TypedDict, Iterable, BinaryIO
)
from pathlib import Path
from bitarray import bitarray  # type: ignore

class ScannedData(TypedDict):
    bit_freqs: Dict[int, int]
    transitions: int
    flip_flops: int

class BPRESS:
    
    #lookup table for most common length digests
    token_digest_table: Dict[int, str] = {1 : "0", 2 : "100", 3 : "101", 4 : "1100", 5 : "1101", 6 : "111000", 7 : "111001", 8 : "111010", 9 : "111011", 10 : "11110000", 11 : "11110001", 12 : "11110010", 13 : "11110011", 14 : "11110100", 15 : "11110101", 16 : "11110110", 17 : "11110111"}
    """
    this function allows us to generate a binary string formatted using a head flag in the form:
    0, 100, 110, 1110, 11110 
    along with a tail that grows by an additional bit in length with each bucketization.
    this creates a distinctly formatted bucketized mapping system, whereby we have computed
    the first several outputs in the table above, which can be updated for missing values using
    the function below.

    digest head and tail lengths grow linearly, increasing by 1 bit in length per bucket group.
    the relationship [head length] = [tail length] + 2 remains constant for all bucket groups 
    beginning with the "100" and up. 

    these unique binary digests are mapped to a key represented by an integer, which denotes
    length of contiguous complement bits between 2 identical delimiters for a binary input.

    the final format of the binary digest is as follows:

    head:
    111110 -> denotes bucketization
    tail:
    0011 -> represents mapped index decimal value within bucketized group
    digest:
    111110 0011 -> value 3 in the group associated with the given flag -> maps to exactly 1 interval length
    """
    def __init__(self):
        # core shared state with precise types
        self.scanned_data: ScannedData = {
            "bit_freqs": {0: 0, 1: 0},
            "transitions": 0,
            "flip_flops": 0,
        }
                # declare attributes that other methods touch; initialize safely
        self.file_in: Optional[int] = None
        self.file_out: Optional[int] = None
        self.buffer: int = 4 * 1024
        self.imp_size: int = 0

        self.bytes_read_pass_one: int = 0
        self.bytes_read_pass_two: int = 0
        self.bytes_compressed: int = 0

        self.scan_complete: bool = False
        self.protocol_complete: bool = False
        self.compression_complete: bool = False
        self.protocol_update_complete: bool = False
        self.writing_complete: bool = False
        self.check_complete: bool = False

        self.delimiter_bit: Optional[int] = None
        self.protocol_header: Optional[bitarray] = None
        self.bit_stuffing: bool = False
        self.padding: Optional[str] = None
        self.end_bits: Optional[bitarray] = None

    def map_token_digest(self, token_len: int, output_dict: Dict[int, str] = token_digest_table) -> bitarray:
                
        if token_len in output_dict:
            raise ValueError("token length map already exists")

        #set in proceeding steps
        tail_len: Optional[int] = None
        bucket_values: Optional[List[int]] = None

        #these values are set based on the next possible value in our token digest map
        min_token_len: int = 18
        min_tail_len: int = 4

        #synthesize possible token length range based on tail bucketization
        def get_input_len_range() -> Tuple[int, int]:
            range_max: int = 5
            n: int = min_tail_len - 2
            while n >= 0:
                range_max += 2**(min_tail_len - n)
                n -= 1
            return (min_token_len, range_max)

        #find appriopriate tail bucketization length for input. Store value
        while True:
            token_len_range_t: Tuple[int, int] = get_input_len_range()
            token_len_range_l: List[int] = list(range(token_len_range_t[0], token_len_range_t[1] + 1))

            if token_len in token_len_range_l:
                tail_len = min_tail_len
                bucket_values = token_len_range_l
                break

            min_token_len = (token_len_range_t[1] + 1)
            min_tail_len += 1

        #synthesize full bin stem
        flag_stem: str = "".join([str(1) for _ in range(0, tail_len + 1)] + ["0"])

        #find the index and tail value for token
        token_bucket_index: int = bucket_values.index(token_len)
        bin_typing: str = f"{tail_len}b"
        if tail_len < 10:
            bin_typing: str = f"0{tail_len}b"

        tail_stem: str = format(token_bucket_index, bin_typing)

        #assemble final stem and update digest table
        token_bin_stem: str = flag_stem + tail_stem
        output_dict[token_len] = token_bin_stem

        return bitarray(token_bin_stem)


    """
    the purpose of this function is to receive a token length as an interger and either:
    A: scan and return the appropriate binary stem value for this length from the pre-computed table
    B: compute the new binary stem value, update the table and return this value, formatted as a bitarray
    """

    #compress a given token using lookup table or digest generating function
    def compress_token(
            self,
            token_length: int, 
            digest_gen: Optional[Callable[..., bitarray]] = None,
            digest_map: Optional[Dict[int,str]] = None, 
    ) -> bitarray:
        
        if digest_gen is None:
            digest_gen = self.map_token_digest
        if digest_map is None:
            digest_map = self.token_digest_table


        if not token_length in digest_map:
            digest = digest_gen(token_length)
            return digest
        
        return bitarray(digest_map[token_length])
    
    """
    pulls out the next token length and also returns the new bit_stream for reassignment
    """
    def pull_token(self, bit_stream: bitarray, delimiter: int) -> Tuple[int, bitarray]:
        for i in range(len(bit_stream)):
            if bit_stream[i] == delimiter:
                token_length = i + 1
                return token_length, bit_stream[token_length:]
        raise ValueError("Delimiter not found")

    """
    small utilities that are used to scan the compression target on initial pass.
    utilities will be used to create a dictionary of data that can be used to dynamically
    make decisions about best path forward
    """

    #@test_status("level_1")
    def count_bits(self, bit_stream: bitarray) -> List[int]:
        freq_0 = bit_stream.count(0)
        freq_1 = bit_stream.count(1)
        return [freq_0, freq_1]
    
    #@test_status("level_1")   
    def count_transitions(self, bit_stream: bitarray) -> int:
        transitions = 0
        if len(bit_stream) <= 1:
            return transitions
        for i in range(0,len(bit_stream)-1):
            if bit_stream[i] != bit_stream[i+1]:
                transitions += 1
        return transitions
    
    #@test_status("level_1")   
    def count_flip_flops(self, bit_stream: bitarray) -> int:
        if len(bit_stream) < 3:
            return 0
        flip_flops = sum(1 for i in range(0,len(bit_stream)-2) if bit_stream[i] != bit_stream[i+1] and bit_stream[i] == bit_stream[i+2])
        return flip_flops


    """
    Flexible modular delimiter setup allowing for future customization:
    default is to select delimiter naively based on simple bit frequency. in this case we could pass in
    the argument for "data" as : {0:x, 1:y} where x & y represent the respective frequency of each bit.
    We can also set a mode to test different naive delimiter settings, as well as pass other types of data
    into the delimiter, along with a callback function's identifer to pass the data and any other custom
    positional or keyword arguments down to this callback.

    standard delimiting protocol TBD.
    """
    
    def config_delimiter(
        self,
        data: Any,
        *args: Any,
        mode: str = "low",
        behaviour: Optional[Callable[..., int]] = None,
        **kwargs: Any
    ) -> int:
        if mode == "custom":
            if not callable(behaviour):
                raise ValueError("Custom mode requires a callable behaviour")
            return behaviour(data, *args, **kwargs)

        bf: Dict[int, int] = data["bit_freqs"] 

        if mode == "high":
            return max(bf, key=bf.get) #type: ignore

        if mode == "low":
            return min(bf, key=bf.get) #type: ignore

        raise ValueError(f"Unknown mode: {mode}")

    
        # method toolkit to aid with context manager control flow
    def update_scanned_data (self, bit_stream: bitarray):
        scan_bits: List[int] = self.count_bits(bit_stream)
        self.scanned_data["bit_freqs"][0] += scan_bits[0]
        self.scanned_data["bit_freqs"][1] += scan_bits[1]
        self.scanned_data["transitions"] += self.count_transitions(bit_stream)
        self.scanned_data["flip_flops"] += self.count_flip_flops (bit_stream)

    def scan_stream(self):
        last: bitarray = bitarray()
        while True:
            #generate bitarray stream
            buffer = os.read(self.file_in, self.buffer) #type: ignore
            self.bytes_read_pass_one += len(buffer)
            stream: bitarray = bitarray()
            stream.frombytes(buffer)
            first = stream[:2]
  

            #gather and update data
            self.update_scanned_data(stream)

            if last and buffer:
                if last[-1] != stream[0]:
                    self.scanned_data["transitions"] += 1
                
                edge_bits = last + stream[:2]
                flip_flops: int = self.count_flip_flops(edge_bits)

                if flip_flops > 0:
                    self.scanned_data["flip_flops"] += flip_flops

            last = stream[-2:]

            #check for end of file and close if so
            if len(buffer) < self.buffer and self.bytes_read_pass_one == self.imp_size:
                self.scan_complete = True
                break
            elif len(buffer) < self.buffer:
                break



class BPRESS_DATA(BPRESS):
    def __init__ (self, file_path):
        self.file_path = file_path
        self.buffer = 4 * 1024
        self.basename = os.path.basename(self.file_path)
        self.imp_size = os.path.getsize(self.file_path)
        self.bytes_read_pass_one = 0

        self.scanned_data = {
        "bit_freqs" : {0: 0, 1: 0},
        "transitions" : 0,
        "flip_flops" : 0
        }
    
    def __repr__ (self):
        return_string = f"<BPRESS DATA SUITE>\n\n<Scanned Data>\nInternal Scan: {self.scanned_data}\nFile Size: {self.imp_size}"
        return return_string
    
    def __enter__ (self):
        self.file_in = os.open(self.file_path, os.O_RDONLY)
        self.scan_stream()
        return self

    def __exit__ (self, exc_type, exc_val, exc_tb):
        os.close(self.file_in) #type: ignore



class BPRESS_COMPRESS(BPRESS):

    #bpress compress object instantiated
    def __init__(
            self, imp_path: str, 
            exp_path: str, 
            buffer: int = 4 * 1024, 
            delimiter_setting: str = "low",
            delimiter_fn: Optional[Callable] = None
    ):
        # file meta-data
        self.imp_path = imp_path
        self.exp_path = exp_path
        self.imp_basename = os.path.basename(self.imp_path)
        self.exp_basename = os.path.basename(self.exp_path)
        self.imp_size = os.path.getsize(self.imp_path)
        self.exp_size = None
        self.tokens_compressed = 0

        # compressor settings
        self.buffer = buffer
        self.delimiter_setting = delimiter_setting
        self.delimiter_fn = delimiter_fn
        self.strict_io = False

        #internal state tracking
        self.scan_complete = False
        self.protocol_complete = False
        self.compression_complete = False
        self.protocol_update_complete = False
        self.writing_complete = False
        self.check_complete = False

        #file data
        self.scanned_data = {
            "bit_freqs" : {0: 0, 1: 0},
            "transitions" : 0,
            "flip_flops" : 0
        }
        self.delimiter_bit = None
        self.protocol_header = None
        self.bit_stuffing = False
        self.padding = None
        self.end_bits = None

        if self.delimiter_fn == None:
            self.delimiter_fn = self.config_delimiter


    def __repr__(self):
        return_string = f"<BPRESS COMPRESSION OBJECT>\n\n<Internal State Data:>\nScanned Data: {self.scanned_data}\nSelected Delimiter: {self.delimiter_bit}\nProtocol header: {self.protocol_header.to01()}\nBit stuffing: {bool(self.bit_stuffing)}\nPadding tail: {self.padding}\n\n<metadata>\n" #type: ignore
        return return_string


    def __enter__(self):
        #exit empty file
        if self.imp_size <= 0:
            return
        
        #create descriptors, data endpoint      
        self.file_in = os.open(self.imp_path, os.O_RDONLY)
        if os.path.exists(self.exp_path):
            self.file_out = os.open(self.exp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        else:
            self.file_out = os.open(self.exp_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

        self.bytes_read_pass_one = 0
        self.bytes_read_pass_two = 0
        self.bytes_compressed = 0
        self.raw_carryover = bitarray()
        self.comp_carryover = bitarray()

        #first read through file
        self.scan_stream()

        #verify that scanning process has properly terminated
        if not self.scan_complete:
            raise RuntimeError("An error occured during scanning")

        #delimite decision is made
        self.delimiter_bit = self.delimiter_fn(self.scanned_data, mode = self.delimiter_setting) #type: ignore
        
        #reset position in file descriptor
        os.lseek(self.file_in, 0, os.SEEK_SET)

        #Outer -> buffer/write loop
        while True:
            #generate bitarray stream
            buffer = os.read(self.file_in, self.buffer)
            self.bytes_read_pass_two += len(buffer)
            stream: bitarray = bitarray()
            stream.frombytes(buffer)
 
            #check if we have exhausted the file
            """
            note:
                end of file logic:

                check raw carryover: if there are raw bits carried over and the buffer is empty
                file must have been size n * buffer. this means we expected more stream but hit the end -> must perform 
                bit stuffing logic here. check if a bit has been stuffed already as an extra precaution and raise error
                if it seems like a second stuffing is occuring

                once bit stuffing logic is complete: either compress remainder or move to tail generation

                generate tail as needed and append to comp carryover

                proceed to writing and exiting loop.
            """
            if not buffer:
                
                # perfect edge
                if not self.raw_carryover and not self.comp_carryover:
                    break

                # check for edge case where file length is a multiple of buffer size and handle bit stuffing
                if self.raw_carryover:
                    if self.bit_stuffing:
                        raise ValueError("Delimiter stuffing occured before end of compression")
                    
                    if self.raw_carryover[-1] != self.delimiter_bit:
                        self.raw_carryover.append(self.delimiter_bit)
                        self.bit_stuffing = True
                    
                    while True:
                        if not self.raw_carryover:
                            break
                        token_length, self.raw_carryover = self.pull_token(self.raw_carryover, self.delimiter_bit)
                        self.comp_carryover.extend(self.compress_token(token_length))
                        
                # byte align compressed carryover before writing
                padding_length = len(self.comp_carryover)%8

                if padding_length > 0:
                    anti_delimiter = self.delimiter_bit ^ 1
                    padding_bits = bitarray([anti_delimiter] * (8 - padding_length))
                    self.comp_carryover.extend(padding_bits)
                    self.padding = padding_bits.to01()

                os.write(self.file_out, self.comp_carryover.tobytes())
                self.compression_complete = True
                break
   

            #make bit stuffing decision
            """
            if we didnt exit on an empty buffer, check buffer size for potential EOF signal.
            if buffer size is less than planned, we have loaded the final file
            """
            if len(buffer) < self.buffer:
                if stream[-1] != self.delimiter_bit:
                    stream.append(self.delimiter_bit)
                    self.bit_stuffing = True
    

            #initialize both raw and compressed streams
            if self.raw_carryover:
                stream = self.raw_carryover + stream
                self.raw_carryover = bitarray()

            compressed_stream: bitarray = self.comp_carryover if self.comp_carryover else bitarray()

            #generate & write preamble and delimiter on first pass
            if not self.protocol_complete:
                if self.delimiter_bit not in stream:
                    raise ValueError("Delimiter was not found in file")
                
                #write magic byte and tail padding placeholder:
                protocol_header: bitarray = bitarray("0110001000000000")
                protocol_header.append(self.delimiter_bit)

                #add preamble
                delim_index = stream.index(self.delimiter_bit)
                protocol_header.extend(stream[:delim_index + 1])
                stream = stream[delim_index + 1:]
                
                #queue protocol for writing
                compressed_stream.extend(protocol_header)
                self.protocol_header = protocol_header #leaving it as a bitarray for now
                self.protocol_complete = True
                

            #strip end bits off raw input stream
            if not self.bit_stuffing:
                if stream[-1] == self.delimiter_bit:
                    pass
                else:
                    for i in range(len(stream) - 2, -1, -1):
                        if stream[i] == self.delimiter_bit:
                            self.raw_carryover = stream[i+1:]
                            stream = stream[:i+1]
                            break

            #inner loop: pull token, compress, reassign raw bit stream
            while True:
                if not stream:
                    self.bytes_compressed += len(buffer)
                    break
                token_length, stream = self.pull_token(stream, self.delimiter_bit)
                comp_token: bitarray = self.compress_token(token_length)
                compressed_stream.extend(comp_token)

            #byte align compressed stream before completing I/O phase
            self.comp_carryover = compressed_stream[len(compressed_stream) - len(compressed_stream)%8:]
            compressed_stream = compressed_stream[:len(compressed_stream) - len(compressed_stream)%8]

            # write the compressed segment to the file
            os.write(self.file_out, compressed_stream.tobytes())
        
        # create padding flag
        if self.padding is not None:
            padding_flag = bitarray([self.bit_stuffing, 0, 0, 0, 0]) + (bitarray(format(len(self.padding), "03b")))
        else:
            padding_flag = bitarray([self.bit_stuffing, 0, 0, 0, 0, 0, 0, 0])

        #update metadata
        if self.protocol_header is not None:
            self.protocol_header = self.protocol_header[:8] + padding_flag + self.protocol_header[16:]
        self.protocol_update_complete = True

        #write padding flag to file
        patch_padding = os.open(self.exp_path, os.O_WRONLY)
        os.lseek(patch_padding, 1, os.SEEK_SET)
        os.write(patch_padding, padding_flag.tobytes())
        os.close(patch_padding)
        self.writing_complete = True

        #update export size metadata:
        self.exp_size = os.path.getsize(self.exp_path)

        # lightweight error checking
        if self.bytes_read_pass_one != self.bytes_read_pass_two:
            raise RuntimeError("read sizes did not match across reads")
        if self.bytes_read_pass_two != self.bytes_compressed:
            raise RuntimeError("data compressed did not match data read")
        if self.protocol_header is not None:
            if len(self.protocol_header) < 18:
                raise RuntimeError("protocol header was too short")
            if self.protocol_header[16] != self.delimiter_bit:
                raise RuntimeError("protcol header contains wrong delimiter")
            if self.protocol_header[8] != self.bit_stuffing:
                raise RuntimeError("bit sutffing failed")
        if self.padding and self.padding[-1] == self.delimiter_bit:
            raise RuntimeError("padding does not match protocol expectations")
        
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.close(self.file_in) #type: ignore
        os.close(self.file_out) #type: ignore












