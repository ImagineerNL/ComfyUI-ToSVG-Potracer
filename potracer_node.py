# potracer version - Final Code v1.0 (initial publish)

import torch
import numpy as np
from PIL import Image
import traceback
import nodes # For checking available node classes

# --- Using Potracer (Pure Python) ---
# NOTE: Assumes 'potracer' installs itself as the 'potrace' module.
# NOTE: Requires 'pypotrace'/'pypotrace-windows' to be UNINSTALLED
# NOTE: Requires 'potracer' to be INSTALLED ('pip install potracer')
try:
    import potrace # Import the module provided by potracer installation
    _ = potrace.Bitmap # Verify class access
    potracer_available = True
except ImportError:
    print("\n[PotracerVectorize Error] Failed to import 'potrace' module (from potracer).")
    print("Ensure 'pypotrace' is uninstalled and 'potracer' is installed ('pip install potracer').")
    potracer_available = False
except AttributeError:
    print("\n[PotracerVectorize Error] Imported 'potrace' module, but 'potrace.Bitmap' not found.")
    print("The 'potracer' library structure might be different than expected.")
    potracer_available = False

# Check if the 'SaveSVG' node class is available
is_save_svg_available = False
SAVE_SVG_CLASS_NAME = "SaveSVG"
if potracer_available: # Only check if main dependency is there
    try:
        if hasattr(nodes, 'NODE_CLASS_MAPPINGS') and SAVE_SVG_CLASS_NAME in nodes.NODE_CLASS_MAPPINGS:
            is_save_svg_available = True
        else:
            is_save_svg_available = False
    except Exception as e:
        is_save_svg_available = False
        print(f"[PotracerVectorize Warning] An error occurred while checking for node '{SAVE_SVG_CLASS_NAME}': {e}")


# Setup turnpolicy mapping if possible
if potracer_available:
    try:
        # Map UI strings to internal library constants if they exist
        turnpolicy_map = {
            "minority": potrace.POTRACE_TURNPOLICY_MINORITY,
            "black": potrace.POTRACE_TURNPOLICY_BLACK,
            "white": potrace.POTRACE_TURNPOLICY_WHITE,
            "left": potrace.POTRACE_TURNPOLICY_LEFT,
            "right": potrace.POTRACE_TURNPOLICY_RIGHT,
            "majority": potrace.POTRACE_TURNPOLICY_MAJORITY,
        }
        DEFAULT_TURNPOLICY_STR = "minority"
    except AttributeError:
         # Fallback if constants aren't found (use strings)
         turnpolicy_map = {}
         DEFAULT_TURNPOLICY_STR = "minority"
else:
    # Fallback if library failed import
    turnpolicy_map = {}
    DEFAULT_TURNPOLICY_STR = "minority"


