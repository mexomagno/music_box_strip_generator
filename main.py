# coding=utf-8

"""
Contains all the logic to generate the paper strips
"""
import os
import argparse
import yaml
from fpdf import FPDF
import midi
from pprint import pprint


class _MidiParser:
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
                    note, octave = _MidiParser.pitch_to_note(event.get_pitch())
                    rendered.append({
                        "note": note,
                        "octave": octave,
                        "beat": event.tick / resolution * 2,
                        "raw_pitch": event.get_pitch()
                    })
        rendered = sorted(rendered, key=lambda k: k["beat"])
        return rendered


class MusicBox:
    MAJOR_SCALE_INTERVALS = [2, 2, 1, 2, 2, 2, 1]
    NOTE_LABELS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    DEGREE_OFFSETS = {"I": 0, "II": 1, "III": 2, "IV": 3, "V": 4, "VI": 5, "VII": 6}

    def __init__(self, box_dict):
        # TODO: Validate contents
        self.manufacturer = box_dict["meta"]["manufacturer"]
        self.description = box_dict["meta"]["description"]
        self.notes_count = box_dict["dimensions"]["notes_count"]
        self.pin_width = box_dict["dimensions"]["pin_width"]
        self.start_margin = box_dict["dimensions"]["start_margin"]
        self.end_margin = box_dict["dimensions"]["end_margin"]
        self.hole_radius = box_dict["dimensions"]["hole_radius"]
        self.beat_width = box_dict["dimensions"]["beat_width"]
        self.is_chromatic = box_dict["music_props"]["chromatic"]
        self.tuning = box_dict["music_props"]["tuning"]
        if not self.is_chromatic:
            if box_dict["music_props"]["starting_degree"] is None:
                self.start_offset = self.DEGREE_OFFSETS["I"]
            else:
                self.start_offset = self.DEGREE_OFFSETS[box_dict["music_props"]["starting_degree"].strip().upper()]
        else:
            self.start_offset = 0
        # self.starting_note = box_dict["music_props"]["starting_note"]
        self.draw_tonic_as_c = box_dict["music_props"]["draw_tonic_as_c"]  # TODO: Support option
        self.clef = box_dict["music_props"]["clef"]
        # Create scale array
        self.notes = list()  # List of tuples
        note_index = (self.NOTE_LABELS.index(self.tuning) + self.start_offset) % len(self.NOTE_LABELS)
        scale_index = len(self.MAJOR_SCALE_INTERVALS) - 1
        octave = box_dict["music_props"]["starting_octave"]
        for i in range(self.notes_count):
            # add current note index
            self.notes.append((self.NOTE_LABELS[note_index], octave))
            if self.is_chromatic:
                current_index = note_index
                note_index = (note_index + 1) % len(self.NOTE_LABELS)
            else:
                current_index = note_index
                scale_index = (scale_index + 1) % len(self.MAJOR_SCALE_INTERVALS)
                note_index = (note_index + self.MAJOR_SCALE_INTERVALS[scale_index]) % len(self.NOTE_LABELS)
            # update octave
            if note_index < current_index:
                octave += 1
        # TODO: Remove self variables only used on Init, consider later midi parsing

    def __str__(self):
        return "{cls} instance\n" \
               "- Description: {description}\n" \
               "- Manufacturer: {manufacturer}\n" \
               "- Notes count: {notes_count}\n" \
               "- Pin width: {pin_width}\n" \
               "- Is chromatic?: {is_chromatic}\n" \
               "- Scale: {scale}\n" \
               "- First note offset: {offset}" \
            .format(cls=self.__class__.__name__,
                    description=self.description,
                    manufacturer=self.manufacturer,
                    notes_count=self.notes_count,
                    pin_width=self.pin_width,
                    is_chromatic=self.is_chromatic,
                    scale=self.notes,
                    offset=self.start_offset)

    def get_margins(self):
        return [self.start_margin, self.end_margin]

