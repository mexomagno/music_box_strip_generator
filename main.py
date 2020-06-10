# coding=utf-8

"""
Contains all the logic to generate the paper strips
"""
import os
import argparse
import yaml
from musicbox.box import MusicBox
from musicbox.pdf import Renderer
from musicbox.midi import Parser


def parse_args(parsed_boxes):
    def _midi_file(s):
        # check if exists
        if not os.path.exists(s):
            raise argparse.ArgumentTypeError("File '{}' doesn't exist".format(s))
        _, ext = os.path.splitext(s)
        if ext.lower() != ".mid":
            raise argparse.ArgumentTypeError("Unsupported extension: '{}'. Use a midi file only".format(s))
        # Check if valid midi file
        if not Parser.file_is_valid(s):
            raise argparse.ArgumentTypeError("Unable to process midi file")

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

    def _existing_box(s):
        if not 1 <= int(s) <= len(parsed_boxes):
            raise argparse.ArgumentTypeError(f'Box index {s} out of range ({len(parsed_boxes)} boxes were found in definition)')
        return int(s)

    ap = argparse.ArgumentParser(description="MIDI Music paper strips generator for Kikkerland's music box")
    ap.add_argument("midi_file", metavar="MIDI_FILE", type=_midi_file, help="MIDI file to parse")
    ap.add_argument("song_title", metavar="SONG_TITLE", type=_title_string, help="Title of the song")
    ap.add_argument("song_author", metavar="SONG_AUTHOR", type=_title_string, help="Author of the song")
    ap.add_argument("output_dir", metavar="OUTPUT_DIR", type=_real_dir, help="Directory where to put the output",
                    nargs="?")

    ap.add_argument("--paper_size", "-s", help="(mm) Size of the paper where to print", nargs=2, default=[215.9, 279.4],
                    type=float)
    ap.add_argument("--box", "-b", help="Music box to use, from musicboxes.yml", type=_existing_box, default=0)
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
    print(f"Settings file version: {settings_dict['version']}\n")

    print("Definitions found:")
    [ print(f"\t{index+1}: {box['meta']['description']}") for index, box in enumerate(settings_dict['boxes']) ]

    print(f"Total boxes: {len(settings_dict['boxes'])}\n")

    return settings_dict['boxes']


def main():
    # Get and parse args
    parsed_boxes = load_music_boxes()
    parsed_args = parse_args(parsed_boxes)
    # Check if selected box exists
    box_def = parsed_boxes[parsed_args.box - 1]
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
