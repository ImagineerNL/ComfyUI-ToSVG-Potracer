# version 1.3.1 - Corrected for Recraft SaveSVG compatibility
import torch
import numpy as np
from PIL import Image
import traceback
import nodes # For checking available node classes
from io import BytesIO # Needed for the new output type
import os # For SaveAsSVG
import time # For SaveAsSVG
import folder_paths # For SaveAsSVG

# --- Using Potracer (Pure Python) ---
# NOTE: Assumes 'potracer' installs itself as the 'potrace' module.
# NOTE: Requires 'pypotrace'/'pypotrace-windows' to be UNINSTALLED
# NOTE: Requires 'potracer' to be INSTALLED ('pip install potracer')
try:
    import potrace # Import the module provided by potracer installation
    _ = potrace.Bitmap # Check class access
    potracer_available = True
except ImportError:
    print("\n[PotracerVectorize Error] Failed to import 'potrace' module (from potracer).")
    print("Ensure 'pypotrace' is uninstalled and 'potracer' is installed ('pip install potracer').")
    potracer_available = False
except AttributeError:
    print("\n[PotracerVectorize Error] Imported 'potrace' module, but 'potrace.Bitmap' not found.")
    print("The 'potracer' library structure might be different than expected.")
    potracer_available = False

# Setup turnpolicy mapping if possible
if potracer_available:
    try:
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
         turnpolicy_map = {} # Fallback if constants aren't found
         DEFAULT_TURNPOLICY_STR = "minority" # Default policy string
else:
    turnpolicy_map = {}
    DEFAULT_TURNPOLICY_STR = "minority"

# --- Helper Class for Recraft SaveSVG Compatibility ---
# This class MUST be named SVG to match the type expected by Recraft's SaveSVGNode
class SVG:
    """
    Wrapper class to hold a list of BytesIO objects in a .data attribute.
    This structure is intended to be compatible with Recraft's SaveSVGNode.
    """
    def __init__(self, bytesio_list: list[BytesIO]):
        # Ensure data is always a list, even if input is None or not a list
        if isinstance(bytesio_list, list):
            self.data = bytesio_list
        else:
            self.data = [] # Default to an empty list for invalid input

