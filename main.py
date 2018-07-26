# coding=utf-8

"""
Basic example of usage
"""

from fpdf import FPDF
from fpdf import Template
import midi
import pprint


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
    def _pitch_to_note(midi_pitch_code):
        return "C C# D D# E F F# G G# A A# B".split(" ")[midi_pitch_code % 12], -1 + int(midi_pitch_code/12)

    @staticmethod
    def render_to_box(midi_object):
        """
        Parses and generates a music-box-compatible structure

        Parameters
        ----------
        midi_object: midi.Pattern

        Returns
        -------

        """
        midi_object.make_ticks_abs()
        resolution = midi_object.resolution
        rendered = list()
        for event in midi_object[0]:
            if isinstance(event, midi.NoteOnEvent) and event.get_velocity() > 0:
                note, octave = _MidiProcessor._pitch_to_note(event.get_pitch())
                rendered.append({
                    "note": note,
                    "octave": octave,
                    "time": event.tick/resolution
                })
        return rendered


def test_fpdf_templates():
    elements = list()
    elements.append({'name': 'company_name', 'type': 'T', 'x1': 17.0, 'y1': 32.5, 'x2': 115.0, 'y2': 37.5,
                     'font': 'Arial', 'size': 12.0, 'bold': 1, 'italic': 0, 'underline': 0, 'foreground': 0,
                     'background': 0, 'align': 'I', 'text': 'Testeando la wea y ke paza bastardo qlo','priority': 2,})
    for x in range(2):
        last_y = elements[-1]["y2"]
        elements.append({
            "name": "box_{}".format(x+1),
            "type": "B",
            "x1": 10, "y1": last_y,
            "x2": 200, "y2": last_y + 50,
            "font": "Arial",
            "size": "10.0",
            "bold": 1,
            "italic": 0,
            "underline": 0,
            "foreground": 1,
            "background": 0,
            "align": "I",
            "text": u"Caja {}".format(x+1),
            "priority": 0
        })
    f = Template(format="letter", elements=elements, title="Testeando the template wea")
    f.add_page()
    print("Rendering")
    f.render("./delete_me.pdf")
    print("done")

class MusicBoxPDFGenerator(FPDF):
    """
    Represents a music box document.
    All units in mm except for fonts, which are in points.
    """
    def __init__(self, n_notes, pin_width, strip_margin, tuning="C", start_note="C", beat_width=8):
        super().__init__("p", "mm", (279.4, 215.9))
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
            "start_note": start_note
        }
        self.generated = False

    def generate(self, midi_file, output_file):
        if self.generated:
            raise RuntimeError("Document was already generated!")

        # Parse midi file
        parsed_notes = _MidiProcessor.render_to_box(midi.read_midifile(midi_file))

        self.add_page()
        strip_generator = StripGenerator(settings=self.settings,
                                         song_title="Cancion qlia",
                                         song_author="Autor qliao")
        # Add notes to strip
        current_y = strip_generator.get_height() / 2 + self.t_margin
        STRIP_MARGIN = 10

        while len(parsed_notes) > 0:
            print("> Created new strip")
            new_strip = strip_generator.new_strip()
            current_y += strip_generator.get_height() + STRIP_MARGIN
            if current_y + strip_generator.get_height() / 2 > self.h - self.b_margin:
                print("> Had to add page")
                self.add_page()
                current_y = strip_generator.get_height() / 2 + self.t_margin
            parsed_notes = new_strip.draw(pdf=self,
                                          x0=self.l_margin,
                                          x1=self.w - self.r_margin,
                                          y=current_y,
                                          notes=parsed_notes)
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

    def new_strip(self):
        if not self.has_header:
            self.has_header = True
            return Strip(song_title=self.song_title,
                         song_author=self.song_author,
                         settings=self.settings,
                         note_symbols=self.note_symbols,
                         is_first=True)
        else:
            return Strip(settings=self.settings,
                         note_symbols=self.note_symbols)

    def get_height(self):
        PIN_WIDTH = self.settings["pin_width"]
        N_NOTES = self.settings["n_notes"]
        STRIP_MARGIN = self.settings["strip_margin"]
        return PIN_WIDTH*N_NOTES + 2*STRIP_MARGIN


