# coding=utf-8

"""
Basic example of usage
"""
import os
import argparse
from fpdf import FPDF
import midi


class _MidiProcessor:
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
        return "C C# D D# E F F# G G# A A# B".split(" ")[midi_pitch_code % 12], -1 + int(midi_pitch_code/12)

    @staticmethod
    def note_to_pitch(note, octave):
        return 12 * (octave+1) + "C C# D D# E F F# G G# A A# B".split(" ").index(note)

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
                    note, octave = _MidiProcessor.pitch_to_note(event.get_pitch())
                    rendered.append({
                        "note": note,
                        "octave": octave,
                        "beat": event.tick/resolution * 2,
                        "raw_pitch": event.get_pitch()
                    })
        rendered = sorted(rendered, key=lambda k:k["beat"])
        return rendered


class MusicBoxPDFGenerator(FPDF):
    """
    Represents a music box document.
    All units in mm except for fonts, which are in points.
    """
    def __init__(self, n_notes, pin_width, strip_margin, strip_separation=0, tuning="C", start_note="C", start_octave=5, beat_width=8, paper_size=(279.4, 215.9)):
        super().__init__("p", "mm", paper_size)
        self.set_title("Testing this shit")
        self.set_author("Maximiliano Castro")
        self.set_auto_page_break(True)
        self.set_margins(8, 6, 8)
        self.alias_nb_pages()
        self.set_compression(True)

        self.settings = {
            "n_notes": n_notes,
            "pin_width": pin_width,
            "strip_margin": strip_margin,
            "beat_width": beat_width,
            "tuning": tuning,
            "start_note": start_note,
            "start_octave": start_octave,
            "strip_separation": strip_separation
        }
        self.generated = False

    def generate(self, midi_file, output_file, song_title="NO-TITLE", song_author="NO-AUTHOR"):
        if self.generated:
            raise RuntimeError("Document was already generated!")

        # Parse midi file
        parsed_notes = _MidiProcessor.render_to_box(midi.read_midifile(midi_file))

        self.add_page()
        strip_generator = StripGenerator(settings=self.settings,
                                         song_title=song_title,
                                         song_author=song_author)
        # Add notes to strip
        STRIP_SEPARATION = self.settings["strip_separation"]
        current_y = - strip_generator.get_height() / 2 - STRIP_SEPARATION + self.t_margin

        drawn_beats = 0
        while len(parsed_notes) > 0:
            print("> Created new strip")
            new_strip = strip_generator.new_strip(drawn_beats)
            current_y += strip_generator.get_height() + STRIP_SEPARATION
            if current_y + strip_generator.get_height() / 2 > self.h - self.b_margin:
                print("> Had to add page")
                self.add_page()
                current_y = strip_generator.get_height() / 2 + self.t_margin
            parsed_notes, total_strip_beats = new_strip.draw(pdf=self,
                                                             x0=self.l_margin,
                                                             x1=self.w - self.r_margin,
                                                             y=current_y,
                                                             notes=parsed_notes)
            drawn_beats += total_strip_beats
            print("> Drew a strip")

        self.generated = True
        self.output(output_file, "F")
        print("Done, Saved as {}".format(output_file))


class StripGenerator:
    def __init__(self, settings, song_title=None, song_author=None):
        self.settings = settings
        tuning = settings["tuning"]
        start_note = settings["start_note"]
        self.song_title = song_title
        self.song_author = song_author
        if tuning == "C":
            self.note_symbols = "C,D,E,F,G,A,B".split(",")
        elif tuning == "X":
            self.note_symbols = "C,C#,D,D#,E,F,F#,G,G#,A,A#,B".split(",")
        else:
            raise RuntimeError("Unsupported tuning '{}'".format(tuning))
        if start_note not in self.note_symbols:
            raise ValueError("Incorrect starting note '{}'".format(start_note))
        note_offset = self.note_symbols.index(start_note)
        # rotate note symbols according to start note position in them
        self.note_symbols = self.note_symbols[note_offset:] + self.note_symbols[:note_offset]
        print("Created strip generator. Notes: {}".format(', '.join(self.note_symbols)))
        self.has_header = False

    def new_strip(self, first_beat_position):
        if not self.has_header:
            self.has_header = True
            return Strip(song_title=self.song_title,
                         song_author=self.song_author,
                         settings=self.settings,
                         note_symbols=self.note_symbols,
                         is_first=True)
        else:
            return Strip(settings=self.settings,
                         note_symbols=self.note_symbols,
                         first_beat=first_beat_position)

    def get_height(self):
        PIN_WIDTH = self.settings["pin_width"]
        N_NOTES = self.settings["n_notes"]
        STRIP_MARGIN = self.settings["strip_margin"]
        return PIN_WIDTH*(N_NOTES-1) + 2*STRIP_MARGIN


