"""Defines a music box instance."""
import re

class MusicBox:
    # MAJOR_SCALE_INTERVALS = [2, 2, 1, 2, 2, 2, 1]
    # NOTE_LABELS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    # DEGREE_OFFSETS = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}

    def __init__(self, **kwargs):
        # TODO: Validate contents
        for (key, value) in kwargs['meta'].items():
            setattr(self, key, value)

        for (key, value) in kwargs['dimensions'].items(): 
            setattr(self, key, value)

        # load notes as (note, octave) tuples
        self.notes = [MusicBox._note_str_to_tuple(note) for note in kwargs['music_props']['notes']]
        # if not self.is_chromatic:
        # if box_dict["music_props"]["starting_degree"] is None:
        # self.start_offset = self.DEGREE_OFFSETS["I"]
        # else:
            # self.start_offset = self.DEGREE_OFFSETS[kwargs["music_props"]["starting_degree"].strip().upper()]
        # else:
        #     self.start_offset = 0
        # self.starting_note = box_dict["music_props"]["starting_note"]
        # self.draw_tonic_as_c = kwargs["music_props"]["draw_tonic_as_c"]  # TODO: Support option
        self.clef = kwargs["music_props"]["clef"]
        # Create scale array
        # note_index = (self.NOTE_LABELS.index(self.tuning) + self.start_offset) % len(self.NOTE_LABELS)
        # scale_index = len(self.MAJOR_SCALE_INTERVALS) - 1
        # octave = kwargs["music_props"]["starting_octave"]
        # for i in range(self.notes_count):
        #     # add current note index
        #     self.notes.append((self.NOTE_LABELS[note_index], octave))
        #     # if self.is_chromatic:
        #     #     current_index = note_index
        #     #     note_index = (note_index + 1) % len(self.NOTE_LABELS)
        #     # else:
        #     current_index = note_index
        #     scale_index = (scale_index + 1) % len(self.MAJOR_SCALE_INTERVALS)
        #     note_index = (note_index + self.MAJOR_SCALE_INTERVALS[scale_index]) % len(self.NOTE_LABELS)
        #     # update octave
        #     if note_index < current_index:
        #         octave += 1
        # TODO: Remove self variables only used on Init, consider later midi parsing

    def __str__(self):
        return "{cls} instance\n" \
               "- Description: {description}\n" \
               "- Manufacturer: {manufacturer}\n" \
               "- Notes count: {notes_count}\n" \
               "- Pin width: {pin_width}\n" \
            .format(cls=self.__class__.__name__,
                    description=self.description,
                    manufacturer=self.manufacturer,
                    notes_count=self.notes_count,
                    pin_width=self.pin_width)

    def get_margins(self):
        return [self.start_margin, self.end_margin]

    def has_note(self, note_str):
        """Checks if a given note is playable in the loaded music box."""
        # note string has to be like [note][octave], for example F#3, bb4
        return self.find_note(note_str) >= 0
        # return any([MusicBox._note_equals(note_str, note) for note in self.notes])

    def find_note(self, note_tuple):
        for index, note in enumerate(self.notes):
            if MusicBox._note_equals(note, note_tuple):
                return index
        return -1

    @staticmethod
    def _note_equals(a, b):
        """Compares notes (tuples or strings). Case insensitive, considers enharmonics."""
        enharmonics = [
            sorted(('c#', 'db')),
            sorted(('d#', 'eb')),
            sorted(('f#', 'gb')),
            sorted(('g#', 'ab')),
            sorted(('a#', 'bb')),
        ]

        na = a if type(a) is not tuple else MusicBox._note_tuple_to_str(a)
        nb = b if type(b) is not tuple else MusicBox._note_tuple_to_str(b)

        na = na.lower().strip()
        nb = nb.lower().strip()
        a_parts = MusicBox._note_str_to_tuple(na)
        b_parts = MusicBox._note_str_to_tuple(nb)
        return a_parts[1] == b_parts[1] and \
            (a_parts[0] == b_parts[0] or sorted((a_parts[0], b_parts[0])) in enharmonics)

    @staticmethod
    def _note_str_to_tuple(note_str):
        """Takes note string and returns a tuple with note name + octave."""
        return (re.sub('\d', '', note_str), int(re.sub('[^\d]', '', note_str)))

    @staticmethod
    def _note_tuple_to_str(note_tuple):
        return f"{note_tuple[0]}{note_tuple[1]}"

    @property
    def notes_count(self):
        return len(self.notes)