class Strip:
    def __init__(self, settings, note_symbols, is_first=False, song_title=None, song_author=None):
        self.is_first = is_first
        self.settings = settings
        self.note_symbols = note_symbols
        self.song_title = song_title if song_title else "NO-TITLE"
        self.song_author = song_author if song_author else "NO-AUTHOR"

    def draw(self, pdf, x0, x1, y, notes):
        """ Draws the strip in the pdf document """
        x_start = x0
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
        return notes[1:]

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
        STRIP_WIDTH = PIN_WIDTH*N_NOTES + 2*STRIP_MARGIN
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
                         x1 - pdf.line_width/2, y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2)
                pdf.set_line_width(current_line_width)
                if (G_CLEF_NOTES[-1] == "G"):
                    # store g clef position for later
                    G_CLEF_Y = y - STRIP_WIDTH / 2 + PIN_WIDTH * h_line + PIN_WIDTH / 2
                G_CLEF_NOTES = G_CLEF_NOTES[:-1]
            else:
                pdf.line(x0, y - STRIP_WIDTH/2 + PIN_WIDTH*h_line + PIN_WIDTH/2,
                         x1, y - STRIP_WIDTH/2 + PIN_WIDTH*h_line + PIN_WIDTH/2)

        # Draw vertical lines
        BEAT_WIDTH = self.settings["beat_width"]
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
        STRIP_WIDTH = PIN_WIDTH * N_NOTES + 2 * STRIP_MARGIN
        pdf.line(x0, y - STRIP_WIDTH/2, x1, y - STRIP_WIDTH/2)
        pdf.line(x0, y + STRIP_WIDTH/2, x1, y + STRIP_WIDTH/2)

        return G_CLEF_Y