class Strip:
    def __init__(self, settings, note_symbols, first_beat=0, is_first=False, song_title=None, song_author=None):
        """
        Creates a "Strip" representing a paper strip which will contain the notes

        Parameters
        ----------
        settings: dict
            Dictionary with the main music box settings
        note_symbols: List[str]
            Notes present in the scale
        first_beat: int
            Relative position of this strip's first beat
        is_first: bool
            If this strip is the first one (and should have a header)
        song_title: str
            Song title
        song_author: str
            Song author
        """
        self.is_first = is_first
        self.settings = settings
        self.note_symbols = note_symbols
        self.song_title = song_title if song_title else "NO-TITLE"
        self.song_author = song_author if song_author else "NO-AUTHOR"
        self.first_beat = first_beat

    def draw(self, pdf, x0, x1, y, notes):
        """ Draws the strip in the pdf document """
        x_start = x0
        BEAT_WIDTH = self.settings["beat_width"]

        if self.is_first:
            # Draw strip header
            x_start = self._draw_header(pdf, x_start, y)

        # Draw notes grid
        g_clef_y = self._draw_body(pdf, x_start, x1, y)

        if self.is_first and g_clef_y:
            #draw G clef
            PIN_WIDTH = self.settings["pin_width"]
            G_CLEF_H =  PIN_WIDTH * 15
            pdf.image("g_clef.png", x=x_start,
                      y=g_clef_y - G_CLEF_H / 1.8,
                      h=G_CLEF_H)
            x_start += 2*BEAT_WIDTH

        notes_left = self._draw_notes(pdf, x_start, x1, y, notes)

        total_strip_beats = int((x1 - x_start) / BEAT_WIDTH)
        return notes_left, total_strip_beats

    def _draw_header(self, pdf, x0, y):
        #def show_pointer(s="O"):
        # rotate reference

        pdf.rotate(90, x0, y)
        # Coordinates are the same, but are drawn rotated
        current_y = y
        # draw triangle
        TRIANGLE_SIZE = (8, 8)
        TRIANGLE_MARGIN_T = 4
        pdf.image(name="triangle_tiny.png",
                  x=x0-TRIANGLE_SIZE[0]/2,
                  y=current_y + TRIANGLE_MARGIN_T,
                  w=TRIANGLE_SIZE[0],
                  h=TRIANGLE_SIZE[1])
        current_y += TRIANGLE_MARGIN_T  # Relative to rotated perspective
        # Write song info:
        STRIP_MARGIN = self.settings["strip_margin"]
        PIN_WIDTH = self.settings["pin_width"]
        N_NOTES = self.settings["n_notes"]
        MAX_TITLE_WIDTH = PIN_WIDTH * N_NOTES + 2 * STRIP_MARGIN - 4
        pdf.set_font("courier", "B", 30)

        while max(pdf.get_string_width(self.song_title), pdf.get_string_width(self.song_author)) > MAX_TITLE_WIDTH:
            pdf.set_font_size(pdf.font_size_pt - 0.1)
        pdf.text(x=x0-pdf.get_string_width(self.song_title)/2,
                 y=current_y + TRIANGLE_SIZE[1] + pdf.font_size + 5,
                 txt=self.song_title)
        current_y += TRIANGLE_SIZE[1] + pdf.font_size + 5
        pdf.text(x=x0-pdf.get_string_width(self.song_author)/2,
                 y=current_y + pdf.font_size + 3,
                 txt=self.song_author)
        current_y += pdf.font_size + 10

        # draw notes
        x0_first_note = x0 - N_NOTES * PIN_WIDTH/2
        pdf.set_font("Arial", "B", 8)
        for n in range(N_NOTES):
            symbol = self.note_symbols[n % len(self.note_symbols)]
            pdf.text(x0_first_note + n*PIN_WIDTH,
                     current_y + pdf.font_size,
                     symbol)
        current_y += pdf.font_size + 1

        # un-rotate
        pdf.rotate(0, y, x0)
        x0_adjusted = x0 + (current_y - y)

        # Draw strip limits
        STRIP_WIDTH = PIN_WIDTH*(N_NOTES-1) + 2*STRIP_MARGIN
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
        N_NOTES = self.settings["n_notes"]
        PIN_WIDTH = self.settings["pin_width"]
        STRIP_WIDTH = N_NOTES * PIN_WIDTH
        BEAT_WIDTH = self.settings["beat_width"]
        G_CLEF_NOTES = "EGBDF"
        G_CLEF_Y = None
        do_g_clef = all([x in self.note_symbols for x in G_CLEF_NOTES])
        clef_offset = len(self.note_symbols) - (N_NOTES % len(self.note_symbols))
        for h_line in range(N_NOTES):
            if do_g_clef and len(G_CLEF_NOTES) != 0 \
                    and G_CLEF_NOTES[-1] == list(reversed(self.note_symbols))[(h_line + clef_offset)% len(self.note_symbols)]:
                current_line_width = pdf.line_width
                pdf.set_line_width(1)
                pdf.line(x0 + pdf.line_width/2, y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2,
                         x0 + (x1-x0) - ((x1-x0) % BEAT_WIDTH) - pdf.line_width/2, y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2)
                pdf.set_line_width(current_line_width)
                if G_CLEF_NOTES[-1] == "G":
                    # store g clef position for later
                    G_CLEF_Y = y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2
                G_CLEF_NOTES = G_CLEF_NOTES[:-1]
            else:
                pdf.line(x0, y - STRIP_WIDTH/2 + PIN_WIDTH*h_line + PIN_WIDTH/2,
                         x0 + (x1 - x0) - ((x1 - x0) % BEAT_WIDTH), y - STRIP_WIDTH/2 + PIN_WIDTH*h_line + PIN_WIDTH/2)

        # Draw vertical lines
        for v_line in range(int((x1-x0)/BEAT_WIDTH) + 1):
            line_x = x0 + v_line*BEAT_WIDTH
            y_half = STRIP_WIDTH/2 - PIN_WIDTH/2
            if v_line % 2 == 0:
                pdf.line(line_x, y - y_half, line_x, y + y_half)
            else:
                pdf.dashed_line(line_x, y - y_half, line_x, y + y_half,
                                dash_length=1.6*PIN_WIDTH,
                                space_length=1.1*PIN_WIDTH)

        # Draw strip limits
        pdf.set_draw_color(0, 0, 0)
        STRIP_MARGIN = self.settings["strip_margin"]
        STRIP_WIDTH = PIN_WIDTH * (N_NOTES-1) + 2 * STRIP_MARGIN
        pdf.line(x0, y - STRIP_WIDTH/2, x1, y - STRIP_WIDTH/2)
        pdf.line(x0, y + STRIP_WIDTH/2, x1, y + STRIP_WIDTH/2)

        return G_CLEF_Y

    def _draw_notes(self, pdf, x0, x1, y, notes):
        N_NOTES = self.settings["n_notes"]
        BEAT_WIDTH = self.settings["beat_width"]
        PIN_WIDTH = self.settings["pin_width"]
        STRIP_WIDTH = (N_NOTES-1) * PIN_WIDTH
        pdf.set_draw_color(0, 0, 0)

        NOTE_RADIUS = 1.5
        total_strip_beats = int((x1 - x0) / BEAT_WIDTH)
        min_beat = self.first_beat
        max_beat = min_beat + total_strip_beats

        # To filter out notes out of admitted pitch
        min_pitch = _MidiProcessor.note_to_pitch(self.settings["start_note"], self.settings["start_octave"])
        max_pitch = _MidiProcessor.note_to_pitch(self.note_symbols[self.note_symbols.index(self.settings["start_note"])
                                                                   + N_NOTES % len(self.note_symbols) - 1],
                                                 self.settings["start_octave"] + int(N_NOTES/len(self.note_symbols)))
        print("This strip: Beats: {} - {}, Note range: {} - {}. Notes left: {}"
              .format(min_beat, max_beat, _MidiProcessor.pitch_to_note(min_pitch), _MidiProcessor.pitch_to_note(max_pitch), len(notes)))

        def debug_circle(x, y):
            last_color = pdf.fill_color
            pdf.set_fill_color(0, 0, 255)
            RADIUS = 2
            pdf.ellipse(x-RADIUS/2, y-RADIUS/2, RADIUS, RADIUS, "B")
            pdf.fill_color = last_color

        def beat_to_x(beat):
            return x0 + (beat - min_beat)*BEAT_WIDTH - NOTE_RADIUS/2

        def note_to_y(note, octave):
            note_y0 = y + STRIP_WIDTH/2
            START_OCTAVE = self.settings["start_octave"]
            note_position = self.note_symbols.index(note) + (octave - START_OCTAVE)*len(self.note_symbols)
            return note_y0 - (note_position*PIN_WIDTH) - NOTE_RADIUS/2

        # Remove trailing beats before (error caused?)
        while notes and notes[0]["beat"] < min_beat:
            print("deleted note because it had time {}, which is outside {} - {}".format(notes[0]["beat"], min_beat, max_beat))
            notes.pop(0)
        # Draw notes inside strip
        pdf.set_fill_color(0, 0, 0)
        last_line_width = pdf.line_width
        pdf.set_line_width(NOTE_RADIUS*0.6)
        while len(notes) > 0:
            note = notes.pop(0)
            # pprint.pprint(note)
            n_beat = note["beat"]
            n_note = note["note"]
            n_octave = note["octave"]
            n_pitch = note["raw_pitch"]
            if n_beat > max_beat:
                print("Reached out of strip note: {}:{}{}".format(n_beat, n_note, n_octave))
                notes = [note] + notes
                break
            if n_note not in self.note_symbols:
                print("Omitting out of tune note '{}'".format(n_note))
                continue
            if not min_pitch <= n_pitch <= max_pitch:
                print("Cannot draw note: {} is out of {} - {})"
                      .format(_MidiProcessor.pitch_to_note(n_pitch),
                              _MidiProcessor.pitch_to_note(min_pitch),
                              _MidiProcessor.pitch_to_note(max_pitch)))
                continue
            # Draw note
            pdf.ellipse(beat_to_x(n_beat), note_to_y(n_note, n_octave), NOTE_RADIUS, NOTE_RADIUS, "B")
        pdf.set_line_width(last_line_width)
        # for note in notes:
        #     if note["note"] not in self.note_symbols:
        #         print("Tried to draw '{}' which is out of tune")
        #         continue
        #     print("Drawing at time {}".format(note["time"]))
        #     note_x = beat_x0 + (note["time"] - self.first_beat_position) * BEAT_WIDTH
        #     note_y = y
        #     pdf.set_fill_color(0, 0, 0)
        #     pdf.ellipse(note_x-NOTE_RADIUS/2, note_y-NOTE_RADIUS/2, NOTE_RADIUS, NOTE_RADIUS, "F")
        #     notes = notes[1:]
        return notes

