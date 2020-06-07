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
        self.notes = [(re.sub('\d', '', note), int(re.sub('[^\d]', '', note))) for note in kwargs['music_props']['notes']]
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

    @property
    def notes_count(self):
        return len(self.notes)