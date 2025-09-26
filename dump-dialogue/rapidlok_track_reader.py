from collections import OrderedDict
from disk_entities import Track

SECTOR_HEADER_SIZE = 7
SECTOR_GAP_SIZE = 14
PAYLOAD_FIRST_BYTE_SIZE = 1
CHECKSUM_SIZE = 4
BYTES_PER_TRIPLE = 3
UNPACKED_TRIPLES_PER_SECTOR = 0xC2  # 194
PACKED_PAIRS_COUNT = 0x30  # used in unpack_data
SECTORS_COUNT_FOR_TRACKS_BELOW_19 = 11
SECTORS_COUNT_FOR_TRACKS_19_AND_ABOVE = 10


class RapidlokTrackReader:
    def __init__(self, track_number, data):
        self.track_data = data
        self.track_number = track_number
        self.total_sectors = self.compute_total_sectors(self.track_number)
        self.decoded_sectors = self.read_track()

    def get_track(self) -> Track:
        return Track(self.track_number, self.decoded_sectors, self.track_data)

    def read_track(self):
        sector_starts = self.find_sector_start_positions()
        sector_positions = self.build_ordered_dict_by_positions(sector_starts)
        raw_sectors = self.split_into_raw_sectors(sector_positions)
        return self.decode_sectors(raw_sectors)

    def split_into_raw_sectors(self, sector_positions):
        raw_sector_data: dict[int, list[int]] = {}
        positions = list(sector_positions.items())
        for i, (start_pos, sector_num) in enumerate(positions):
            end_pos = positions[i + 1][0] if i < len(positions) - 1 else len(self.track_data)
            data = self.track_data[start_pos:end_pos]

            # Trim sector header, gap bytes, and first payload byte (always 0x6B)
            pos = SECTOR_HEADER_SIZE
            #Scan for the sequence 0xFF, 0x6B
            while pos < 32 and pos < len(data) - 1:
                if data[pos] == 0xff and data[pos + 1] == 0x6b:
                    break
                pos += 1

            #Some sectors might be unformatted, so if we couldn't find the sequence in the first 32 bytes, skip the sector
            if pos == 32 or pos == len(data):
                continue

            #Skip the 2 bytes of the sequence
            pos += 2

            raw_sector_data[sector_num] = data[pos:]
        return raw_sector_data

    def decode_sectors(self, raw_sectors):
        decoded_sectors: dict[int, list[int]] = {}
        for sector_number, raw_data in raw_sectors.items():
            # Unpack interleaved bytes (0,1,2), (3,4,5), ... into three streams using slicing with step
            total_bytes = UNPACKED_TRIPLES_PER_SECTOR * BYTES_PER_TRIPLE
            chunk = raw_data[:total_bytes]
            unpacked_data_1 = chunk[0::3]
            unpacked_data_2 = chunk[1::3]
            unpacked_data_3 = chunk[2::3]
            processed_data = process_unpacked_data(unpacked_data_1, unpacked_data_2, unpacked_data_3)
            # Remove the last bytes used for checksum
            decoded_sectors[sector_number] = processed_data[:-CHECKSUM_SIZE]
        return decoded_sectors

    def find_sector_start_positions(self) -> dict[int, int]:
        sector_starts: dict[int, int] = {}
        for i in range(self.total_sectors + 1):
            sector_starts[i] = self.find_sector_start(i)
        return sector_starts

    def find_sector_start(self, sector_number: int) -> int:
        header = self.create_header_for_sector(sector_number)
        return self.find_sequence(self.track_data, header)

    @staticmethod
    def build_ordered_dict_by_positions(sector_starts):
        sector_positions = {v: k for k, v in sector_starts.items()}
        return OrderedDict(sorted(sector_positions.items(), key=lambda x: x[0]))

    @staticmethod
    def compute_total_sectors(track_number) -> int:
        return SECTORS_COUNT_FOR_TRACKS_BELOW_19 if track_number < 19 else SECTORS_COUNT_FOR_TRACKS_19_AND_ABOVE

    @staticmethod
    def find_sequence(data: list[int], sequence: list[int]) -> int:
        if len(sequence) > len(data):
            return -1
        for i in range(len(data) - len(sequence) + 1):
            if all(data[i + j] == sequence[j] for j in range(len(sequence))):
                return i
        return -1

    def create_header_for_sector(self, sector_number: int) -> list[int]:
        h1, h2, h3 = create_bitstream(self.track_number, sector_number)
        h4, h5, h6 = create_bitstream(self.track_number ^ sector_number ^ 0x96, 0x96)
        return [0x75, h1, h2, h3, h4, h5, h6]

    def sector_payload_offset(self) -> int:
        return SECTOR_HEADER_SIZE + SECTOR_GAP_SIZE

def create_bitstream(a, x):
    low_a, hi_a = get_nibbles(a)
    low_x, hi_x = get_nibbles(x)

    bitmasks_4_to_6 = [0x24, 0x25, 0x26, 0x27, 0x2c, 0x2d, 0x2e, 0x2f, 0x34, 0x35, 0x36, 0x37, 0x3c, 0x3d, 0x3a, 0x3b]
    mask = (bitmasks_4_to_6[hi_x] << 18) | (bitmasks_4_to_6[low_x] << 12) | (bitmasks_4_to_6[hi_a] << 6) | bitmasks_4_to_6[low_a]
    return (mask & 0xFF0000) >> 16, (mask & 0xFF00) >> 8, mask & 0xFF

def unpack_data(packed_data):
    unpacked_data_1 = []
    unpacked_data_2 = []
    unpacked_data_3 = []
    for i in range(0, PACKED_PAIRS_COUNT):
        x = packed_data[i * 2]
        a = packed_data[i * 2 + 1]
        bitstream_1, bitstream_2, bitstream_3 = create_bitstream(a, x)
        unpacked_data_1.append(bitstream_1)
        unpacked_data_2.append(bitstream_2)
        unpacked_data_3.append(bitstream_3)
    return unpacked_data_1, unpacked_data_2, unpacked_data_3

def process_unpacked_data(unpacked_data_1, unpacked_data_2, unpacked_data_3):
    result = []
    for i in range(len(unpacked_data_1)):
        # Concatenate 24 bits from three bytes
        value = (unpacked_data_1[i] << 16) | (unpacked_data_2[i] << 8) | unpacked_data_3[i]
        # Process bits in groups of 3, keeping only 2nd and 3rd bits
        output = 0
        for bit_pos in range(23, -1, -3):  # Start from MSB
            if bit_pos >= 2:  # Ensure we have 3 bits to process
                three_bits = (value >> (bit_pos - 2)) & 0x7
                two_bits = three_bits & 0x3  # Keep only the last 2 bits
                output = (output << 2) | two_bits
        output ^= 0xffff
        result.append((output & 0xFF00) >> 8)
        result.append(output & 0xFF)
    return result

def get_nibbles(n):
    return n & 0x0f, (n & 0xF0) >> 4
