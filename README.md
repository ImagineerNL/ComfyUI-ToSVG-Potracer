STILL WIP; DO NOT USE YET!!


Traces a raster image (IMAGE) into an SVG vector graphic using the 'potracer' pure Python library for POTRACE. This SVG conversion is great for BW logo's, text, etc.

The input image should only use the two colors black and white. If other pixel values appear in the input, they will be converted to black and white using a simple threshold method. 

Parameters:
 - threshold: Brightness cutoff (0-255) for binarization to B/W.
 - input_foreground = 'Black on White' or 'White on Black' 
 - turnpolicy: how to resolve ambiguities in path decomposition (Default: minority)
 - turdsize: suppress speckles of up to this many pixels (default: 2)
 - corner_treshold: smaller values = sharper corners (default: 1)
 - zero_sharp_corners: force al corners to be fluid. 
     (same as corner_treshold = 1.34)
 - opttolerance: curve optimization tolerance (default: 0.2)
 - optimize_curve: curve optimization, joins adjacent Bezier curve segments where possible. Reduces filesize and points (default: true)

 - foreground_color: defines foreground color after trace #rrggbb (default: #000000)
 - stroke_color: defines stroke color after trace #rrggbb (default: #ff0000)
 - stroke_width: sets a stroke width/outline for the traced shapes (default: 0.0)
 - background_color: defines background color after trace #rrggbb (default: #ffffff)
 - no_background removes the background color.

Output:
 - svg_strings: a list of strings to be converted to svg shape. 
 Requires ComfyUI-ToSVG --> SaveSVG to save the SVGfile.

 Sources, Love and Inspiration:
 - Potrace: https://potrace.sourceforge.net/
 - Potracer: https://github.com/tatarize/potrace
 - ComfyUI-ToSVG: https://github.com/Yanick112/ComfyUI-ToSVG
 