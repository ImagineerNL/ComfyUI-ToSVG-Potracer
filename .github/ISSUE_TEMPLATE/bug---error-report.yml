name: Bug / Error report
description: Template for bug reports
title: '[Bug]: '
body:
  - type: dropdown
    id: '1'
    attributes:
      label: Origin
      description: Where in your process did this occur?
      multiple: true
      options:
        - Manual installation via Git Pull
        - Manual installation via ComfyRegistry
        - Installation via ComfyUI Custom Nodes Manager
        - Import of Github Example Workflows
        - Import of Other Workflows
    validations:
      required: true
  - type: textarea
    id: '2'
    attributes:
      label: 'Describe the bug '
      description: >-
        A clear and concise description of what the bug is. ***Note, I will not
        open PNG workflow files***
      value: |
        *If applicable, add screenshots to help explain your problem.*
    validations:
      required: true
  - type: textarea
    id: Codesnippet
    attributes:
      label: ComfyUI log containing error
      description: >-
        Only the snippet of the error in the ComfyUI log when trying to run or
        install the node/workflow
      placeholder: Search your log for 'ComfyUI-ToSVG-Potracer'
  - type: dropdown
    id: '3'
    attributes:
      label: System running ComfyUI
      options:
        - Windows
        - Mac
        - Linux
        - Cloud Platform
        - Other
    validations:
      required: true
  - type: input
    id: '4'
    attributes:
      label: 'Details of System running ComfyUI:'
      description: please complete the following information
      placeholder: Manual install, StabilityMatrix, Google Colab, RunComfy, etc
    validations:
      required: true
  - type: textarea
    id: '5'
    attributes:
      label: Additional info
      description: If possible, add details and context here.
      value: |-
        - MODEL Type (e.g. Flux, SDXL) :
        - MODEL: 
        - LORA: 
        - PROMPT INFO: 
        - Etc
  - type: textarea
    id: pip
    attributes:
      label: Pip Versions
      description: >-
        If local install: In your venv, run: **`pip show potrace-windows,
        pypotrace, potracer`**
      placeholder: >-
        It should show: `WARNING: Package(s) not found: potrace-windows,,
        pypotrace,` and then list the potracer version (i'm running 0.0.4)
  - type: textarea
    id: ComfyUINodes
    attributes:
      label: ComfyUI Manager Custom Nodes
      description: >-
        Please provide a screenshot of your nodes containing 'SVG', to help
        discern conflicting nodes.
      placeholder: >-
        ComfyUI Manager - > Custom Nodes Manager --> Search bar: `svg` and post
        a screenshot of the listed node(packages)
  - type: markdown
    attributes:
      value: >-
        This template was generated with [Issue Forms
        Creator](https://issue-forms-creator.netlify.app)