class PotracerVectorize:
    """
    Potracer Vectorize To SVG (Pure Python) v1.0

    Traces a raster image into a single-path SVG using 'potracer'.
    Requires 'pypotrace' uninstalled, 'potracer' installed.
    Advises installing 'ComfyUI-ToSVG' if SaveSVG node is missing.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        if not potracer_available:
             return {"required": {"error": ("STRING", {"default": "ERROR: Failed to load potracer. Check install (uninstall pypotrace, install potracer - see console) & restart ComfyUI.", "multiline": True})}}

        policy_options = list(turnpolicy_map.keys()) if turnpolicy_map else ["black", "white", "left", "right", "minority", "majority"]

        # Define node inputs
        required_inputs = {
            "image": ("IMAGE",),
            "threshold": ("INT", {"default": 128, "min": 0, "max": 255}), # Binarization threshold
        }
        optional_inputs = {
             "input_foreground": (["White on Black", "Black on White"], {"default": "Black on White"}), # Controls input inversion
             "turnpolicy": (policy_options, {"default": DEFAULT_TURNPOLICY_STR}), # Algorithm option
             "turdsize": ("INT", {"default": 2, "min": 0}), # Algorithm option (min speckle size)
             "corner_threshold": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.34, "step": 0.01}), # Algorithm option (alphamax)
             "zero_sharp_corners": ("BOOLEAN", {"default": False}), # Overrides corner_threshold if True (uses 1.34)
             "opttolerance": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 1.0, "step": 0.01}), # Algorithm option
             "optimize_curve": ("BOOLEAN", {"default": True}), # Algorithm option (opticurve)
             # "separate_shapes" removed for reliable hole rendering
             "foreground_color": ("STRING", {"widget": "color", "default": "#000000"}), # SVG path fill color
             "stroke_color": ("STRING", {"widget": "color", "default": "#ff0000"}), # SVG path stroke color
             "stroke_width": ("FLOAT", {"default": 0.0, "min": 0.0, "step": 0.5}), # SVG path stroke width
             "background_color": ("STRING", {"widget": "color", "default": "#ffffff"}), # SVG background color (use "none" for transparent)
             "no_background": ("BOOLEAN", {"default": False}), # If true, prevents background color rect
        }

        # Conditionally add info text if SaveSVG node class is missing
        if not is_save_svg_available:
            optional_inputs["save_svg_status_message"] = ("STRING", {
                "default": "NOTE: 'SaveSVG' node not found.\nFor saving install:\nhttps://github.com/Yanick112/ComfyUI-ToSVG",
                "multiline": True # Displays as a multi-line text box
            })

        return {"required": required_inputs, "optional": optional_inputs}

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("svg_strings",)
    FUNCTION = "vectorize"
    CATEGORY = "💎TOSVG" # Set desired category
    
    def vectorize(self, image, threshold, turnpolicy, turdsize, corner_threshold, opttolerance,
                  input_foreground="Black on White", optimize_curve=True,
                  zero_sharp_corners=False,
                  foreground_color="#000000", background_color="#ffffff",
                  stroke_color="#ff0000", stroke_width=0.0,
                  no_background=False,
                  save_svg_status_message=None): # dummy arg if save_svg not installed

        if not potracer_available: return ([],)

        image_np = image.cpu().numpy()
        svg_strings = []

        # Process each image in the batch
        for i, img in enumerate(image_np):
            plist = None
            try:
                # --- Image Preparation ---
                pil_img = Image.fromarray((img * 255).astype(np.uint8))
                width, height = pil_img.size
                threshold_norm = threshold / 255.0
                current_img_np = image_np[i]
                # Create initial mask: True = Dark, False = Light
                if current_img_np.ndim == 3: binary_np = current_img_np[:, :, 0] < threshold_norm
                elif current_img_np.ndim == 2: binary_np = current_img_np < threshold_norm
                else: svg_strings.append(f'<svg width="{width}" height="{height}"><desc>Error: Unexpected image dimensions</desc></svg>'); continue
                # Apply Inversion Logic based on user selection
                if input_foreground == "Black on White": binary_np = ~binary_np
                # Skip if blank
                if np.all(binary_np) or not np.any(binary_np): svg_strings.append(f'<svg width="{width}" height="{height}"><desc>Potracer: Skipped blank image</desc></svg>'); continue

                # --- Parameter Prep ---
                try: turdsize_int = int(turdsize)
                except ValueError: turdsize_int = 0
                policy_arg = turnpolicy # Use string argument
                if zero_sharp_corners: alphamax_value_to_use = 1.34
                else: alphamax_value_to_use = corner_threshold

                # --- Potracer Processing ---
                bm = potrace.Bitmap(binary_np) # Pass final mask where True = desired foreground
                plist = bm.trace( turdsize=turdsize_int, turnpolicy=policy_arg, alphamax=alphamax_value_to_use, opticurve=optimize_curve, opttolerance=opttolerance )

                # --- Manual SVG Generation (Flat Path) ---
                svg_header = f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
                svg_footer = "</svg>"
                background_rect = ""
                bg_color_lower = background_color.lower()
                # Add background rect ONLY if no_background is False AND color is not "none"/empty
                if not no_background and bg_color_lower != "none" and bg_color_lower != "":
                     background_rect = f'<rect width="{width}" height="{height}" fill="{background_color}"/>'
                # Determine fill/stroke attributes once
                stroke_attr = f'stroke="{stroke_color}" stroke-width="{stroke_width}"' if stroke_width > 0 and stroke_color.lower() != "none" else 'stroke="none"'
                fill_attr = f'fill="{foreground_color}"' if foreground_color.lower() != "none" else 'fill="none"'
                # Fallback fill if both fill/stroke are none
                if fill_attr == 'fill="none"' and stroke_attr == 'stroke="none"': fill_attr = 'fill="black"'

                all_paths_svg = "" # String to hold the single path element
                path_parts = [] # Build single list for all parts

                if plist: # Check if trace returned curves
                    fill_rule_to_use = "evenodd" # Use evenodd for combined path to handle holes
                    # Iterate through curves and segments to build path data for single path element
                    for curve_idx, curve in enumerate(plist):
                         # Safety checks for curve/segment data integrity
                         if not (hasattr(curve, 'start_point') and hasattr(curve.start_point, 'x') and hasattr(curve.start_point, 'y')): continue
                         fs = curve.start_point; path_parts.append(f"M{fs.x},{fs.y}")
                         if not hasattr(curve, 'segments'): continue
                         for seg_idx, segment in enumerate(curve.segments):
                            valid_segment=True
                            if not (hasattr(segment, 'is_corner') and hasattr(segment, 'end_point') and hasattr(segment.end_point, 'x') and hasattr(segment.end_point, 'y')): valid_segment=False
                            if valid_segment and segment.is_corner: # Line segments
                                if not (hasattr(segment, 'c') and hasattr(segment.c, 'x') and hasattr(segment.c, 'y')): valid_segment=False
                                else: path_parts.append(f"L{segment.c.x},{segment.c.y}L{segment.end_point.x},{segment.end_point.y}")
                            elif valid_segment: # Bezier curve segments
                                if not (hasattr(segment, 'c1') and hasattr(segment.c1, 'x') and hasattr(segment.c1, 'y') and hasattr(segment, 'c2') and hasattr(segment.c2, 'x') and hasattr(segment.c2, 'y')): valid_segment=False
                                else: path_parts.append(f"C{segment.c1.x},{segment.c1.y} {segment.c2.x},{segment.c2.y} {segment.end_point.x},{segment.end_point.y}")
                         path_parts.append("z") # Close path for the curve

                    # Assemble the <path> element if data was generated
                    if path_parts:
                        all_paths_svg = f'<path {stroke_attr} {fill_attr} fill-rule="{fill_rule_to_use}" d="{"".join(path_parts)}"/>'
                        # Combine final SVG string
                        svg_data = svg_header + background_rect + all_paths_svg + svg_footer
                    else: # Handle cases where path generation failed internally
                         svg_data = f'{svg_header}<desc>Potracer: Path data generation failed</desc>{svg_footer}'
                else: # Handle cases where trace returned no curves
                    svg_data = f'{svg_header}<desc>Potracer: No paths found</desc>{svg_footer}'

                # Add the final SVG string to the list
                svg_strings.append(svg_data)

            # --- Error Handling ---
            except Exception as e:
                # Print detailed error traceback and context
                print(f"\n[PotracerVectorize Error] Exception caught during vectorization for image {i+1} (0-based index {i}):")
                try: print(f"  Error Type: {type(e).__name__}"); print(f"  Error Representation: {repr(e)}")
                except Exception as inner_e: print(f"  Failed to print basic exception info: {repr(inner_e)}")
                print(f"  --- Full Traceback ---"); traceback.print_exc(); print(f"  --- End Traceback ---")
                current_turdsize = turdsize_int if 'turdsize_int' in locals() and turdsize_int is not None else turdsize
                print(f"  Parameters: threshold={threshold}, turnpolicy={turnpolicy}, turdsize={current_turdsize}, "
                      f"corner_threshold={corner_threshold}, opttolerance={opttolerance}, optimize_curve={optimize_curve}, input_foreground='{input_foreground}', "
                      f"zero_sharp_corners={zero_sharp_corners}, " # separate_shapes removed
                      f"foreground_color='{foreground_color}', background_color='{background_color}', "
                      f"stroke_color='{stroke_color}', stroke_width={stroke_width}, no_background={no_background}")
                print("-" * 20)
                # Return empty list on any error during processing
                return ([],)

        # Return the list of generated SVG strings
        return (svg_strings,)

# --- ComfyUI Node Mappings ---
NODE_CLASS_MAPPINGS = {
    # Register the node class
    "PotracerVectorize": PotracerVectorize
}
NODE_DISPLAY_NAME_MAPPINGS = {
    # Set the desired display name
    "PotracerVectorize": "Potracer to SVG"
}