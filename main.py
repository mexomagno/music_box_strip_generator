# coding=utf-8

"""
Basic example of usage
"""

from fpdf import FPDF
from fpdf import Template


class StripGenerator:
    def __init__(self, tuning="A#", scale="major", first_note="A#4", note_count=15, key_distance_mm=4):
        self.midi_file = None
        pass

    def load_midi(self, midi_file):
        # prepare midi file
        new_midi = _MidiProcessor.fit_to_tuning(midi_file, self.tuning)
        min_delay = 10 # Calculate from hole size and tempo
        new_midi = _MidiProcessor.round_beats(new_midi, min_delay)
        # Save to instance variable
        self.midi_file = new_midi

    def to_pdf(self, output_path, format):
        # Draw PDF
        pdf_doc = _PrintableStrips.generate(midi_file=self.midi_file,
                                            output_path=output_path,
                                            format=format)
        pass

class _MidiProcessor:
    @staticmethod
    def fit_to_tuning(midi_file, tuning):
        """ Force chromatism into tuning """
        pass

    @staticmethod
    def round_beats(midi_file, min_delay):
        """ Clump/summarize notes that repeat too fast """
        pass


class _PrintableStrips:
    DEFAULT_DOCUMENT_SIZE = (215.9, 279.4)
    def __init__(self, d):
        pass

    def generate(self, midi_file, output_path, format):
        # Create PDF document components
        pdf_parts_list = list()
        # Create title
        pdf_parts_list.append(_PdfTitle(position=()))

        


class _PdfPart:
    def __init__(self, position, center_vertical, center_horizontal):
        self.position = position
        self.center_vertical = center_vertical
        self.center_horizontal = center_horizontal

class _PdfTitle(_PdfPart):
    def __init__(self, text, font_size, font):
        pass

class _PdfStrip(_PdfPart):
    pass

def prepare_text_for_pdf(s):
    if isinstance(s, str):
        try:
            return s.decode("utf-8").encode("latin1")
        except UnicodeEncodeError as e:
            print ("Error encoding: {}".format(e))
            return s.decode("utf-8").encode("cp1252")
    return s


def main():
    # Create musical strip. Settings depend on actual musical box
    strip = StripGenerator(tuning="A#",
                           scale="major",
                           first_note="A#4",
                           note_count=15,
                           key_distance_mm=4)
    # Load and parse midi file
    strip.load_midi(midi_file="midi_file.mid")
    # Generate printable strips
    strip.to_pdf(pdf_path="path.pdf",
                      paper_format="letter")



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


def test_fpdf_drawing():
    # Crear wea
    pdf = FPDF("p", "mm", (215.9, 279.4))
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
    NOTE_OFFSET = 0
    NOTE_SEPARATION = 2
    BEATS_PER_STRIP = 30
    FIRST_STRIP_OFFSET = 20
    x0 = pdf.l_margin + FIRST_STRIP_OFFSET
    x1 = pdf.w - pdf.r_margin
    PARTITURE_W = x1-x0
    y0 = 30
    y1 = y0 + NOTE_SEPARATION*(N_NOTES-1)
    # Dibujar líneas horizontales notas
    pdf.set_font("arial", "B", 7)
    for n in range(N_NOTES):
        y = y0 + n*NOTE_SEPARATION
        if len(G_CLEF_NOTES) != 0 and ''.join(reversed(NOTE_NAMES))[(n+len(NOTE_NAMES)-(N_NOTES%len(NOTE_NAMES)))%len(NOTE_NAMES)] == G_CLEF_NOTES[-1]:
            current_line_width = pdf.line_width
            pdf.set_line_width(1)
            pdf.line(x0+pdf.line_width/2, y, x1-pdf.line_width/2, y)
            pdf.set_line_width(current_line_width)
            if (G_CLEF_NOTES[-1] == "G"):
                # draw G clef
                G_CLEF_H = NOTE_SEPARATION*15
                pdf.image("g_clef.png", x=x0,
                          y=y - G_CLEF_H/1.8,
                          h=G_CLEF_H)
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
    pdf.line(x0-MAX_TITLE_FONT_SIZE*2, y0 - STRIP_MARGIN_V,
             pdf.w, y0 - STRIP_MARGIN_V)
    pdf.line(x0 - MAX_TITLE_FONT_SIZE * 2, y1 + STRIP_MARGIN_V,
             pdf.w, y1 + STRIP_MARGIN_V)
    # Guardar
    pdf.output("delete_me.pdf", "F")

test_fpdf_drawing()
