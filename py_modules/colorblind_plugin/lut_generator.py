"""
colorblind LUT generator.

This module generates 3D Look-Up Tables (LUTs) for colorblind correction,
simulation, and daltonization. It's a pure Python port of https://github.com/andrewwillmott/colour-blind-luts
credit to Andrew Willmott for the original implementation.
Modified to return .cube format luts for use with gamescope.
"""

import math
from typing import Tuple, List, Literal


# Type aliases
CBType = Literal["protanope", "deuteranope", "tritanope"]
Operation = Literal["simulate", "daltonise", "correct"]


class Vec3:
    """3D vector class for RGB/LMS color operations."""

    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vec3') -> 'Vec3':
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vec3':
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> 'Vec3':
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def dot(self, other: 'Vec3') -> float:
        """Dot product."""
        return self.x * other.x + self.y * other.y + self.z * other.z

    def pow(self, exponent: float) -> 'Vec3':
        """Component-wise power."""
        return Vec3(
            math.pow(self.x, exponent),
            math.pow(self.y, exponent),
            math.pow(self.z, exponent)
        )

    def clamp(self) -> 'Vec3':
        """Clamp components to [0.0, 1.0] range."""
        return Vec3(
            max(0.0, min(1.0, self.x)),
            max(0.0, min(1.0, self.y)),
            max(0.0, min(1.0, self.z))
        )

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)


class Mat3:
    """3x3 matrix class for color space transformations."""

    __slots__ = ('rows',)

    def __init__(self, r0: Vec3, r1: Vec3, r2: Vec3):
        """Initialize with three row vectors."""
        self.rows = (r0, r1, r2)

    def mul_vec(self, v: Vec3) -> Vec3:
        """Multiply matrix by vector."""
        return Vec3(
            self.rows[0].dot(v),
            self.rows[1].dot(v),
            self.rows[2].dot(v)
        )

    def row(self, i: int) -> Vec3:
        """Get row vector."""
        return self.rows[i]

    def col(self, i: int) -> Vec3:
        """Get column vector."""
        return Vec3(
            self.rows[0].to_tuple()[i],
            self.rows[1].to_tuple()[i],
            self.rows[2].to_tuple()[i]
        )


# =============================================================================
# Color Space Conversion Matrices
# =============================================================================

# LMS color space models human eye response
# https://en.wikipedia.org/wiki/LMS_color_space
# From: https://ixora.io/projects/colorblindness/color-blindness-simulation-research/

LMS_FROM_RGB = Mat3(
    Vec3(0.31399022, 0.63951294, 0.04649755),
    Vec3(0.15537241, 0.75789446, 0.08670142),
    Vec3(0.01775239, 0.10944209, 0.87256922)
)

RGB_FROM_LMS = Mat3(
    Vec3(5.47221206, -4.64196010, 0.16963708),
    Vec3(-1.1252419, 2.29317094, -0.16789520),
    Vec3(0.02980165, -0.19318073, 1.16364789)
)

# Colorblind simulation matrices (in LMS space)
# These transform LMS colors to simulate particular forms of color blindness

LMS_PROTANOPE = Mat3(
    Vec3(0.0, 1.05118294, -0.05116099),  # L channel lost
    Vec3(0.0, 1.0, 0.0),
    Vec3(0.0, 0.0, 1.0)
)

LMS_DEUTERANOPE = Mat3(
    Vec3(1.0, 0.0, 0.0),
    Vec3(0.9513092, 0.0, 0.04866992),  # M channel lost
    Vec3(0.0, 0.0, 1.0)
)

LMS_TRITANOPE = Mat3(
    Vec3(1.0, 0.0, 0.0),
    Vec3(0.0, 1.0, 0.0),
    Vec3(-0.86744736, 1.86727089, 0.0)  # S channel lost
)

# Combined simulation matrix (used in correction algorithm)
LMS_SIMULATE = Mat3(
    Vec3(0.0, 1.05118294, -0.05116099),
    Vec3(0.9513092, 0.0, 0.04866992),
    Vec3(-0.86744736, 1.86727089, 0.0)
)