def test_fpdf_drawing():
    # Crear wea
    pdf = FPDF("p", "mm", (279.4, 215.9))
    pdf.set_title("Testing this shit")
    pdf.set_author("Maximiliano Castro")
    pdf.set_auto_page_break(True)
    pdf.set_margins(8,6,8)
    pdf.alias_nb_pages()
    pdf.compress = True

    # Añadir contenido
    pdf.add_page()
    # Agregar título
    pdf.set_font("arial", "B", 20)
    pdf.cell(w=0, h=10, txt="Wena ctm probandoóó ññ",
             border=1, ln=1, align="C")
    # Dibujar weas
    N_NOTES = 15
    NOTE_NAMES = "CDEFGAB"
    G_CLEF_NOTES = "EGBDF"
    G_CLEF_Y = -1
    NOTE_OFFSET = 0
    NOTE_SEPARATION = 2
    BEATS_PER_STRIP = 60
    FIRST_STRIP_OFFSET = 20
    x0 = pdf.l_margin + FIRST_STRIP_OFFSET
    x1 = pdf.w - pdf.r_margin
    PARTITURE_W = x1-x0
    y0 = 30
    y1 = y0 + NOTE_SEPARATION*(N_NOTES-1)
    # Dibujar líneas horizontales notas
    pdf.set_font("arial", "B", 7)
    pdf.set_draw_color(140, 140, 140)
    for n in range(N_NOTES):
        y = y0 + n*NOTE_SEPARATION
        if len(G_CLEF_NOTES) != 0 and ''.join(reversed(NOTE_NAMES))[(n+len(NOTE_NAMES)-(N_NOTES%len(NOTE_NAMES)))%len(NOTE_NAMES)] == G_CLEF_NOTES[-1]:
            current_line_width = pdf.line_width
            pdf.set_line_width(1)
            pdf.line(x0+pdf.line_width/2, y, x1-pdf.line_width/2, y)
            pdf.set_line_width(current_line_width)
            if (G_CLEF_NOTES[-1] == "G"):
                # draw G clef
                G_CLEF_Y = y
            G_CLEF_NOTES = G_CLEF_NOTES[:-1]
        else:
            pdf.line(x0, y, x1, y)
    # draw note chars and song header
    pdf.rotate(90, x0, y0 + (N_NOTES-1)*NOTE_SEPARATION)
    rotated_y = y0 + (N_NOTES-1)*NOTE_SEPARATION
    for n in range(N_NOTES):
        note_char = NOTE_NAMES[(n + NOTE_OFFSET) % len(NOTE_NAMES)]
        pdf.text(x0 - pdf.get_string_width(note_char)/2 + n * NOTE_SEPARATION,
                 rotated_y - pdf.font_size / 3,
                 note_char)
        # pdf.rotate(270, y+pdf.font_size/3, x0)
    # Write song title
    STRIP_MARGIN_V = 7
    TOTAL_STRIP_HEIGHT = NOTE_SEPARATION*(N_NOTES-1) + 2 * STRIP_MARGIN_V
    SONG_TITLE = "Cancion culia de un culiao"
    SONG_AUTHOR = "Culiao con nombre largo"
    MAX_TITLE_FONT_SIZE_PT = 30
    pdf.set_font("courier", "B", MAX_TITLE_FONT_SIZE_PT)
    MAX_TITLE_FONT_SIZE = pdf.font_size
    while pdf.get_string_width(SONG_TITLE) > TOTAL_STRIP_HEIGHT:
        pdf.set_font_size(pdf.font_size_pt - 0.1)
    pdf.text(x=x0 + (NOTE_SEPARATION * (N_NOTES - 1))/2 -
             pdf.get_string_width(SONG_TITLE) / 2,
             y=rotated_y - pdf.font_size*3,
             txt=SONG_TITLE)
    pdf.set_font_size(15)
    while pdf.get_string_width(SONG_TITLE) > TOTAL_STRIP_HEIGHT:
        pdf.set_font_size(pdf.font_size_pt - 0.1)
    pdf.text(x=x0 + (NOTE_SEPARATION * (N_NOTES - 1))/2 -
             pdf.get_string_width(SONG_AUTHOR) / 2,
             y=rotated_y - pdf.font_size*1.7,
             txt=SONG_AUTHOR)

    # add triangle
    TRIANGLE_SIZE = (8, 8)
    pdf.image(name="triangle_tiny.png",
              x=x0 + (NOTE_SEPARATION * (N_NOTES - 1))/2 - TRIANGLE_SIZE[0]/2,
              y=rotated_y - MAX_TITLE_FONT_SIZE*2.5 + TRIANGLE_SIZE[1]/2,
              w=TRIANGLE_SIZE[0],
              h=TRIANGLE_SIZE[1])

    pdf.rotate(0, rotated_y, x0)
    # Verticales tempo
    for n in range(BEATS_PER_STRIP + 1):
        x = x0 + n*PARTITURE_W/BEATS_PER_STRIP
        if n%2 == 0:
            pdf.line(x, y0, x, y0 + NOTE_SEPARATION*(N_NOTES-1))
        else:
            pdf.dashed_line(x, y0, x, y0 + NOTE_SEPARATION*(N_NOTES-1),
                            dash_length=1.6*NOTE_SEPARATION,
                            space_length=1.1*NOTE_SEPARATION)

    # Divisores strip
    corner_x = x0-MAX_TITLE_FONT_SIZE*1.3
    pdf.line(corner_x, y0 - STRIP_MARGIN_V,
             pdf.w, y0 - STRIP_MARGIN_V)
    pdf.line(corner_x, y1 + STRIP_MARGIN_V,
             pdf.w, y1 + STRIP_MARGIN_V)
    pdf.line(corner_x, y0 - STRIP_MARGIN_V,
             pdf.l_margin*0.2, y0+(y1-y0)/2)
    pdf.line(pdf.l_margin*0.2, y0+(y1-y0)/2,
             corner_x, y1 + STRIP_MARGIN_V)

    # draw g clef
    if G_CLEF_Y > 0:
        G_CLEF_H = NOTE_SEPARATION * 15
        pdf.image("g_clef.png", x=x0,
                  y=G_CLEF_Y - G_CLEF_H / 1.8,
                  h=G_CLEF_H)

    # draw notes
    # We could use a plotting approach, where each duration can be directly mapped to a distance from the origin


    # Guardar
    pdf.output("delete_me.pdf", "F")

def test_oop_document_drawing():
    doc = MusicBoxPDFGenerator(n_notes=15,
                               pin_width=2,
                               strip_margin=10,
                               beat_width=6,
                               tuning="C",
                               start_note="C")
    doc.generate("test.mid", "delete_me.pdf")


test_oop_document_drawing()
