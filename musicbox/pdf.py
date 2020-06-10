from .midi import Parser
import midi
from fpdf import FPDF

class Renderer(FPDF):
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
        # Beware: Complex, giant midi files will be brought to memory all at once with this step!
        parsed_notes = Parser.render_to_box(midi.read_midifile(midi_file))

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
        # g_clef_y = self._draw_body(pdf, x_start, x1, y)
        self._draw_body(pdf, x_start, x1, y)

        # if self.is_first and g_clef_y:
        #     # draw G clef
        #     PIN_WIDTH = self.music_box_object.pin_width
        #     G_CLEF_H = PIN_WIDTH * 15
        #     pdf.image("res/g_clef.png", x=x_start,
        #               y=g_clef_y - G_CLEF_H / 1.8,
        #               h=G_CLEF_H)
        #     x_start += 2 * BEAT_WIDTH

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

        self._draw_note_labels(pdf, x0=x0 - N_NOTES * PIN_WIDTH / 2, y=current_y)

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

    def _draw_note_labels(self, pdf, x0, y, font_size=6):
        pdf.set_font("Arial", "B", font_size)
        notes = self.music_box_object.notes

        for n in range(len(notes)):
            symbol = notes[n % len(notes)][0]
            # First letter
            pdf.set_font_size(font_size)
            pdf.text(x0 + n * self.music_box_object.pin_width,
                     y + pdf.font_size,
                     symbol[0])
            # Rest of the symbol
            pdf.set_font_size(font_size/2)
            pdf.text(x0 + n * self.music_box_object.pin_width + pdf.font_size*1.4,
                     y + pdf.font_size*2,
                     symbol[1:])

        pdf.set_font_size(font_size)

    def _draw_body(self, pdf, x0, x1, y):
        pdf.set_draw_color(140, 140, 140)
        N_NOTES = self.music_box_object.notes_count
        PIN_WIDTH = self.music_box_object.pin_width
        STRIP_WIDTH = N_NOTES * PIN_WIDTH
        BEAT_WIDTH = self.music_box_object.beat_width
        # G_CLEF_NOTES = "EGBDF"
        # G_CLEF_Y = None
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

        # return G_CLEF_Y

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
        min_pitch = Parser.note_to_pitch(first_note[0], first_note[1])
        max_pitch = Parser.note_to_pitch(last_note[0], last_note[1])

        # print("This strip: Beats: {} - {}, Note range: {} - {}. Notes left: {}"
        #       .format(min_beat, max_beat, Parser.pitch_to_note(min_pitch), Parser.pitch_to_note(max_pitch), len(notes)))
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
            note_y0 = y + STRIP_WIDTH / 2
            note_position = self.music_box_object.find_note((note, octave))
            return note_y0 - (note_position * PIN_WIDTH) - NOTE_RADIUS / 2

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
            if not min_pitch <= n_pitch <= max_pitch:
                print(f"Cannot draw note: {Parser.pitch_to_note(n_pitch)} is outside [{self.music_box_object.notes[0]} - {self.music_box_object.notes[-1]}]")
                continue
            # Draw note
            if not self.music_box_object.has_note(f"{n_note}{n_octave}"):
                print(f"Skipped {n_note}{n_octave} (not present in music box)")
                continue
            note_y_pos = note_to_y(n_note, n_octave)
            pdf.ellipse(beat_to_x(n_beat), note_y_pos, NOTE_RADIUS, NOTE_RADIUS, "B")
        pdf.set_line_width(last_line_width)
        return notes