# =============================================================================
# Daltonization Matrices (Fidaner et al.)
# =============================================================================
# From: http://scien.stanford.edu/class/psych221/projects/05/ofidaner/project_report.pdf
# These matrices convert color error to delta corrections

# Alternative LMS conversion used by Viénot daltonization
LMS_FROM_RGB_V = Mat3(
    Vec3(17.8824, 43.5161, 4.11935),
    Vec3(3.45565, 27.1554, 3.86714),
    Vec3(0.0299566, 0.184309, 1.46709)
)

RGB_FROM_LMS_V = Mat3(
    Vec3(0.080944447900, -0.13050440900, 0.116721066),
    Vec3(-0.010248533500, 0.05401932660, -0.113614708),
    Vec3(-0.000365296938, -0.00412161469, 0.693511405)
)

LMS_PROTANOPE_V = Mat3(
    Vec3(0.0, 2.02344, -2.52581),
    Vec3(0.0, 1.0, 0.0),
    Vec3(0.0, 0.0, 1.0)
)

LMS_DEUTERANOPE_V = Mat3(
    Vec3(1.0, 0.0, 0.0),
    Vec3(0.494207, 0.0, 1.24827),
    Vec3(0.0, 0.0, 1.0)
)

LMS_TRITANOPE_V = Mat3(
    Vec3(1.0, 0.0, 0.0),
    Vec3(0.0, 1.0, 0.0),
    Vec3(-0.395913, 0.801109, 0.0)
)

# Error to delta conversion matrices (Fidaner)
DALTON_ERROR_TO_DELTA_P = Mat3(
    Vec3(0.0, 0.0, 0.0),
    Vec3(0.7, 1.0, 0.0),
    Vec3(0.7, 0.0, 1.0)
)

DALTON_ERROR_TO_DELTA_D = Mat3(
    Vec3(1.0, 0.7, 0.0),
    Vec3(0.0, 0.0, 0.0),
    Vec3(0.0, 0.7, 1.0)
)

DALTON_ERROR_TO_DELTA_T = Mat3(
    Vec3(1.0, 0.0, 0.7),
    Vec3(0.0, 1.0, 0.7),
    Vec3(0.0, 0.0, 0.0)
)

# Correction algorithm matrices
NC_DELTA_RECIP = Mat3(
    Vec3(0.0, 1.05118299, -1.15280771),
    Vec3(0.951309144, 0.0, 0.535540938),
    Vec3(-19.5461426, 20.5465717, 0.0)
)

# =============================================================================
# Constants
# =============================================================================

GAMMA = 2.2  # sRGB gamma


# =============================================================================
# Color Conversion Functions
# =============================================================================

def to_linear(rgb: Vec3) -> Vec3:
    """Convert sRGB to linear RGB (apply gamma correction)."""
    return rgb.pow(GAMMA)


def from_linear(rgb: Vec3) -> Vec3:
    """Convert linear RGB to sRGB (remove gamma correction)."""
    return rgb.pow(1.0 / GAMMA)


# =============================================================================
# Colorblind Simulation and Correction Functions
# =============================================================================

def simulate(rgb: Vec3, cb_type: CBType, strength: float = 1.0) -> Vec3:
    """
    Simulate colorblindness by reducing sensitivity in one LMS channel.

    Args:
        rgb: Input color in sRGB space (0-1 range)
        cb_type: Type of colorblindness
        strength: Strength of effect (0.0 = normal, 1.0 = full colorblindness)

    Returns:
        Simulated color in sRGB space
    """
    # Map cb_type to LMS channel index
    channel_map = {"protanope": 0, "deuteranope": 1, "tritanope": 2}
    channel = channel_map[cb_type]

    # Convert to linear and then to LMS
    linear_rgb = to_linear(rgb)
    lms = LMS_FROM_RGB.mul_vec(linear_rgb)

    # Get the affected channel and compute simulated value
    lms_tuple = lms.to_tuple()
    sim_row = LMS_SIMULATE.row(channel)
    sim_value = sim_row.dot(lms)

    # Interpolate between original and simulated based on strength
    affected = lms_tuple[channel]
    new_value = affected + strength * (sim_value - affected)

    # Reconstruct LMS vector
    lms_list = list(lms_tuple)
    lms_list[channel] = new_value
    lms_sim = Vec3(*lms_list)

    # Convert back to RGB and clamp before gamma correction
    rgb_out = RGB_FROM_LMS.mul_vec(lms_sim)
    rgb_clamped = rgb_out.clamp()

    return from_linear(rgb_clamped)


