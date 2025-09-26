from dataclasses import dataclass

from common_helpers import *
from gcr_decoder import GCRDecoder


class SectorHeader:
    def __init__(self, data):
        self.data = data
        self.parse_header()

    def parse_header(self):
        header_bytes = self.decode_header(self.data)
        attributes = [
            "block_id",
            "block_checksum",
            "sector",
            "track",
            "format_id_2",
            "format_id_1"
            ]

        for i in range(0, len(attributes)):
            setattr(self, attributes[i], header_bytes[i])

        self.format_id = chr(self.format_id_1) + chr(self.format_id_2)

    def decode_header(self, header_info):
        return GCRDecoder.decode_gcr_bytes(header_info)

    def __repr__(self):
        s = "Track " + str(self.track)
        s += " Sector " + str(self.sector)
        s += " ID: " + self.format_id
        s += " Checksum: " + hex_str_8(self.block_checksum)
        return s

class Sector:
    def __init__(self, header, data):
        self.header = header
        self.data = data

    def __repr__(self):
        s = "Sector - "
        s += str(self.header)
        s += "\n" + repr_hex_bytes(self.data)
        return s

class Track:
    def __init__(self, track_number, sectors, raw_data):
        self.track_number = track_number
        self.sectors = sectors
        self.raw_data = raw_data

    def __getitem__(self, key):
        return self.sectors[key]

    def get_total_sectors(self):
        return len(self.sectors)

    def __repr__(self):
        s = "Track " + str(self.track_number) + "\n"
        s += "\n" + repr_hex_bytes(self.raw_data) + "\n"

        for sector_id, sector in self.sectors.items():
            s += "\nSector " + str(sector_id) + "\n"
            s += str(sector)
        return s

@dataclass
class DiskLocation:
    side: int
    track: int
    sector: int

    def __init__(self, side, track, sector, offset = 0):
        self.side = side
        self.track = track
        self.sector = sector
        self.offset = offset

    def move_to_next_sector(self):
        if self.sector == get_sectors_per_track(self.track):
            self.sector = 0
            self.track += 1
        else:
            self.sector += 1

    def add_sector_index(self, index):
        while index > 0:
            #print(str(self))
            self.move_to_next_sector()
            index -= 1

    def __repr__(self):
        return "Side " + str(self.side) + " T/S " + str(self.track) + "/" + str(self.sector) + " offset " + str(self.offset)

def get_sectors_per_track(track):
    if track >= 31:
        return 16
    elif track <= 17:
        return 20
    elif track <= 24:
        return 18
    else:
        return 17


class GameDisks:
    def __init__(self, side_1, side_2):
        self.disk_sides = []
        self.disk_sides.append(side_1)
        self.disk_sides.append(side_2)

    def __getitem__(self, key):
        return self.disk_sides[key]

    def get_sector(self, disk_location):
        track_id = TrackId(str(disk_location.track) + ".0")
        return self.disk_sides[disk_location.side - 1][track_id][disk_location.sector]

class TrackId:
    @staticmethod
    def first():
        return TrackId("1.0")

    def __init__(self, track_id):
        track_id_parts = track_id.split(".")
        self.track_number = int(track_id_parts[0])
        self.half_track = track_id_parts[1]

        if self.track_number not in range(1, 43):
            raise Exception("Invalid track number %d" % self.track_number)

        if self.half_track not in ("0", "5"):
            raise Exception("Invalid half track %s" % self.half_track)

    def next(self):
        if self.half_track == "5":
            new_id = str(self.track_number + 1) + ".0"
        else:
            new_id = str(self.track_number) + ".5"
        return TrackId(new_id)

    def is_last(self):
        return self.track_number == 42 and self.half_track == "5"

    def __repr__(self):
        return str(self.track_number) + "." + self.half_track

    def __hash__(self):
        return hash((self.track_number, self.half_track))

    def __eq__(self, other):
        if not isinstance(other, TrackId):
            return NotImplemented
        return self.track_number == other.track_number and self.half_track == other.half_track

