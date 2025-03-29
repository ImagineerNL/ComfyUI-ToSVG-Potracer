- [UNofficial ComfyUI Potrace(r) SVG conversion](#unofficial-comfyui-potracer-svg-conversion)
  - [Comparing Vtracer and Potracer](#comparing-vtracer-and-potracer)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Workflow](#workflow)
  - [Tested on](#tested-on)
  - [Sources, Shoutouts, Love and Inspiration](#sources-shoutouts-love-and-inspiration)
  - [To Do](#to-do)
- [***Disclaimer***](#disclaimer)


# UNofficial ComfyUI Potrace(r) SVG conversion
This is my First ever (public) ComfyUI node.
While tested thoroughly, and as with all custom nodes, USE AT YOUR OWN RISK.

I created this custom node because i wasn't getting the results I wanted when using the [ComfyUI-ToSVG node by Yanick112](https://github.com/Yanick112/ComfyUI-ToSVG). 
This is NOT a complaint; his work is great and inspired me. <br>
ComfyUI-toSVG implements the VTracer logic, and this works great for multicolor and detailed images. <br>
For logo's, text, etc. I found Potrace SVG conversion better suited, with the caveat that it only handles 2 colors; a Foreground and Background. <br>
I also found Potrace better more optimized shapes with less points and thus requires less to no cleanup when loading into vector design software. 

Potracer to SVG node traces a raster image (IMAGE) into an SVG vector graphic using the 'potracer' pure Python library for POTRACE.

## Comparing Vtracer and Potracer
While each user and route will have their specific usecase, my usecase is creating designs for Vinylcutters and logo's. This usecase requires sharp images, fluid shapes and clear separation of fore and background.

![Vtracer vs Potracer](img/Vtracer-v-Potracer_combined.jpg)
- *Left side: Vtracer (Green, Top) shows significantly more artifacts, hard edges or straight lines, and irregular traces compared to Potracer (Blue, Bottom), which stays true to the original form.*
- *Right side: Vtracer has significantly more vector points compared to the optimized Potracer version.*
- For the usecases where Vtracer suits best, go check out (https://github.com/Yanick112/ComfyUI-ToSVG/), where Yanick explains the workings in detail. 

## Installation
Due to both usecases for SVG export are very valid when working with ComfyUI, I opted to keep the naming and category alike for easier navigation.
>***note: This node requires Yanick112's ComfyUI-ToSVG --> SaveSVG node to save the SVGfile. See his repository for install instructions***

1. Navigate to your /ComfyUI/custom_nodes/ folder.
2. Run the following command to clone the repository:

    git clone https://github.com/ImagineerNL/ComfyUI-ToSVG-Potracer


3. Navigate to your ComfyUI-ToSVG-Potracer folder.
    - Command for Portable/venv:
    
            path/to/ComfUI/python_embeded/python.exe -s -m pip install -r requirements.txt

    - Command for system Python:

            pip install -r requirements.txt

Enjoy setting up your ComfyUI-ToSVG tool! If you encounter any issues or need further help, feel free to reach out.

## Usage
The input image should only use the two colors black and white. If other pixel values appear in the input, they will be converted to black and white using a simple threshold method. 
Outputs svg strings as 1 flat shape (as a compound path). Should you want to adjust the shapes by hand, currently, when you release the path in vector design software, the 'internal openings' become filled shapes. This is easy to fix using the boolean tools and substract. My main usecase is Silhouette Studio for vinylcutting and especially with 'zero_sharp_corners' set to true, i don't need to do any postprocessing on the shape.  

![alt text](img/ToSVG-Potracer.jpg)

| Parameter                	| Usage                                                                                                  	| Default        	|
|--------------------------	|--------------------------------------------------------------------------------------------------------	|:----------------:	|
| **threshold**            	| *Brightness cutoff (0-255) for binarization to B/W.*                                                   	| 128            	|
| **input_foreground**    	| *Defines if the input image is a Black object on White background or White on Black background*        	| Black on White 	|
| **turnpolicy**          	| *How to resolve ambiguities in path decomposition*                                                     	| minority       	|
| **turdsize**            	| *Suppress speckles of up to this many pixels*                                                          	| 2              	|
| **corner_treshold**     	| *Smaller values = sharper corners*                                                                     	| 1              	|
| **zero_sharp_corners**  	| *Forces al corners to be fluid. (same as corner_treshold = 1.34)*                                      	| false          	|
| **opttolerance**        	| *Curve optimization tolerance*                                                                         	| 0.2            	|
| **optimize_curve**      	| *Curve optimization, joins adjacent Bezier curve segments where possible. Reduces filesize and points* 	| true           	|
| **foreground_color**    	| *Defines foreground color after trace #rrggbb*                                                         	| #000000        	|
| **stroke_color**        	| *Defines stroke color after trace #rrggbb*                                                             	| #ff0000        	|
| **stroke_width**        	| *Sets a stroke width/outline for the traced shapes*                                                    	| 0.0            	|
| **background_color**    	| *Defines background color after trace #rrggbb*                                                         	| #ffffff        	|
| **no_background**       	| *Removes the background color.*                                                                        	| false          	|
||
||
| ***Output***                    | 
| **svg_strings**           | *a list of strings to be converted to svg shape. <br> **Note: Requires ComfyUI-ToSVG --> SaveSVG to save the SVGfile.*** 
 

## Workflow

||
| :-------------: |
| ![alt text](img/ComfyUI-ToSVG-Potracer_Reference_Workflow.jpg ) |
| *The above image is just a visualisation, does not contain workflow* |
||
| <img src="ComfyUI_ToSVG_Potrace_Workflow.png" alt="ComfyUI_ToSVG_Potrace_Workflow.png" width="200"/> <br> *drag/drop in ComfyUI* <br> [Example Workflow JSON](example_workflows/example_ToSVG_Potracer.json) <br> [Example Workflow PNG](ComfyUI_ToSVG_Potrace_Workflow.png) |

## Tested on
The node is model independent, but I'm getting great results using:
 - Model: Flux_dev (t5xxl_fp8_e4m3fn / clip_l)
- Settings: <br>
  Euler - Simple<br>
  Steps - 25-30<br>
  Latent Image size - 1024x1024<br>
  Distilled CFG Scale - 3.5<br>
  CFG - 1<br>
  Comfyui-various - Image Contrast: 1.5 - 2

 - Lora: [Simple_Vector_Flux_v2_renderartist](https://civitai.com/models/785122/simple-vector-flux)<br>
    Trigger keyword: v3ct0r , vector<br>
    Recommended strengths: 0.6 - 0.9
- Lora: [Simple_Vectors_Flux_by_Sarcastic_TOFU](https://civitai.com/models/1329550/simplevectorsfluxbysarcastictofu) <br>
    Trigger keyword: Simple_Vectors_Flux
- Lora: [Textimprover-FLUX-V0.4](https://civitai.com/models/793052) <br>
    Trigger: aidmaTextImprover <br>
    Strength: 0.3 - 1 <br>
    Can help: " with text:'YOUR TEXT' "
- LORA: [v3ctora (Vector art & Line art (Flux))](https://civitai.com/models/686231/vector-art-and-line-art-flux) <br>
Trigger: v3ctora style

## Sources, Shoutouts, Love and Inspiration
 - Potrace: https://potrace.sourceforge.net/
 - Potracer: https://github.com/tatarize/potrace
 - ComfyUI-ToSVG: https://github.com/Yanick112/ComfyUI-ToSVG
 - StabilityMatrix: https://github.com/LykosAI/StabilityMatrix
 - Gemini AI

## To Do
- [X] Deploy V1 to Github
- [ ] Real life testing & feedback
- [ ] Deploy to Comfyregistry

# ***Disclaimer***
While tested a lot and I have IT knowledge, I am no programmer by trade. This is a passion project for my own specific usecase and I'm sharing it so other people might benefit from it just as much as i benefitted from others. I am convinced this implementation has its flaws and it will probably not work on all other installations worldwide.
I can not guarantee if this project will get more updates and when. 