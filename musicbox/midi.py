import midi


class Parser:
    @staticmethod
    def fit_to_tuning(midi_object, tuning):
        """ Force chromatism into tuning """
        pass

    @staticmethod
    def fit_octaves(midi_object, start_note, end_note):
        """ Force notes on extreme octaves to be inside a range (inclusive) """
        pass

    @staticmethod
    def round_beats(midi_object, min_delay):
        """ Clump/summarize notes that repeat too fast """
        pass

    @staticmethod
    def merge_channels(midi_object):
        """ merges all channels into one """
        pass

    @staticmethod
    def pitch_to_note(midi_pitch_code):
        return "C C# D D# E F F# G G# A A# B".split(" ")[midi_pitch_code % 12], -1 + int(midi_pitch_code / 12)

    @staticmethod
    def note_to_pitch(note, octave):
        return 12 * (octave + 1) + "C C# D D# E F F# G G# A A# B".split(" ").index(note)

    @staticmethod
    def render_to_box(midi_object):
        """
        Parses and generates a music-box-compatible structure

        Parameters
        ----------
        midi_object: midi.Pattern

        Returns
        -------
        dict

        """
        midi_object.make_ticks_abs()
        resolution = midi_object.resolution
        rendered = list()
        for track in midi_object:
            for event in track:
                if isinstance(event, midi.NoteOnEvent) and event.get_velocity() > 0:
                    note, octave = Parser.pitch_to_note(event.get_pitch())
                    rendered.append({
                        "note": note,
                        "octave": octave,
                        "beat": event.tick / resolution * 2,
                        "raw_pitch": event.get_pitch()
                    })
        rendered = sorted(rendered, key=lambda k: k["beat"])
        return rendered