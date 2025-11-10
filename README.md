# Decky Colorblind

## Overview
Decky plugin to apply colorblind correction filters.
Applies correction LUTs directly through gamescope to avoid performance impact.
Makes use of [Andrew Willmott's custom hue-shift correction algorithm](https://github.com/andrewwillmott/colour-blind-luts)
to avoid brightness loss.

> **NOTE:** I am not colorblind! If you are, and you encounter any issues, please report them :)

## Features
- Supports three major types of colorblindness:
  - Protanopia
  - Deuteranopia
  - Tritanopia
- Supports both hue-shift and daltonize correction
- Simulate colorblindness
- Low performance impact
- Works across all games and the UI (in game-mode)

## Installation

> **NOTE:** Not yet available on the decky store


## Implementation
Gamescope directly supports applying 3D LUTs via the 'looks' system configurable with gamescopectl.
This isn't super well documented ([only reference I could find](https://github.com/ValveSoftware/gamescope?tab=readme-ov-file#reshade-support)), but it's supported and very performant.

```bash
# Apply a LUT
gamescopectl set_look <lut_file>

# Disable LUT
gamescopectl set_look
```

Using Andrew Willmott's implementation as reference, we can generate custom LUTs on the fly that can then be applied directly.

## Acknowledgements
- Andrew Willmott for his implementation of colorblind correction https://github.com/andrewwillmott/colour-blind-luts

