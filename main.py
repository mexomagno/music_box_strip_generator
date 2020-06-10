# coding=utf-8

"""
Contains all the logic to generate the paper strips
"""
import os
import argparse
import yaml
from musicbox.box import MusicBox
from musicbox.pdf import Renderer
import midi



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
    ap.add_argument("--box", "-b", help="Music box to use, from musicboxes.yml", type=int, default=0)
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
    settings_file = "musicboxes.yml"
    if not os.path.isfile(settings_file) or not settings_file.strip().lower().endswith(".yml"):
        raise IOError("No valid music boxes config file could be found!!")

    # Try to parse file settings
    settings_dict = yaml.load(open(settings_file))
    print("Loaded '{}'".format(settings_file))
    settings_version = settings_dict["version"]
    print("Settings file version: {version}\n"
          "Music boxes configured: {n_boxes}"
          .format(version=settings_version,
                  n_boxes=len(settings_dict["boxes"])))

    return settings_dict['boxes']


def load_box(index = 0):
    boxes = load_music_boxes()
    return boxes[index]


def main():
    # Get and parse args
    parsed_args = parse_args()
    # Check if selected box exists
    box_def = load_box(parsed_args.box)
    musicbox = MusicBox(**box_def)
    print("\n", musicbox)

    # Generate instance
    doc = Renderer(musicbox,
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
