from common_helpers import *
from disk_entities import TrackId
from gcr_track_reader import GCRTrackReader


class G64:
    TRACK_SIZE_HEADER = 2
    START_POSITION = 12
    OFFSET_SIZE = 4

    def __init__(self, filename):
        with open(filename, "rb") as file:
            self.data = file.read()

        self.filename = filename
        self.validate_signature()
        self.number_of_tracks = self.data[9]
        self.track_size = self.read_word(10)
        self.read_track_offsets()
        self.read_tracks()

    def __getitem__(self, key):
        return self.tracks[key]

    def __repr__(self):
        s = "G64 " + self.filename + " - Number of tracks: " + str(self.number_of_tracks)
        s += " - Track size: " + str(self.track_size)

        s += "\nTrack offsets:"
        for key, value in self.track_offsets.items():
            if value:
                s += "\nTrack " + str(key) + ": " + hex_str_16(value)

        for track_id, track in self.tracks.items():
            s += "\nTrack " + str(track_id) + ":\n"
            s += repr_hex_bytes(track)
        return s

    def read_word(self, i):
        return self.data[i] + (self.data[i+1] << 8)

    def read_dword(self, i):
        return self.data[i] + (self.data[i+1] << 8) + (self.data[i+2] << 16) + (self.data[i+3] << 24)

    def read_tracks(self):

        self.tracks = {}
        track_id = TrackId.first()

        for i in range(0, self.number_of_tracks):
            track_start = self.track_offsets[track_id]
            track_end = track_start + self.track_size + self.TRACK_SIZE_HEADER

            if track_start != 0:
                self.tracks[track_id] = self.data[track_start:track_end]

            if track_id.is_last():
                break
            track_id = track_id.next()

    def decode_tracks_as_gcr(self):
        reader = GCRTrackReader()

        track_id = TrackId.first()

        for i in range(0, self.number_of_tracks):
            self.tracks[track_id] = reader.read_track(track_id.track_number, self.tracks[track_id])

            if track_id.is_last():
                break
            track_id = track_id.next()

    def read_track_offsets(self):

        self.track_offsets = {}
        track_id = TrackId.first()

        for i in range(0, self.number_of_tracks):
            offset_position = self.START_POSITION + i * self.OFFSET_SIZE
            self.track_offsets[track_id] = self.read_dword(offset_position)

            if track_id.is_last():
                break
            track_id = track_id.next()


    def validate_signature(self):
        signature = self.data[0:8]
        if signature != b'GCR-1541':
            raise Exception("GCR signature not found")