class MusicBoxPDFGenerator(FPDF):
    """
    Represents a music box document.
    All units in mm except for fonts, which are in points.
    """

    def __init__(self, music_box_object, paper_size=(279.4, 215.9), strip_separation=0):
        """

        Parameters
        ----------
        music_box_object: MusicBox
        paper_size: Size of the paper where the file will be printed to
        strip_separation: Separation between strips in the paper
        """
        super().__init__("p", "mm", paper_size)
        self.set_author("Mexomagno")
        self.set_auto_page_break(True)
        self.set_margins(8, 6, 8)
        self.alias_nb_pages()
        self.set_compression(True)
        self.music_box_object = music_box_object
        self.strip_separation = strip_separation
        self.generated = False

    def generate(self, midi_file, output_file, song_title="NO-TITLE", song_author="NO-AUTHOR"):
        if self.generated:
            raise RuntimeError("Document was already generated!")

        self.set_title("{} - {} ({}x{})".format(song_title, song_author, self.w, self.h))
        # Parse midi file
        parsed_notes = _MidiParser.render_to_box(midi.read_midifile(midi_file))
        pprint(parsed_notes)

        self.add_page()
        strip_generator = StripGenerator(music_box_object=self.music_box_object,
                                         song_title=song_title,
                                         song_author=song_author)
        # Add notes to strip
        current_y = - strip_generator.get_height() / 2 - self.strip_separation + self.t_margin

        drawn_beats = 0
        while len(parsed_notes) > 0:
            # print("> Created new strip")
            new_strip = strip_generator.new_strip(drawn_beats)
            current_y += strip_generator.get_height() + self.strip_separation
            if current_y + strip_generator.get_height() / 2 > self.h - self.b_margin:
                # print("> Had to add page")
                self.add_page()
                current_y = strip_generator.get_height() / 2 + self.t_margin
            parsed_notes, total_strip_beats = new_strip.draw(pdf=self,
                                                             x0=self.l_margin,
                                                             x1=self.w - self.r_margin,
                                                             y=current_y,
                                                             notes=parsed_notes)
            drawn_beats += total_strip_beats
            # print("> Drew a strip")

        self.generated = True
        self.output(output_file, "F")


class StripGenerator:
    def __init__(self, music_box_object, song_title=None, song_author=None):
        """

        Parameters
        ----------
        music_box_object: MusicBox
        song_title
        song_author
        """
        self.music_box_object = music_box_object
        self.song_title = song_title
        self.song_author = song_author
        self.has_header = False

    def new_strip(self, first_beat_position):
        if not self.has_header:
            self.has_header = True
            return Strip(music_box_object=self.music_box_object,
                         header={"song_title": self.song_title,
                                 "song_author": self.song_author})
        else:
            return Strip(self.music_box_object,
                         first_beat=first_beat_position)

    def get_height(self):
        pw = self.music_box_object.pin_width
        nc = self.music_box_object.notes_count
        sm = self.music_box_object.get_margins()
        return pw * (nc - 1) + sum(sm)