def simulate_v(rgb: Vec3, lms_transform: Mat3) -> Vec3:
    """
    Simulate colorblindness using Viénot LMS matrices.
    Used internally by daltonise function.
    """
    lms = lms_transform.mul_vec(LMS_FROM_RGB_V.mul_vec(rgb))
    return RGB_FROM_LMS_V.mul_vec(lms)


def daltonise(rgb: Vec3, cb_type: CBType, strength: float = 1.0) -> Vec3:
    """
    Apply Fidaner daltonization to enhance colors for colorblind viewing.

    Daltonization shifts colors toward the visible spectrum by computing
    the error between original and simulated colors, then redistributing
    that error into visible channels.

    Args:
        rgb: Input color in sRGB space (0-1 range)
        cb_type: Type of colorblindness
        strength: Strength of effect (0.0 = no change, 1.0 = full daltonization)

    Returns:
        Daltonized color in sRGB space
    """
    # Select appropriate matrices based on colorblind type
    if cb_type == "protanope":
        lms_sim_matrix = LMS_PROTANOPE_V
        error_matrix = DALTON_ERROR_TO_DELTA_P
    elif cb_type == "deuteranope":
        lms_sim_matrix = LMS_DEUTERANOPE_V
        error_matrix = DALTON_ERROR_TO_DELTA_D
    else:  # tritanope
        lms_sim_matrix = LMS_TRITANOPE_V
        error_matrix = DALTON_ERROR_TO_DELTA_T

    # Simulate colorblindness
    rgb_sim = simulate_v(rgb, lms_sim_matrix)

    # Calculate error and convert to delta
    error = rgb - rgb_sim
    rgb_delta = error_matrix.mul_vec(error * strength)

    # Add delta to original color and clamp to valid range
    rgb_out = rgb + rgb_delta
    return rgb_out.clamp()


def correct(rgb: Vec3, cb_type: CBType, strength: float = 1.0) -> Vec3:
    """
    Apply custom correction for colorblind viewing.

    This uses a mixture of two strategies:
    1. Redistributing error into other channels (hue shift)
    2. Simply brightening the affected channel

    Args:
        rgb: Input color in sRGB space (0-1 range)
        cb_type: Type of colorblindness
        strength: Strength of correction (0.0 = no change, 1.0 = full correction)

    Returns:
        Corrected color in sRGB space
    """
    # Map cb_type to channel index
    channel_map = {"protanope": 0, "deuteranope": 1, "tritanope": 2}
    channel = channel_map[cb_type]

    # Convert to linear and then to LMS
    linear_rgb = to_linear(rgb)
    lms = LMS_FROM_RGB.mul_vec(linear_rgb)

    # Get original and simulated values for affected channel
    lms_tuple = lms.to_tuple()
    org_elt = lms_tuple[channel]
    sim_row = LMS_SIMULATE.row(channel)
    sim_elt = sim_row.dot(lms)
    error = strength * (org_elt - sim_elt)

    # Correction strategy mixing factors
    mc = strength * strength  # Strategy 1: hue shifting (redistribution)
    ms = 1.0 - strength       # Strategy 2: brightness (amplification)

    # Tuning values for redistribution (different per channel)
    amount_recip = [0.25, -0.3, -0.07]  # Note: negated in C++ code
    amount = -amount_recip[channel]

    # Build correction vector
    recip_col = NC_DELTA_RECIP.col(channel)
    correct_vec = recip_col * (mc * amount)

    # Set the affected channel component to brightness strategy
    correct_list = list(correct_vec.to_tuple())
    correct_list[channel] = ms * 2.0
    correct_final = Vec3(*correct_list)

    # Apply correction
    lms_corrected = lms + correct_final * error

    # Convert back to RGB and clamp before gamma correction
    rgb_out = RGB_FROM_LMS.mul_vec(lms_corrected)
    rgb_clamped = rgb_out.clamp()

    return from_linear(rgb_clamped)