# --- Main Vectorization Node ---
class PotracerVectorize:
    """
    Potracer Vectorize To SVG (Pure Python) v1.3.1

    Traces a raster image into SVG format using 'potracer'.
    Outputs a single string AND a list of BytesIO objects (wrapped in an SVG class)
    compatible with new ComfyUI Default SaveSVG and old method (renamed SaveAsSVG due to naming issues).
    Includes option to scale output coordinates, width, height, and viewBox.
    Requires 'pypotrace' uninstalled, 'potracer' installed.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # Input definition using user-friendly names and widgets
        if not potracer_available:
             return {"required": {"error": ("STRING", {"default": "ERROR: Failed to load potracer. Check install (uninstall pypotrace, install potracer - see console) & restart ComfyUI.", "multiline": True})}}

        policy_options = list(turnpolicy_map.keys()) if turnpolicy_map else ["black", "white", "left", "right", "minority", "majority"]
        required_inputs = {
            "image": ("IMAGE",),
            "threshold": ("INT", {"default": 128, "min": 0, "max": 255}),
        }
        optional_inputs = {
             "input_foreground": (["White on Black", "Black on White"], {"default": "Black on White"}),
             "turnpolicy": (policy_options, {"default": DEFAULT_TURNPOLICY_STR}),
             "turdsize": ("INT", {"default": 2, "min": 0}),
             "corner_threshold": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.34, "step": 0.01}),
             "zero_sharp_corners": ("BOOLEAN", {"default": False}),
             "opttolerance": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 1.0, "step": 0.01}),
             "optimize_curve": ("BOOLEAN", {"default": True}),
             "foreground_color": ("STRING", {"widget": "color", "default": "#000000"}),
             "stroke_color": ("STRING", {"widget": "color", "default": "#ff0000"}),
             "stroke_width": ("FLOAT", {"default": 0.0, "min": 0.0, "step": 0.5}),
             "background_color": ("STRING", {"widget": "color", "default": "#ffffff"}),
             "no_background": ("BOOLEAN", {"default": False}),
             "output_scale": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 100.0, "step": 0.1}),
        }
        return {"required": required_inputs, "optional": optional_inputs}

    # --- MODIFIED FOR DUAL OUTPUT & RECRAFT COMPATIBILITY ---
    # Output original string AND compatible SVG object for Recraft SaveSVG
    # The type string "SVG" must match the class name `SVG` defined above.
    RETURN_TYPES = ("STRING", "SVG",)
    RETURN_NAMES = ("svg_string_deprecated", "svg_ComfyUI_v0.3.32+",)
    # --- END MODIFICATION ---

    FUNCTION = "vectorize"
    CATEGORY = "IMGNR"

    def vectorize(self, image, threshold, turnpolicy, turdsize, corner_threshold, opttolerance,
                  input_foreground="Black on White", optimize_curve=True,
                  zero_sharp_corners=False,
                  foreground_color="#000000", background_color="#ffffff",
                  stroke_color="#ff0000", stroke_width=0.0,
                  no_background=False,
                  output_scale=1.0,
                  save_svg_status_message=None): # Accept dummy arg for potential future use or other nodes

        # Return empty string and an empty SVG object on error or if potracer not available
        if not potracer_available:
            return ("", SVG([]),) # Ensure SVG([]) is an instance of your SVG class

        image_np = image.cpu().numpy()
        # List to hold individual SVG strings for the first output (joined string)
        batch_svg_strings = []
        # List to hold BytesIO objects for the second output (SVG class instance)
        batch_bytesio_objects = []

        # Process each image in the batch
        for i, single_image_np in enumerate(image_np):
            # Initialize svg_data_for_current_image to a default error SVG string
            # This ensures it has a value if subsequent try-except fails before assignment
            orig_width_temp, orig_height_temp = (single_image_np.shape[1], single_image_np.shape[0]) if single_image_np.ndim >= 2 else (100,100) # crude fallback
            svg_data_for_current_image = f'<svg width="{orig_width_temp}" height="{orig_height_temp}"><desc>Error: Processing failed before SVG generation for image {i}</desc></svg>'

            try:
                # --- Image Preparation ---
                pil_img = Image.fromarray((single_image_np * 255).astype(np.uint8))
                orig_width, orig_height = pil_img.size

                if orig_width <= 0 or orig_height <= 0:
                    error_svg = f'<svg width="1" height="1"><desc>Error: Invalid image dimensions for image {i}</desc></svg>'
                    batch_svg_strings.append(error_svg)
                    batch_bytesio_objects.append(BytesIO(error_svg.encode('utf-8')))
                    continue

                threshold_norm = threshold / 255.0
                # Process current_img_np which is single_image_np
                if single_image_np.ndim == 3: # Assuming CHW or HWC, take first channel if color
                    binary_np = single_image_np[:, :, 0] < threshold_norm if single_image_np.shape[2] > 1 else single_image_np[:,:,0] < threshold_norm
                elif single_image_np.ndim == 2: # Grayscale
                    binary_np = single_image_np < threshold_norm
                else:
                    error_svg = f'<svg width="{orig_width}" height="{orig_height}"><desc>Error: Unexpected image dimensions for image {i}</desc></svg>'
                    batch_svg_strings.append(error_svg)
                    batch_bytesio_objects.append(BytesIO(error_svg.encode('utf-8')))
                    continue

                if input_foreground == "Black on White": # Potrace expects white on black (True=foreground)
                    binary_np = ~binary_np # Invert: True becomes foreground

                if np.all(binary_np) or not np.any(binary_np): # If image is all foreground or all background
                    skipped_svg = f'<svg width="{orig_width}" height="{orig_height}"><desc>Potracer: Skipped blank image {i}</desc></svg>'
                    batch_svg_strings.append(skipped_svg)
                    batch_bytesio_objects.append(BytesIO(skipped_svg.encode('utf-8')))
                    continue

                # --- Parameter Prep ---
                turdsize_int = int(turdsize) if turdsize is not None else 0 # Ensure turdsize is int
                
                # Use actual library constants if turnpolicy_map is populated, otherwise pass string
                policy_arg = turnpolicy_map.get(turnpolicy, turnpolicy) # Fallback to string if key not in map

                alphamax_value_to_use = 1.34 if zero_sharp_corners else corner_threshold
                scale = max(0.01, output_scale) # Ensure scale is positive

                # --- Potracer Processing ---
                bm = potrace.Bitmap(binary_np) # Data is a numpy array, True where foreground
                plist = bm.trace(
                    turdsize=turdsize_int,
                    turnpolicy=policy_arg,
                    alphamax=alphamax_value_to_use,
                    opticurve=optimize_curve,
                    opttolerance=opttolerance
                )

                # --- Manual SVG Generation with Coordinate Scaling ---
                scaled_width = max(1, round(orig_width * scale))
                scaled_height = max(1, round(orig_height * scale))
                svg_header = f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{scaled_width}" height="{scaled_height}" viewBox="0 0 {scaled_width} {scaled_height}">'
                svg_footer = "</svg>"
                background_rect = ""
                bg_color_lower = background_color.lower()

                if not no_background and bg_color_lower != "none" and bg_color_lower != "":
                    background_rect = f'<rect width="100%" height="100%" fill="{background_color}"/>'


                scaled_stroke_width = stroke_width * scale
                stroke_attr = f'stroke="{stroke_color}" stroke-width="{scaled_stroke_width}"' if scaled_stroke_width > 0 and stroke_color.lower() != "none" else 'stroke="none"'
                fill_attr = f'fill="{foreground_color}"' if foreground_color.lower() != "none" else 'fill="none"'
                if fill_attr == 'fill="none"' and stroke_attr == 'stroke="none"': # Fallback if no visible attributes
                    fill_attr = 'fill="black"' # Default to black fill

                all_paths_svg_parts = []
                if plist: # Check if trace returned any paths
                    fill_rule_to_use = "evenodd" # Handles holes correctly for complex shapes
                    for curve in plist:
                        if not (hasattr(curve, 'start_point') and hasattr(curve.start_point, 'x') and hasattr(curve.start_point, 'y')):
                            continue
                        fs = curve.start_point
                        all_paths_svg_parts.append(f"M{fs.x * scale:.2f},{fs.y * scale:.2f}") # Using .2f for float precision

                        if not hasattr(curve, 'segments'):
                            continue
                        for segment in curve.segments:
                            valid_segment = True
                            if not (hasattr(segment, 'is_corner') and hasattr(segment, 'end_point') and hasattr(segment.end_point, 'x') and hasattr(segment.end_point, 'y')):
                                valid_segment = False

                            if valid_segment and segment.is_corner: # Line segment
                                if not (hasattr(segment, 'c') and hasattr(segment.c, 'x') and hasattr(segment.c, 'y')):
                                    valid_segment = False
                                else:
                                    c_x = segment.c.x * scale
                                    c_y = segment.c.y * scale
                                    ep_x = segment.end_point.x * scale
                                    ep_y = segment.end_point.y * scale
                                    all_paths_svg_parts.append(f"L{c_x:.2f},{c_y:.2f}L{ep_x:.2f},{ep_y:.2f}")
                            elif valid_segment: # Bezier curve segment
                                if not (hasattr(segment, 'c1') and hasattr(segment.c1, 'x') and hasattr(segment.c1, 'y') and \
                                        hasattr(segment, 'c2') and hasattr(segment.c2, 'x') and hasattr(segment.c2, 'y')):
                                    valid_segment = False
                                else:
                                    c1_x = segment.c1.x * scale; c1_y = segment.c1.y * scale
                                    c2_x = segment.c2.x * scale; c2_y = segment.c2.y * scale
                                    ep_x = segment.end_point.x * scale; ep_y = segment.end_point.y * scale
                                    all_paths_svg_parts.append(f"C{c1_x:.2f},{c1_y:.2f} {c2_x:.2f},{c2_y:.2f} {ep_x:.2f},{ep_y:.2f}")
                        all_paths_svg_parts.append("Z") # Close path for the current curve

                    if all_paths_svg_parts:
                        path_d_attribute = "".join(all_paths_svg_parts)
                        path_element = f'<path {stroke_attr} {fill_attr} fill-rule="{fill_rule_to_use}" d="{path_d_attribute}"/>'
                        svg_data_for_current_image = svg_header + background_rect + path_element + svg_footer
                    else: # No valid path parts generated
                        svg_data_for_current_image = f'{svg_header}<desc>Potracer: Path data generation failed for image {i}</desc>{svg_footer}'
                else: # No paths found by Potracer
                    svg_data_for_current_image = f'{svg_header}<desc>Potracer: No paths found for image {i}</desc>{svg_footer}'

                # Append generated SVG string to the list for the first output
                batch_svg_strings.append(svg_data_for_current_image)
                # Encode string to UTF-8 bytes, wrap in BytesIO, and append for the second output
                batch_bytesio_objects.append(BytesIO(svg_data_for_current_image.encode('utf-8')))

            except Exception as e:
                # Log detailed error for the specific image
                print(f"\n[PotracerVectorize Error] Exception caught during vectorization for image {i}:")
                try:
                    print(f"  Error Type: {type(e).__name__}")
                    print(f"  Error Representation: {repr(e)}")
                except Exception as inner_e:
                    print(f"  Failed to print basic exception info: {repr(inner_e)}")
                print(f"  --- Full Traceback ---"); traceback.print_exc(); print(f"  --- End Traceback ---")
                # Create an error SVG for this specific image
                error_svg_content = f'<svg width="100" height="100"><desc>Error processing image {i}: {type(e).__name__} - {str(e).replace("<", "&lt;").replace(">", "&gt;")}</desc></svg>'
                batch_svg_strings.append(error_svg_content)
                batch_bytesio_objects.append(BytesIO(error_svg_content.encode('utf-8')))
                # Continue to the next image in the batch rather than returning for all
                continue

        # --- After processing all images in the batch ---

        # Prepare the first output (single string, joined if batch)
        output_string_joined = "\n".join(batch_svg_strings)

        # Prepare the second output (list of BytesIO wrapped in our SVG class)
        svg_output_object = SVG(batch_bytesio_objects)

        return (output_string_joined, svg_output_object,)

class SaveAsSVG: # Basic Save SVG node, similar to ComfyUI-ToSVG
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output" # Required by some UI elements if saving images

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # This node saves the old STRING output, not the new ComfyUI v0.3.32+ SVG object.
                "svg_string_data": ("STRING", {"forceInput": True, "multiline": True}),
                "filename_prefix": ("STRING", {"default": "SVG/ComfyUI_SVG"}),
            },
            "optional": {
                "append_timestamp": ("BOOLEAN", {"default": True}),
                # "custom_output_path": ("STRING", {"default": "", "multiline": False}), # Less common, usually default output path is used
            }
        }

    CATEGORY = "IMGNR" # Or your preferred category
    RETURN_TYPES = () # This node does not return any data to other nodes
    OUTPUT_NODE = True # Indicates this node is an output node
    FUNCTION = "save_svg_file"

    def generate_unique_filename(self, prefix, timestamp_active=False):
        # Generates a unique filename, optionally with a timestamp.
        if timestamp_active:
            timestamp_str = time.strftime("%Y%m%d-%H%M%S")
            # Find a unique counter if multiple saves happen in the same second
            counter = 0
            base_filename = f"{prefix}_{timestamp_str}"
            output_filename = f"{base_filename}.svg"
            while os.path.exists(os.path.join(self.output_dir, output_filename)):
                counter += 1
                output_filename = f"{base_filename}_{counter}.svg"
            return output_filename
        else:
            # Find a unique counter if no timestamp
            counter = 0
            base_filename = prefix
            output_filename = f"{base_filename}.svg"
            while os.path.exists(os.path.join(self.output_dir, output_filename)):
                counter += 1
                output_filename = f"{base_filename}_{counter}.svg"
            return output_filename


    def save_svg_file(self, svg_string_data, filename_prefix="SVG/ComfyUI_SVG", append_timestamp=True):
        # Ensure the output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        # Generate a unique filename
        unique_filename = self.generate_unique_filename(filename_prefix, append_timestamp)
        final_filepath = os.path.join(self.output_dir, unique_filename)

        try:
            with open(final_filepath, "w", encoding='utf-8') as svg_file:
                svg_file.write(svg_string_data)
            print(f"[SaveAsSVG] SVG saved to: {final_filepath}")
            # Standard way to return UI info for file outputs in ComfyUI
            return {"ui": {"text": [f"Saved SVG: {unique_filename}"], "filename": [unique_filename], "subfolder": [""] , "type": [self.type]}}

        except Exception as e:
            print(f"[SaveAsSVG Error] Failed to save SVG: {e}")
            traceback.print_exc()
            return {"ui": {"text": [f"Error saving SVG: {e}"], "filename": [], "subfolder": [] , "type": []}}

# --- ComfyUI Node Mappings ---
NODE_CLASS_MAPPINGS = {
    "PotracerVectorize": PotracerVectorize,
    "SaveAsSVG Potracer (Temporary Fix)": SaveAsSVG, # Renamed to avoid conflict
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PotracerVectorize": "Potracer to SVG",
    "SaveAsSVG Potracer (Temporary Fix)": "Save SVG String (Potracer Temp Fix)",
}
