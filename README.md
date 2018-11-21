# Programmable Music Box Paper Strip Generator

[(Name subject to change)](http://steins-gate.wikia.com/wiki/Future_Gadgets#Future_Gadget_.238_.27Phone_Microwave.27_.28name_subject_to_change.29)

This project was inspired by the [Kikkerland Music box](https://kikkerland.com/products/make-your-own-music-box-kit), which is a neat programmable, paper strip based, music box. You can see some cool examples of it being used [here](https://www.youtube.com/watch?v=SXT2ClngEsw&t=197s) and [here](https://www.youtube.com/watch?v=g9tldJFc-4M).

The paper strip goes through the box and each perforation triggers a specific note.

## What does this do?

The product comes with some [paper strips](https://cdn.shopify.com/s/files/1/1140/3964/products/1200R_2_1024x1024.jpg?v=1507319874) and a perforating tool that you're supposed to use to manually insert music. To avoid mistakes, they include a printed pattern where you can draw like it was a pentagram. 

This project uses MIDI files as the source of musical notes, allowing you to precisely create complex melodies for the music box. You can either create your files or obtain them from any source.

## Installation

1. Install python3 and pip3
1. Clone or download the repository
1. Using `pip3` install the submodule under `lib/python3-midi` by doing ```$ pip3 install lib/python3-midi```
1. Install the other requirements with `$ pip3 install -r requirements`

## Usage

```shell
$ python main.py [-h] [--paper_size PAPER_SIZE PAPER_SIZE]
               [--pin_number PIN_NUMBER] [--pinwidth PINWIDTH]
               [--beatwidth BEATWIDTH] [--strip_padding STRIP_PADDING]
               [--strip_separation STRIP_SEPARATION]
               MIDI_FILE SONG_TITLE SONG_AUTHOR [OUTPUT_DIR]

MIDI Music paper strips generator for Kikkerland's music box

positional arguments:
  MIDI_FILE             MIDI file to parse
  SONG_TITLE            Title of the song
  SONG_AUTHOR           Author of the song
  OUTPUT_DIR            Directory where to put the output

optional arguments:
  -h, --help            show this help message and exit
  --paper_size PAPER_SIZE PAPER_SIZE, -s PAPER_SIZE PAPER_SIZE
                        (mm) Size of the paper where to print
  --pin_number PIN_NUMBER, -n PIN_NUMBER
                        Number of notes the box can reproduce
  --pinwidth PINWIDTH, -pw PINWIDTH
                        (mm) Physical separation between note pins
  --beatwidth BEATWIDTH, -bw BEATWIDTH
                        (mm) Size of eighth notes. Affects song speed
  --strip_padding STRIP_PADDING, -sm STRIP_PADDING
                        (mm) Additional strip width
  --strip_separation STRIP_SEPARATION, -ss STRIP_SEPARATION
                        (mm) Separation between strips
```

## Examples

```shell
$ python main.py "examples/Let it Go - Frozen/Let it go.mid" 
```
[Result](examples/Let it Go - Frozen/output.pdf)


## Features

* Executable via command line
* Supports both Kikkerland's [15](https://cdn.shopify.com/s/files/1/1140/3964/products/1200_music_box_kit_contents-noshadow.jpg?v=1507319874) and [30](https://musicboxmaniacs.com/static/mbm_core/img/bnr/gi30.jpg) note boxes
* Highly customizable for other boxes
* Highly customizable paper settings
* Supports standard `.mid` [MIDI](https://en.wikipedia.org/wiki/MIDI) files
* Printer-ready, high resolution PDF output

## TODO

* More options on how to parse MIDI files
	* Musical scale fitting for non-chromatic boxes
	* Outlier notes cropping or circular transposition
	* Instrument selection or merging
	* Lots of other options one could require to know what to do with complex midi files
* Remove empty strip after music end
* Accurate note labels (Kikkerland's original notes are **wrong**, as **C** is actually **A#**)
* GUI? Web service?

## Known Issues

* The logic to draw the G clef is weird, impractical and buggy for big boxes
* 

## License

This project is distributed under the **GNU GPLv3** license.