class Strip:
    def __init__(self, music_box_object, first_beat=0, header=None):
        """
        Creates a "Strip" representing a paper strip which will contain the notes

        Parameters
        ----------
        music_box_object: MusicBox
        first_beat: int
            Relative position of this strip's first beat
        header: dict
            Dictionary with header elements if present. None otherwise

        """
        self.music_box_object = music_box_object
        self.is_first = header is not None
        self.song_title = header["song_title"] if self.is_first and "song_title" in header else "NO-TITLE"
        self.song_author = header["song_author"] if self.is_first and "song_author" in header else "NO-TITLE"
        self.first_beat = first_beat

    def draw(self, pdf, x0, x1, y, notes):
        """ Draws the strip in the pdf document """
        x_start = x0
        BEAT_WIDTH = self.music_box_object.beat_width

        if self.is_first:
            # Draw strip header
            x_start = self._draw_header(pdf, x_start, y)

        # Draw notes grid
        g_clef_y = self._draw_body(pdf, x_start, x1, y)

        if self.is_first and g_clef_y:
            # draw G clef
            PIN_WIDTH = self.music_box_object.pin_width
            G_CLEF_H = PIN_WIDTH * 15
            pdf.image("res/g_clef.png", x=x_start,
                      y=g_clef_y - G_CLEF_H / 1.8,
                      h=G_CLEF_H)
            x_start += 2 * BEAT_WIDTH

        notes_left = self._draw_notes(pdf, x_start, x1, y, notes)

        total_strip_beats = int((x1 - x_start) / BEAT_WIDTH)
        return notes_left, total_strip_beats

    def _draw_header(self, pdf, x0, y):
        # def show_pointer(s="O"):
        # rotate reference

        pdf.rotate(90, x0, y)
        # Coordinates are the same, but are drawn rotated
        current_y = y
        # draw triangle
        TRIANGLE_SIZE = (8, 8)
        TRIANGLE_MARGIN_T = 4
        pdf.image(name="res/triangle_tiny.png",
                  x=x0 - TRIANGLE_SIZE[0] / 2,
                  y=current_y + TRIANGLE_MARGIN_T,
                  w=TRIANGLE_SIZE[0],
                  h=TRIANGLE_SIZE[1])
        current_y += TRIANGLE_MARGIN_T  # Relative to rotated perspective
        # Write song info:
        STRIP_MARGINS = self.music_box_object.get_margins()
        PIN_WIDTH = self.music_box_object.pin_width
        N_NOTES = self.music_box_object.notes_count
        MAX_TITLE_WIDTH = PIN_WIDTH * N_NOTES + sum(STRIP_MARGINS) - 4
        pdf.set_font("courier", "B", 30)

        while max(pdf.get_string_width(self.song_title), pdf.get_string_width(self.song_author)) > MAX_TITLE_WIDTH:
            pdf.set_font_size(pdf.font_size_pt - 0.1)
        pdf.text(x=x0 - pdf.get_string_width(self.song_title) / 2,
                 y=current_y + TRIANGLE_SIZE[1] + pdf.font_size + 5,
                 txt=self.song_title)
        current_y += TRIANGLE_SIZE[1] + pdf.font_size + 5
        pdf.text(x=x0 - pdf.get_string_width(self.song_author) / 2,
                 y=current_y + pdf.font_size + 3,
                 txt=self.song_author)
        current_y += pdf.font_size + 10

        # draw notes
        x0_first_note = x0 - N_NOTES * PIN_WIDTH / 2
        pdf.set_font("Arial", "B", 8)
        notes = self.music_box_object.notes
        for n in range(N_NOTES):
            symbol = notes[n % len(notes)][0]
            pdf.text(x0_first_note + n * PIN_WIDTH,
                     current_y + pdf.font_size,
                     symbol)
        current_y += pdf.font_size + 1

        # un-rotate
        pdf.rotate(0, y, x0)
        x0_adjusted = x0 + (current_y - y)

        # Draw strip limits
        STRIP_WIDTH = PIN_WIDTH * (N_NOTES - 1) + sum(STRIP_MARGINS)
        x0_strip_angle = x0 + TRIANGLE_SIZE[1] + 5

        # Draw strip borders
        pdf.line(x0_strip_angle, y - STRIP_WIDTH / 2,
                 x0_adjusted, y - STRIP_WIDTH / 2)
        pdf.line(x0_strip_angle, y + STRIP_WIDTH / 2,
                 x0_adjusted, y + STRIP_WIDTH / 2)
        pdf.line(x0, y - 4, x0_strip_angle, y - STRIP_WIDTH / 2)
        pdf.line(x0, y + 4, x0_strip_angle, y + STRIP_WIDTH / 2)
        return x0_adjusted

    def _draw_body(self, pdf, x0, x1, y):
        pdf.set_draw_color(140, 140, 140)
        N_NOTES = self.music_box_object.notes_count
        PIN_WIDTH = self.music_box_object.pin_width
        STRIP_WIDTH = N_NOTES * PIN_WIDTH
        BEAT_WIDTH = self.music_box_object.beat_width
        G_CLEF_NOTES = "EGBDF"
        G_CLEF_Y = None
        do_g_clef = False  #all([x in self.note_symbols for x in G_CLEF_NOTES])
        clef_offset = 0  #len(self.note_symbols) - (N_NOTES % len(self.note_symbols))
        for h_line in range(N_NOTES):
            # if do_g_clef and len(G_CLEF_NOTES) != 0 \
            #         and G_CLEF_NOTES[-1] == list(reversed(self.note_symbols))[
            #     (h_line + clef_offset) % len(self.note_symbols)]:
            #     current_line_width = pdf.line_width
            #     pdf.set_line_width(1)
            #     pdf.line(x0 + pdf.line_width / 2, y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2,
            #              x0 + (x1 - x0) - ((x1 - x0) % BEAT_WIDTH) - pdf.line_width / 2,
            #              y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2)
            #     pdf.set_line_width(current_line_width)
            #     if G_CLEF_NOTES[-1] == "G":
            #         # store g clef position for later
            #         G_CLEF_Y = y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2
            #     G_CLEF_NOTES = G_CLEF_NOTES[:-1]
            # else:
            pdf.line(x0, y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2,
                     x0 + (x1 - x0) - ((x1 - x0) % BEAT_WIDTH),
                     y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2)

        # Draw vertical lines
        for v_line in range(int((x1 - x0) / BEAT_WIDTH) + 1):
            line_x = x0 + v_line * BEAT_WIDTH
            y_half = STRIP_WIDTH / 2 - PIN_WIDTH / 2
            if v_line % 2 == 0:
                pdf.line(line_x, y - y_half, line_x, y + y_half)
            else:
                pdf.dashed_line(line_x, y - y_half, line_x, y + y_half,
                                dash_length=1.6 * PIN_WIDTH,
                                space_length=1.1 * PIN_WIDTH)

        # Draw strip limits
        pdf.set_draw_color(0, 0, 0)
        STRIP_MARGINS = self.music_box_object.get_margins()
        STRIP_WIDTH = PIN_WIDTH * (N_NOTES - 1) + sum(STRIP_MARGINS)
        pdf.line(x0, y - STRIP_WIDTH / 2, x1, y - STRIP_WIDTH / 2)
        pdf.line(x0, y + STRIP_WIDTH / 2, x1, y + STRIP_WIDTH / 2)

        return G_CLEF_Y

    def _draw_notes(self, pdf, x0, x1, y, notes):
        N_NOTES = self.music_box_object.notes_count
        BEAT_WIDTH = self.music_box_object.beat_width
        PIN_WIDTH = self.music_box_object.pin_width
        STRIP_WIDTH = (N_NOTES - 1) * PIN_WIDTH
        pdf.set_draw_color(0, 0, 0)

        NOTE_RADIUS = 1.5
        total_strip_beats = int((x1 - x0) / BEAT_WIDTH)
        min_beat = self.first_beat
        max_beat = min_beat + total_strip_beats

        # To filter out notes out of admitted pitch
        first_note = self.music_box_object.notes[0]
        last_note = self.music_box_object.notes[-1]
        min_pitch = _MidiParser.note_to_pitch(first_note[0], first_note[1])
        max_pitch = _MidiParser.note_to_pitch(last_note[0], last_note[1])

        # print("This strip: Beats: {} - {}, Note range: {} - {}. Notes left: {}"
        #       .format(min_beat, max_beat, _MidiParser.pitch_to_note(min_pitch), _MidiParser.pitch_to_note(max_pitch), len(notes)))
        print("> Notes left: {}".format(len(notes)))

        def debug_circle(x, y):
            last_color = pdf.fill_color
            pdf.set_fill_color(0, 0, 255)
            RADIUS = 2
            pdf.ellipse(x - RADIUS / 2, y - RADIUS / 2, RADIUS, RADIUS, "B")
            pdf.fill_color = last_color

        def beat_to_x(beat):
            return x0 + (beat - min_beat) * BEAT_WIDTH - NOTE_RADIUS / 2

        def note_to_y(note, octave):
            raise NotImplementedError("We are working on it!")
            # note_y0 = y + STRIP_WIDTH / 2
            # START_OCTAVE = self.settings["start_octave"]
            # note_position = self.note_symbols.index(note) + (octave - START_OCTAVE) * len(self.note_symbols)
            # return note_y0 - (note_position * PIN_WIDTH) - NOTE_RADIUS / 2

        # Remove trailing beats before (error caused?)
        while notes and notes[0]["beat"] < min_beat:
            print("deleted note because it had time {}, which is outside {} - {}".format(notes[0]["beat"], min_beat,
                                                                                         max_beat))
            notes.pop(0)
        # Draw notes inside strip
        pdf.set_fill_color(0, 0, 0)
        last_line_width = pdf.line_width
        pdf.set_line_width(NOTE_RADIUS * 0.6)
        while len(notes) > 0:
            note = notes.pop(0)
            # pprint.pprint(note)
            n_beat = note["beat"]
            n_note = note["note"]
            n_octave = note["octave"]
            n_pitch = note["raw_pitch"]
            if n_beat > max_beat:
                # print("Reached out of strip note: {}:{}{}".format(n_beat, n_note, n_octave))
                notes = [note] + notes
                break
            if n_note not in [n[0] for n in self.music_box_object.notes]:
                print("Omitting out of tune note '{}'".format(n_note))
                continue
            if not min_pitch <= n_pitch <= max_pitch:
                print("Cannot draw note: {} is out of {} - {})"
                      .format(_MidiParser.pitch_to_note(n_pitch),
                              _MidiParser.pitch_to_note(min_pitch),
                              _MidiParser.pitch_to_note(max_pitch)))
                continue
            # Draw note
            pdf.ellipse(beat_to_x(n_beat), note_to_y(n_note, n_octave), NOTE_RADIUS, NOTE_RADIUS, "B")
        pdf.set_line_width(last_line_width)
        return notes


