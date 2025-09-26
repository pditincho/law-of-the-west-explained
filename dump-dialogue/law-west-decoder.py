from collections.abc import Iterable, Sequence

from disk_entities import TrackId
from g64 import G64
from rapidlok_track_reader import RapidlokTrackReader
from scene_location import SceneLocation

WOMAN_SCENES = (2, 7, 10)

DOCTOR_SCENE = 4

# Define the alphabet mapping as a constant
ALPHABET: str = " ABCDEFGHIJKLMNOPQRSTUVWXYZ!',.?"
BYTES_PER_LINE: int = 25
LOAD_ADDRESS_SIZE: int = 2
SIDE1_SCENES = {"1", "2", "3", "4"}


def decode_packed_5bit_text(data: Iterable[int]) -> str:
    """Decode a sequence of bytes into text using the 5-bit packing scheme."""
    bitstream = 0
    bitlen = 0
    result: list[str] = []
    for b in data:
        # Add byte to bit buffer
        bitstream = (bitstream << 8) | b
        bitlen += 8
        # Extract as many 5-bit symbols as possible
        while bitlen >= 5:
            bitlen -= 5
            symbol = (bitstream >> bitlen) & 0b11111
            result.append(ALPHABET[symbol])
    return "".join(result)


def decode_chunks(data: Sequence[int], chunk_size: int = BYTES_PER_LINE) -> list[str]:
    """Decode in fixed input-byte chunks (default BYTES_PER_LINE)."""
    chunks: list[str] = []
    for j in range(0, len(data), chunk_size):
        block = data[j: j + chunk_size]
        if not block:
            break
        chunks.append(decode_packed_5bit_text(block))
    return chunks


def decode_text_area(data: Sequence[int], start_offset: int, total_lines: int) -> list[str]:
    total_size = total_lines * BYTES_PER_LINE
    end_offset = start_offset + total_size
    sliced = data[start_offset:end_offset]
    return decode_chunks(sliced, BYTES_PER_LINE)


def read_tracks_for_side(side_g64: G64, excluded_tracks):
    """Read all tracks for a side, skipping excluded track numbers (1..35)."""
    side_tracks = {}
    excluded = set(excluded_tracks)
    for track_num in range(1, 36):
        if track_num in excluded:
            continue
        track_id = TrackId(f"{track_num}.0")
        reader = RapidlokTrackReader(track_num, side_g64.tracks[track_id])
        side_tracks[track_num] = reader.get_track()
    return side_tracks


def read_scenes(_scene_locations, side1_tracks, side2_tracks):
    all_scenes_data: dict[str, list[int]] = {}
    for scene_id, loc in _scene_locations.items():
        track = loc.start_track
        sector = loc.start_sector
        scene_data: list[int] = []
        while True:
            side = _get_side_for_scene(scene_id, side1_tracks, side2_tracks)
            scene_data.extend(side[track][sector])
            if track == loc.end_track and sector == loc.end_sector:
                break
            if sector == RapidlokTrackReader.compute_total_sectors(track):
                track += 1
                sector = 0
            else:
                sector += 1
            if track == 36:
                track = 1
        # Skip the first 2 bytes (the load address) - which is always $9F7F
        all_scenes_data[scene_id] = scene_data[LOAD_ADDRESS_SIZE:]
    return all_scenes_data


def print_dialogue(base_line, _lines):
    character_line = _lines[base_line]
    sheriff_lines = _lines[base_line + 1: base_line + 5]
    print(f"C: {character_line}\n")
    for line in sheriff_lines:
        print(f"S: {line}")

def get_sheriff_lines_for(character_line: int) -> list[int]:
    return list(range(character_line + 1, character_line + 5))


def get_char_line_for_sheriff_line_tier1(sheriff_line: int) -> int:
    return sheriff_line * 5


