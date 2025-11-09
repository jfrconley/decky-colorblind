import subprocess
import lut_generator

# We can use gamescopectl to configure the looks system when applying generated 3d luts
# `gamescopectl set_look <path>` will load a .cube file and apply it across all sessions
# `gamescopectl set_look` will reset the setting, disabling the lut
# this setting appears to be persistent

"""
Resets the look system to default
"""
def reset_look():
    subprocess.run(["gamescopectl", "set_look"])

"""
Sets the look system to use the specified .cube file for color correction.

:param filename: Path to the .cube file to use for color correction
:type filename: str
"""
def set_look(filename: str):
    subprocess.run(["gamescopectl", "set_look", filename])