def test_oop_document_drawing():
    doc = MusicBoxPDFGenerator(n_notes=15,
                               pin_width=2,
                               strip_margin=6.6,
                               beat_width=4,
                               tuning="C",
                               start_note="C",
                               start_octave=4,
                               paper_size=(770.0, 129.0))
    doc.generate(midi_file="bob.mid",
                 output_file="delete_me.pdf",
                 song_title="Three little birds",
                 song_author="Bob Marley")


def parse_args():
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

    ap = argparse.ArgumentParser(description="MIDI Music paper strips generator for Kikkerland's music box")
    ap.add_argument("midi_file", metavar="MIDI_FILE", type=_midi_file, help="MIDI file to parse")
    ap.add_argument("song_title", metavar="SONG_TITLE", type=_title_string, help="Title of the song")
    ap.add_argument("song_author", metavar="SONG_AUTHOR", type=_title_string, help="Author of the song")

    ap.add_argument("--paper_size", "-s", help="(mm) Size of the paper where to print", nargs=2, default=[215.9, 279.4], type=float)
    ap.add_argument("--pin_number", "-n", help="Number of notes the box can reproduce", type=_restricted_pin_number, default=15)
    ap.add_argument("--pinwidth", "-pw", help="(mm) Physical separation between note pins", type=_restricted_pin_width, default=2.0)
    ap.add_argument("--beatwidth", "-bw", help="(mm) Size of eighth notes. Affects song speed", type=_restricted_beat_width, default=4.0)
    ap.add_argument("--strip_padding", "-sm", help="(mm) Additional strip width", type=_restricted_strip_padding, default=6.6)
    ap.add_argument("--strip_separation", "-ss", help="(mm) Separation between strips", type=_restricted_strip_separation, default=0)
    return ap.parse_args()


