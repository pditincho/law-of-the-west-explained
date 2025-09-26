from disk_entities import Sector, SectorHeader, Track, get_sectors_per_track
from gcr_decoder import GCRDecoder


class GCRTrackReader:
    HEADER_INFO_SIZE = 10
    GCR_PAYLOAD_SIZE = 325

    def __init__(self):
        pass

    def read_track(self, track_number, data):
        self.data = data
        self.actual_size = self.read_track_actual_size()
        #Remove header after reading it (track size)
        data = data[2:]
        self.bit_position = 0
        return Track(track_number, self.get_sectors(track_number), data)

    def read_track_actual_size(self):
        return self.read_word(0)

    def read_word(self, i):
        return self.data[i] + (self.data[i+1] << 8)

    def get_sectors(self, track_number):
        track_sectors = {}
        sector_count = 0
        while sector_count < get_sectors_per_track(track_number) + 1:
            sector = self.read_sector()
            if not sector:
                #print("could not find sector header for track %d sector %d" % (track_number, sector_count))
                pass
            track_sectors[sector_count] = sector
            sector_count += 1
        return track_sectors

    def read_sector(self):
        try:
            self.find_sync_end()
            header_info = self.get_header_info_2()
            header = SectorHeader(header_info)
            self.find_sync_end()
        except:
            return None
        gcr_data = self.get_gcr_sector_data()
        sector_data = self.decode_sector_data(gcr_data)
        sector = Sector(header, sector_data)
        return sector

    def find_sync_end(self):
        run_count = 0
        run_observed = False
        minimum_count = 10

        while True:
            bit = self.get_next_bit()
            if bit == 1:
                run_count += 1
            else:
                if run_observed:
                    self.bit_position -= 1
                    return
                else:
                    run_count = 0

            if run_count == minimum_count:
                run_observed = True

    def get_header_info_2(self):
        return self.get_bytes(self.HEADER_INFO_SIZE)

    def get_gcr_sector_data(self):
        return self.get_bytes(self.GCR_PAYLOAD_SIZE)

    def get_next_bit(self):
        byte_position = self.bit_position >> 3
        bit_index = 7 - (self.bit_position % 8)
        bitmask = 1 << bit_index
        byte = self.data[byte_position]
        self.bit_position += 1
        return (byte & bitmask) >> bit_index

    def get_byte(self):
        byte = 0
        for i in range(0, 8):
            byte <<= 1
            bit = self.get_next_bit()
            byte |= bit
        return byte

    def get_bytes(self, length):
        _bytes = []
        for i in range(0, length):
            _bytes.append(self.get_byte())
        return _bytes

    def decode_sector_data(self, sector_data):
        decoded_bytes = GCRDecoder.decode_gcr_bytes(sector_data)
        block_id = decoded_bytes[0]
        payload = decoded_bytes[1:257]
        checksum = decoded_bytes[257]
        return payload