# =============================================================================
# LUT Generation
# =============================================================================

def create_lut(
    cb_type: CBType,
    operation: Operation,
    strength: float,
    lut_size: int
) -> List[Tuple[float, float, float]]:
    """
    Generate a 3D LUT for colorblind correction.

    The LUT samples the RGB cube evenly and applies the specified transformation.
    Output is a flat list in standard 3D LUT order (B changes fastest, then G, then R).

    Args:
        cb_type: Type of colorblindness
        operation: Operation to apply
        strength: Strength of effect (0.0-1.0)
        lut_size: Size of LUT cube (e.g., 32 for 32x32x32)

    Returns:
        List of (r, g, b) tuples representing the transformed LUT
    """
    # Select transformation function
    transform_func = {
        "simulate": simulate,
        "daltonise": daltonise,
        "correct": correct
    }[operation]

    lut = []

    # Calculate sampling parameters
    # We sample at the center of each LUT cell for better accuracy
    scale = 1.0 / lut_size
    offset = scale / 2.0

    # Iterate in standard LUT order: R outermost, G middle, B innermost
    for r_idx in range(lut_size):
        for g_idx in range(lut_size):
            for b_idx in range(lut_size):
                # Sample at cell center
                r = (r_idx + 0.5) * scale
                g = (g_idx + 0.5) * scale
                b = (b_idx + 0.5) * scale

                # Apply transformation
                rgb_in = Vec3(r, g, b)
                rgb_out = transform_func(rgb_in, cb_type, strength)

                # Clamp to valid range
                rgb_clamped = rgb_out.clamp()

                lut.append(rgb_clamped.to_tuple())

    return lut


def write_cube_file(
    lut_data: List[Tuple[float, float, float]],
    lut_size: int,
    output_path: str,
    title: str = "Colorblind Correction LUT"
) -> None:
    """
    Write LUT data to a .cube file.

    The .cube format is an industry standard supported by many color grading
    tools including gamescopectl.

    Args:
        lut_data: List of (r, g, b) tuples
        lut_size: Size of LUT cube
        output_path: Path to output .cube file
        title: Title to include in file header
    """
    with open(output_path, 'w') as f:
        # Write header
        f.write(f'TITLE "{title}"\n')
        f.write(f'LUT_3D_SIZE {lut_size}\n')

        # Write LUT data
        for r, g, b in lut_data:
            # Format with 6 decimal places for precision
            f.write(f'{r:.6f} {g:.6f} {b:.6f}\n')


# =============================================================================
# Public API
# =============================================================================