def parse_args():
    def _midi_file(s):
        # check if exists
        if not os.path.exists(s):
            raise argparse.ArgumentTypeError("File '{}' doesn't exist".format(s))
        _, ext = os.path.splitext(s)
        if ext.lower() != ".mid":
            raise argparse.ArgumentTypeError("Unsupported extension: '{}'. Use a midi file only".format(s))
        # Check if valid midi file
        try:
            midi.read_midifile(s)
        except Exception as e:
            raise argparse.ArgumentTypeError("Could not process midi file! '{}'".format(e))
        return s

    def _title_string(s):
        min_l = 1
        max_l = 50
        if not min_l <= len(s) <= max_l:
            raise argparse.ArgumentTypeError("Length of '{}' is out of range '[{}, {}]".format(len(s), min_l, max_l))
        return s

    def _real_dir(s):
        if not os.path.exists(s):
            raise argparse.ArgumentTypeError("Directory '{}' doesn't exist".format(s))
        return s

    ap = argparse.ArgumentParser(description="MIDI Music paper strips generator for Kikkerland's music box")
    ap.add_argument("midi_file", metavar="MIDI_FILE", type=_midi_file, help="MIDI file to parse")
    ap.add_argument("song_title", metavar="SONG_TITLE", type=_title_string, help="Title of the song")
    ap.add_argument("song_author", metavar="SONG_AUTHOR", type=_title_string, help="Author of the song")
    ap.add_argument("output_dir", metavar="OUTPUT_DIR", type=_real_dir, help="Directory where to put the output",
                    nargs="?")

    ap.add_argument("--paper_size", "-s", help="(mm) Size of the paper where to print", nargs=2, default=[215.9, 279.4],
                    type=float)
    ap.add_argument("--music_box", "-b", help="Which box from the music boxes definition to use", type=int, default=1)
    args = ap.parse_args()
    if not args.output_dir:
        args.output_dir = os.path.dirname(args.midi_file)
    return args


