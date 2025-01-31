import re
import argparse

from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color

# Solarized 16-color palette mapping
solarized_map: dict[str, int] = {
    # "#002b36": 8,
    "#073642": 0,
    # "#586e75": 10,
    # "#657b83": 11,
    # "#839496": 12,
    # "#93a1a1": 14,
    # "#eee8d5": 7,
    # "#fdf6e3": 15,
    "#b58900": 3,
    "#cb4b16": 9,
    "#dc322f": 1,
    "#d33682": 5,
    "#6c71c4": 13,
    "#268bd2": 4,
    "#2aa198": 6,
    "#859900": 2,
}

# Keep the full Solarized hex list for closest-color calculations
solarized_colors_hex = list(solarized_map.keys())


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_lab(rgb_color):
    # rgb_color is in (R,G,B), each 0-255
    srgb = sRGBColor(*rgb_color, is_upscaled=True)
    lab = convert_color(srgb, LabColor)
    assert isinstance(lab, LabColor), "Conversion to LabColor failed"
    return (lab.lab_l, lab.lab_a, lab.lab_b)


def euclidean_distance(lab1, lab2):
    return (
        (lab1[0] - lab2[0]) ** 2 + (lab1[1] - lab2[1]) ** 2 + (lab1[2] - lab2[2]) ** 2
    ) ** 0.5


def find_closest_color(target_hex):
    target_lab = rgb_to_lab(hex_to_rgb(target_hex))
    closest_hex = None
    min_distance = float("inf")

    # Get perceived brightness of target color (rough approximation using L value)
    target_brightness = target_lab[0]  # L component in Lab color space

    for sol_hex in solarized_colors_hex:
        dist = euclidean_distance(target_lab, rgb_to_lab(hex_to_rgb(sol_hex)))

        # Apply penalty for the dark gray color (#073642 - cterm_color 0)
        # Make the penalty proportional to the brightness of the target color
        # Brighter colors get a higher penalty when mapped to dark gray
        if sol_hex == "#073642" and target_brightness > 40:
            dist *= 2.0  # Adjust this multiplier to control the penalty strength

        if dist < min_distance:
            min_distance = dist
            closest_hex = sol_hex
    return closest_hex


def replace_cterm_in_line(line):
    """
    Looks for something like color = "#XXXXXX", cterm_color = "NN"
    Keeps the same color, updates cterm_color only.
    """
    pattern = re.compile(
        r'(color\s*=\s*")'
        r"(?P<hex>#[0-9A-Fa-f]{6})"
        r'(",\s*cterm_color\s*=\s*")'
        r"(?P<cterm>\d+)"
        r'(")'
    )

    def replacer(match: re.Match):
        original_hex = match.group("hex")

        closest = find_closest_color(original_hex)
        assert closest is not None, "No closest color found"
        new_cterm_val = solarized_map[closest]
        return f"{match.group(1)}{original_hex}{match.group(3)}{new_cterm_val}{match.group(5)}"

    return pattern.sub(replacer, line)


def update_lua_file(input_file, output_file):
    with open(input_file, "r") as f:
        lines = f.readlines()
    updated_lines = [replace_cterm_in_line(ln) for ln in lines]
    with open(output_file, "w") as f:
        f.writelines(updated_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Update cterm_color in Lua icons file."
    )
    parser.add_argument("input_file", help="Path to the input .lua file")
    args = parser.parse_args()
    update_lua_file(args.input_file, args.input_file)
    print(f"Updated cterm_color values written to {args.input_file}")


if __name__ == "__main__":
    main()