def generate_lut(
    cb_type: CBType,
    operation: Operation,
    strength: float = 1.0,
    output_path: str = None,
    lut_size: int = 32
) -> str:
    """
    Generate a colorblind correction LUT and save to .cube file.

    This is the main entry point for LUT generation.

    Args:
        cb_type: Type of colorblindness to correct for:
            - "protanope": Red deficiency (1% of men)
            - "deuteranope": Green deficiency (1% of men)
            - "tritanope": Blue deficiency (0.003% of population)

        operation: Operation to perform:
            - "simulate": Simulate how colorblind users see
            - "daltonise": Enhance colors using Fidaner method
            - "correct": Correct using custom amplification/hue shift

        strength: Strength of effect (0.0-1.0, default 1.0)
            - 0.0: No effect (identity LUT)
            - 1.0: Full strength correction
            - Values between allow for partial correction

        output_path: Path to output .cube file (optional)
            If None, generates default name based on parameters

        lut_size: Size of LUT cube (default 32)
            Common values: 16, 32, 64
            Larger = more accurate but bigger files

    Returns:
        Path to the generated .cube file

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate inputs
    valid_cb_types = ["protanope", "deuteranope", "tritanope"]
    if cb_type not in valid_cb_types:
        raise ValueError(f"cb_type must be one of {valid_cb_types}")

    valid_operations = ["simulate", "daltonise", "correct"]
    if operation not in valid_operations:
        raise ValueError(f"operation must be one of {valid_operations}")

    if not 0.0 <= strength <= 1.0:
        raise ValueError("strength must be between 0.0 and 1.0")

    if lut_size not in [16, 32, 64]:
        raise ValueError("lut_size must be 16, 32, or 64")

    # Generate default output path if not provided
    if output_path is None:
        output_path = f"{cb_type}_{operation}_{int(strength*100)}.cube"

    # Generate LUT
    lut_data = create_lut(cb_type, operation, strength, lut_size)

    # Create title for .cube file
    title = f"{cb_type.capitalize()} {operation.capitalize()} (strength={strength:.2f})"

    # Write to file
    write_cube_file(lut_data, lut_size, output_path, title)

    return output_path


# =============================================================================
# Command-Line Interface
# =============================================================================

def main():
    """Command-line interface for LUT generation."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate colorblind correction/simulation LUTs in .cube format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate protanope correction LUT
  %(prog)s protanope correct -o protanope_correct.cube

  # Generate deuteranope simulation at 80%% strength
  %(prog)s deuteranope simulate --strength 0.8

  # Generate tritanope daltonization with 64x64x64 resolution
  %(prog)s tritanope daltonise --size 64 -o tritanope_daltonise_64.cube

  # List all available options
  %(prog)s --help
        """
    )

    # Positional arguments
    parser.add_argument(
        "cb_type",
        choices=["protanope", "deuteranope", "tritanope"],
        help="Type of colorblindness to correct/simulate"
    )

    parser.add_argument(
        "operation",
        choices=["simulate", "daltonise", "correct"],
        help="Operation to perform (simulate: show how CB users see, "
             "daltonise: Fidaner enhancement, correct: custom correction)"
    )

    # Optional arguments
    parser.add_argument(
        "-s", "--strength",
        type=float,
        default=1.0,
        metavar="FLOAT",
        help="Effect strength from 0.0 (none) to 1.0 (full) (default: 1.0)"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        metavar="PATH",
        help="Output .cube file path (default: auto-generated from parameters)"
    )

    parser.add_argument(
        "--size",
        type=int,
        default=32,
        choices=[16, 32, 64],
        help="LUT resolution (16/32/64) - higher is more accurate (default: 32)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed generation information"
    )

    # Parse arguments
    args = parser.parse_args()

    # Validate strength
    if not 0.0 <= args.strength <= 1.0:
        parser.error(f"strength must be between 0.0 and 1.0, got {args.strength}")

    try:
        # Show generation info if verbose
        if args.verbose:
            print(f"Generating {args.size}x{args.size}x{args.size} LUT...")
            print(f"  Type: {args.cb_type}")
            print(f"  Operation: {args.operation}")
            print(f"  Strength: {args.strength}")
            total_entries = args.size ** 3
            print(f"  Total entries: {total_entries:,}")

        # Generate LUT
        output_path = generate_lut(
            cb_type=args.cb_type,
            operation=args.operation,
            strength=args.strength,
            output_path=args.output,
            lut_size=args.size
        )

        # Success message
        if args.verbose:
            import os
            file_size = os.path.getsize(output_path)
            print(f"\n✓ Successfully generated LUT")
            print(f"  Output: {output_path}")
            print(f"  Size: {file_size:,} bytes")
        else:
            print(f"Generated: {output_path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