def parse_args_old():
    # Define custom arg types
    def _restricted_pin_number(x):
        x = int(x)
        min = 15
        max = 100
        if not min <= x <= max:
            raise argparse.ArgumentTypeError("{} out of range [{}, {}]".format(x, min, max))
        return x

    def _restricted_pin_width(x):
        x = float(x)
        min = 0.1
        max = 4
        if not min <= x <= max:
            raise argparse.ArgumentTypeError("{} out of range [{}, {}]".format(x, min, max))
        return x

    def _restricted_beat_width(x):
        x = float(x)
        min = 1
        max = 20
        if not min <= x <= max:
            raise argparse.ArgumentTypeError("{} out of range [{}, {}]".format(x, min, max))
        return x

    def _restricted_strip_padding(x):
        x = float(x)
        min = 0
        max = 15
        if not min <= x <= max:
            raise argparse.ArgumentTypeError("{} out of range [{}, {}]".format(x, min, max))
        return x

    def _restricted_strip_separation(x):
        x = float(x)
        min = 0
        max = 30
        if not min <= x <= max:
            raise argparse.ArgumentTypeError("{} out of range [{}, {}]".format(x, min, max))
        return x

    def _midi_file(s):
        # check if exists
        if not os.path.exists(s):
            raise argparse.ArgumentTypeError("File '{}' doesn't exist".format(s))
        _, ext = os.path.splitext(s)
        if ext.lower() != ".mid":
            raise argparse.ArgumentTypeError("Unsupported extension: '{}'. Use a midi file only".format(s))
        # Check if valid midi file
        try:
            midi.read_midifile(s)
        except Exception as e:
            raise argparse.ArgumentTypeError("Could not process midi file! '{}'".format(e))
        return s

    def _title_string(s):
        min_l = 1
        max_l = 50
        if not min_l <= len(s) <= max_l:
            raise argparse.ArgumentTypeError("Length of '{}' is out of range '[{}, {}]".format(len(s), min_l, max_l))
        return s

    def _real_dir(s):
        if not os.path.exists(s):
            raise argparse.ArgumentTypeError("Directory '{}' doesn't exist".format(s))
        return s

    ap = argparse.ArgumentParser(description="MIDI Music paper strips generator for Kikkerland's music box")
    ap.add_argument("midi_file", metavar="MIDI_FILE", type=_midi_file, help="MIDI file to parse")
    ap.add_argument("song_title", metavar="SONG_TITLE", type=_title_string, help="Title of the song")
    ap.add_argument("song_author", metavar="SONG_AUTHOR", type=_title_string, help="Author of the song")
    ap.add_argument("output_dir", metavar="OUTPUT_DIR", type=_real_dir, help="Directory where to put the output",
                    nargs="?")

    ap.add_argument("--paper_size", "-s", help="(mm) Size of the paper where to print", nargs=2, default=[215.9, 279.4],
                    type=float)
    # ap.add_argument("--pin_number", "-n", help="Number of notes the box can reproduce", type=_restricted_pin_number, default=15)
    # ap.add_argument("--pinwidth", "-pw", help="(mm) Physical separation between note pins", type=_restricted_pin_width, default=2.0)
    ap.add_argument("--beatwidth", "-bw", help="(mm) Size of eighth notes. Affects song speed",
                    type=_restricted_beat_width, default=4.0)
    ap.add_argument("--strip_padding", "-sm", help="(mm) Additional strip width", type=_restricted_strip_padding,
                    default=6.6)
    ap.add_argument("--strip_separation", "-ss", help="(mm) Separation between strips",
                    type=_restricted_strip_separation, default=0)
    args = ap.parse_args()
    if not args.output_dir:
        args.output_dir = os.path.dirname(args.midi_file)
    return args