def get_char_line_for_sheriff_line_tier2(sheriff_line: int) -> int:
    b = ((sheriff_line // 5) - 1) * 4
    c = b + (sheriff_line % 5) - 1
    return c * 5 + 25


def get_char_line_for_sheriff_line_tier3(sheriff_line: int) -> int:
    b = ((sheriff_line // 5) - 5) * 4
    return b + (sheriff_line % 5) + 105 - 1


def get_authority_for_final_line_woman(outcome: int) -> int:
    authority = [0, 0, 0, 0, 6, 6, 6, 6]
    return authority[outcome // 32]

def get_authority_for_final_line_man(outcome: int) -> int:
    return outcome // 32

def get_romance_for_final_line(outcome: int) -> int:
    romance = [0, 1, 2, 3, 0, 1, 2, 3]
    return romance[outcome // 32]

def get_doctor_state_for_final_line(outcome: int):
    doctor_state = [0, 0, 1, 2, 0, 0, 0, 3]
    state_descriptions = {0 : "out of town", 1 : "drunk", 2 : "hostile", 3 : "friendly"}
    state = doctor_state[outcome // 32]
    return state_descriptions[state]

def get_character_state_from_outcome(outcome: int):
    states = {
    #Commented states will not happen as an immediate outcome of the dialogue but are included for completeness
    #0 :	"Standing still (waiting for dialogue)",
    1 :	"Draw gun - Slow (delay of 5)",
    2 :	"Leave right but draw gun if sheriff draws",
    3 :	"Walk away then leave right",
    4 :	"Surrender", #Not sure about the real difference between 4 and 5
    5 :	"Surrender",
    6 :	"Leave right but surrender if sheriff draws",
    7 :	"Gang shootout",
    8 :	"Walk right, then away (and then leave right)",    #This state will always transition to state #03
    9 :	"Draw gun - Fast (delay of 2)",
    #10 :	"Entering scene and walking towards center of street",
    #11 : 	"Entering scene and walking towards center of street",
    #12 :	"Running around and shooting",
    #13 :	"Falling down after being shot",
    #14 :	"Shooting",
    15 :	"Walk away then leaving left",
    #16 :	"Walking toward sheriff before starting a conversation",
    #17 :	"Walking away then leaving right",
    18 :	"Leave, about to shoot from the street",
    19 :	"Draw gun - Very Fast (delay of 1)",
    #20 :	"Preparing to shoot from scene's edge",
    21 :	"Leave and shoot on exit",
    #22 :	"Talking"
    }

    return states[outcome & 0x1F]


def print_dialogue_tree(_lines: Sequence[str], scene_number: int):
    char_1 = [0]
    for c1 in char_1:
        sheriff_1 = get_sheriff_lines_for(c1)
        for s1 in sheriff_1:
            c2 = get_char_line_for_sheriff_line_tier1(s1)
            sheriff_2 = get_sheriff_lines_for(c2)
            for s2 in sheriff_2:
                c3 = get_char_line_for_sheriff_line_tier2(s2)
                sheriff_3 = get_sheriff_lines_for(c3)
                for s3 in sheriff_3:
                    c4 = get_char_line_for_sheriff_line_tier3(s3)
                    print(f"      NPC: {_lines[c1]}")
                    print(f"  Sheriff: {_lines[s1]}")
                    print(f"      NPC: {_lines[c2]}")
                    print(f"  Sheriff: {_lines[s2]}")
                    print(f"      NPC: {_lines[c3]}")
                    print(f"  Sheriff: {_lines[s3]}")
                    print(f"      NPC: {_lines[c4]}")
                    selections = [s1 - c1, s2 - c2, s3 - c3]
                    outcome = get_outcome_from_selections(scene_number, selections)
                    print_outcomes(outcome, scene_number)

                    print("\n")


def get_outcome_from_selections(scene_number: int, selections: list[int]) -> int:
    sheriff_line_index = selections[0] * 16 + selections[1] * 4 + selections[2]
    offset = sheriff_line_index - 0x15
    outcome = scenes_data[str(scene_number)][offset]
    return outcome


def print_outcomes(outcome: int, scene_number: int):
    if scene_number in WOMAN_SCENES:
        print(f"Authority: {get_authority_for_final_line_woman(outcome)}")
        print(f"Romance: {get_romance_for_final_line(outcome)}")
    else:
        print(f"Authority: {get_authority_for_final_line_man(outcome)}")
        if scene_number == DOCTOR_SCENE:
            print(f"Doctor state: {get_doctor_state_for_final_line(outcome)}")
    print(f"NPC State: {get_character_state_from_outcome(outcome)}")


def _get_side_for_scene(scene_id: str, side1_tracks, side2_tracks):
    return side1_tracks if scene_id in SIDE1_SCENES else side2_tracks


if __name__ == "__main__":
    side_1 = G64("side1.g64")
    side_2 = G64("side2.g64")

    side_1_tracks = read_tracks_for_side(side_1, excluded_tracks=[1, 17, 18])
    side_2_tracks = read_tracks_for_side(side_2, excluded_tracks=range(9, 22))

    scene_locations = {
        "1": SceneLocation(2, 1, 4, 10),
        "2": SceneLocation(7, 9, 10, 6),
        "3": SceneLocation(4, 11, 7, 8),
        "4": SceneLocation(13, 5, 16, 2),
        "5": SceneLocation(28, 5, 31, 5),
        "6": SceneLocation(22, 3, 25, 3),
        "7": SceneLocation(25, 4, 28, 4),
        "8": SceneLocation(31, 6, 34, 6),
        "9": SceneLocation(34, 7, 2, 6),
        "10": SceneLocation(2, 7, 5, 4),
        "11": SceneLocation(5, 5, 8, 2),
    }

    scenes_data = read_scenes(scene_locations, side_1_tracks, side_2_tracks)
    for k, v in scenes_data.items():
        print(f"{'=' * 20} Scene {k} {'=' * 20}")
        lines = decode_text_area(v, 0x140, 169)
        print_dialogue_tree(lines, int(k))
