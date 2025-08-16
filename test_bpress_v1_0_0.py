from bpress_v1_0_0 import BPRESS
from bitarray import bitarray # type: ignore 

bp = BPRESS()

#test data & helpers
test_data = [bitarray("10000000"), bitarray("10101010101001"), bitarray("0"), bitarray()]
test_data_2 ={"zero_lead": 5, "one_lead": 10}
def alt_delim(data):
    return 0



# unit tests for statistics gathering functions in BPRESS parent class:

def test_count_bits():
    assert bp.count_bits(test_data[0]) == [7,1]
    assert bp.count_bits(test_data[1]) == [7,7]
    assert bp.count_bits(test_data[2]) == [1,0]
    assert bp.count_bits(test_data[3]) == [0,0]   

def test_count_transitions():
    assert bp.count_transitions(test_data[0]) == 1
    assert bp.count_transitions(test_data[1]) == 12
    assert bp.count_transitions(test_data[2]) == 0
    assert bp.count_transitions(test_data[3]) == 0

def test_count_flip_flops():
    assert bp.count_flip_flops(test_data[0]) == 0
    assert bp.count_flip_flops(test_data[1]) == 10
    assert bp.count_flip_flops(test_data[2]) == 0
    assert bp.count_flip_flops(test_data[0]) == 0

def test_delimiter():
    assert bp.config_delimiter({"bit_freqs" : {0: 17, 1:20}}) == 0
    assert bp.config_delimiter({"bit_freqs" : {0: 1, 1: 0}}) == 1
    assert bp.config_delimiter({"bit_freqs" : {0: 0, 1: 0}}) == 0
    assert bp.config_delimiter({"bit_freqs" : {0: 10, 1:20}}, mode = "high") == 1
    assert bp.config_delimiter(None, mode = "custom", behaviour = alt_delim) == 0