def main():
    # Get and parse args
    parsed_args = parse_args()
    # Generate instance
    doc = MusicBoxPDFGenerator(n_notes=parsed_args.pin_number,
                               pin_width=parsed_args.pinwidth,
                               strip_margin=parsed_args.strip_padding,
                               strip_separation=parsed_args.strip_separation,
                               beat_width=parsed_args.beatwidth,
                               tuning="C",
                               start_note="C",
                               start_octave=4,
                               paper_size=parsed_args.paper_size)

    print("Will generate with settings:\n"
          "\tPaper size: {paper_size} (Warning: p1102w suports [76.2-215.9]x[127-356]\n"
          "\tPin number: {pin_number}\n"
          "\tStrip padding: {strip_padding}\n"
          "\tStrip separation: {strip_separation}\n"
          "\tBeat width: {beat_width}\n"
          "\tPin size: {pin_size}\n"
          .format(paper_size=parsed_args.paper_size,
                  pin_number=parsed_args.pin_number,
                  strip_padding=parsed_args.strip_padding,
                  strip_separation=parsed_args.strip_separation,
                  beat_width=parsed_args.beatwidth,
                  pin_size=parsed_args.pinwidth))

    print("Starting document generation...")
    pdf_name = "{}.pdf".format(os.path.splitext(os.path.basename(parsed_args.midi_file))[0])
    doc.generate(midi_file=parsed_args.midi_file,
                 output_file=pdf_name,
                 song_title=parsed_args.song_title,
                 song_author=parsed_args.song_author)

    print("Done. Generated as '{}'".format(pdf_name))

if __name__ == "__main__":
    main()