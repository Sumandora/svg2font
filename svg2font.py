import argparse
import os

import fontforge
import svgelements


parser = argparse.ArgumentParser("svg2font")
parser.add_argument("--firstchar", help="The begin of character-range which holds he svgs",
                    type=int, default=0xE000)
parser.add_argument("--path", help="The path to source svgs from", type=str, required=True)
parser.add_argument("--font_name", help="The name that the font gets", type=str, required=True)
parser.add_argument("--cpp_map", help="Should a c++ unordered_map definition be generated?",
                    type=bool, default=False, action=argparse.BooleanOptionalAction)
parser.add_argument("--correct_direction", help="Should directions be corrected to validate glyphs",
                    type=str, choices=["no", "auto", "always"], default="no")
args = parser.parse_args()

f = fontforge.font()

f.fontname = args.font_name
f.familyname = args.font_name
f.fullname = args.font_name

# The GUI says that TTF prefers when em is a power of 2, so I set it from 1000 to 1024
f.em = 1024

# FontForge doesn't export unset glyphs, so set encoding to unicode so that any firstchar is valid
f.encoding = "UnicodeFull"


def width_and_height_from_svg(file):
    svg = svgelements.SVG.parse(file)

    return svg.width, svg.height


def add_glyph(idx, file):
    glyph = f.createMappedChar(idx)

    # FontForge scales with something that isn't the width/height, just disable it.
    glyph.importOutlines(file, scale=False, correctdir=True, removeoverlap=True)

    # The glyph needs to be scaled manually, so the width/height are needed
    width, height = width_and_height_from_svg(file)

    aspect_ratio = width / float(height)
    # this one would break in theory, because if the glyph is taller than wide then it would
    # over-scale, but since the width of the glyph is adjusted to match the aspect_ratio,
    # that ensures that it never happens
    scale_factor = (f.em / height)

    # glyphs are always `f.em`-units tall, so the width is this:
    glyph_width = round(f.em * aspect_ratio)

    # why does the transform function only take matrices
    # the following statements can be combined in theory, but I had some weirdness in FontForge,
    # when testing these things manually and doing them all at once, the glyph would just be
    # teleported to a random position, which is especially frustrating
    # because the preview does show it at the correct position
    glyph.transform([1, 0, 0, 1, -width / 2, -f.ascent + height / 2])  # move to origin
    glyph.transform([scale_factor, 0, 0, scale_factor, 0, 0])  # scale from origin

    glyph.transform([1, 0, 0, 1, 0, f.ascent - f.em / 2])  # center vertically
    glyph.transform([1, 0, 0, 1, glyph_width / 2, 0])  # center horizontally

    # transformations affect the width of the glyph. In the gui there is a checkbox, this doesn't
    # seem to exist in the python api. Just set the width after doing the transforms
    glyph.width = glyph_width

    # While there are several pitfalls when importing random svgs into a font,
    # one of the easier to fix ones is wrong winding order of paths.
    if args.correct_direction == "always" or \
            (args.correct_direction == "auto" and not glyph.selfIntersects()):
        print("Fixing glyph direction")
        glyph.correctDirection()


# character map for later generating code to map from character to index
cmap = {}

# this is the first "private use area" in unicode, I think this fits the use-case well enough
c = args.firstchar

for root, dirs, files in os.walk(args.path):
    for filename in files:
        if not filename.endswith(".svg"):
            continue
        path = os.path.join(root, filename)
        print("Adding " + str(path) + " as " + str(c))
        add_glyph(c, path)
        # the "+ 1" is the '/' character that comes after the directory
        rel_path = path[len(args.path):]
        if rel_path.startswith('/'):
            rel_path = rel_path[1:]
        cmap[c] = rel_path
        c += 1


f.generate(args.font_name + ".ttf")

if args.cpp_map:
    with open(args.font_name + ".hpp", "w") as f:
        f.write("#pragma once\n\n#include <unordered_map>\n#include <string_view>\n\n")
        f.write("const inline std::unordered_map<std::string_view, std::string_view> cmap{\n")
        for idx in cmap:
            f.write("\t{ \"" + (cmap[idx]) + "\", \"\\u" + f"{idx:04x}" + "\" },\n")
        f.write("};\n")