def load_music_boxes():
    settings_file = "musicboxes.yaml"
    if not os.path.isfile(settings_file) or not settings_file.strip().lower().endswith(".yaml"):
        raise IOError("No valid configurations file could be found!!")

    # Try to parse file settings
    settings_dict = yaml.load(open(settings_file))
    print("Loaded '{}'".format(settings_file))
    settings_version = settings_dict["version"]
    print("Settings file version: {version}\n"
          "Music boxes configured: {n_boxes}"
          .format(version=settings_version,
                  n_boxes=len(settings_dict["music_boxes"])))

    # Construct boxes from settings
    loaded_boxes = list()
    for box_definition in settings_dict["music_boxes"]:
        loaded_boxes.append(MusicBox(box_definition))
    print("Boxes loaded")
    return loaded_boxes


def main():
    # Get and parse args
    parsed_args = parse_args()
    # Check if selected box exists
    boxes = load_music_boxes()

    selected_box_index = parsed_args.music_box - 1
    if selected_box_index not in range(len(boxes)):
        raise argparse.ArgumentError("The selected music box index '{mb_index}' doesn't exist."
                                     "Check the defined music boxes in the definitions file")
    selected_box = boxes[selected_box_index]
    print("Will use the following music box: ")
    print(selected_box)

    # Generate instance
    doc = MusicBoxPDFGenerator(selected_box,
                               strip_separation=0,
                               paper_size=parsed_args.paper_size)

    print("Will generate with settings:\n"
          "\tPaper size: {paper_size} (Warning: HP p1102w printer supported dimensions are [76.2-215.9]x[127-356]\n"
          "\tOutput dir: {out_dir}\n"
          .format(paper_size=parsed_args.paper_size,
                  out_dir=parsed_args.output_dir))

    print("Starting document generation...")
    # Create unique pdf name located where midi file is
    midi_folder = os.path.dirname(parsed_args.midi_file)
    pdf_name_core = "{}".format(os.path.splitext(os.path.basename(parsed_args.midi_file))[0])
    pdf_name = "{}.pdf".format(pdf_name_core)
    n = 0
    while os.path.exists(os.path.join(parsed_args.output_dir, "{}".format(pdf_name))):
        n += 1
        pdf_name = "{}_{}.pdf".format(pdf_name_core, n)
    # generate
    doc.generate(midi_file=parsed_args.midi_file,
                 output_file=os.path.join(parsed_args.output_dir, pdf_name),
                 song_title=parsed_args.song_title,
                 song_author=parsed_args.song_author)

    print("Done. Generated as '{}'".format(os.path.join(parsed_args.output_dir, pdf_name)))


if __name__ == "__main__":
    main()
