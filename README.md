# svg2font

## Guide

### Step 1: Gather SVGs
Create a directory that only contains the icons that you want in the font.

### Step 2 (optional): Simplify SVGs
This step is not needed, but complex SVGs might confuse FontForge. You can use GIMP and Inkscape, however to my knowledge only Inkscape can be automated.

Run the following command:
```shell
inkscape icon.svg --actions="select-all;path-simplify;path-combine;path_flatten" --export-type="svg"
```
This command will produce a [filename]_out.svg file, which should have less render instructions.

### Step 3: Running svg2font
You may call svg2font like this:
```shell
python svg2font.py --path my_svgs --font_name my_cool_font
```

You now have a font that contains all your svgs, starting at \uE000.
The stdout should give you a clear idea of where each icon is.
You can append `--cpp_map` if you desire to use the font in a C++ app, and you want a header that keeps track of unicode indices.
