import os
from typing import List, Dict, Set, Union
import re


def alpha_num_order(string: str) -> str:
    """ Returns all numbers on 5 digits to let sort the string with numeric order.
    Ex: alphaNumOrder("a6b12.125")  ==> "a00006b00012.00125"
    """
    return ''.join([format(int(x), '05d') if x.isdigit()
                    else x for x in re.split(r'(\d+)', string)])


def add_to_dict(dictionary: dict, key: Union[int, str], value: Union[dict, set, list]) -> dict:
    """ Will add key-value pair to dictionary, otherwise will update key-value pair """
    if key in dictionary:
        key_present = True
        child_value_type = type(dictionary[key])
    else:
        key_present = False
        child_value_type = type(value)

    if key_present:

        if child_value_type is list:
            dictionary[key].extend(value)
        else:
            dictionary[key].update(value)
    else:
        dictionary[key] = value
    return dictionary


def get_img_listing(in_dir: str) -> List[str]:
    allowed_extensions = ('.tif', '.tiff')
    listing = os.listdir(in_dir)
    img_listing = [f for f in listing if f.endswith(allowed_extensions)]
    return img_listing


def extract_digits_from_string(string: str):
    digits = [int(x) for x in re.split(r'(\d+)', string) if x.isdigit()]  # '1_00001_Z02_CH3' -> ['1', '00001', '02', '3']
    return digits


def create_arrangement_skeleton_by_channel_tile_zplane(listing: List[str]) -> Dict[int, Dict[int, Set[int]]]:
    tile_arrangement = dict()
    for file_name in listing:
        digits = extract_digits_from_string(file_name)
        tile = digits[1]
        zplane = digits[2]
        channel = digits[3]
        tile_arrangement = add_to_dict(tile_arrangement, channel, {})
        tile_arrangement[channel] = add_to_dict(tile_arrangement[channel], tile, {zplane})

    return tile_arrangement


def arrange_listing(listing: List[str]) -> Dict[int, Dict[int, Dict[int, str]]]:
    pattern = "1_{tile:05d}_Z{zplane:03d}_CH{channel:d}.tif"

    tile_arrangement = create_arrangement_skeleton_by_channel_tile_zplane(listing)

    arranged_listing = dict()
    for channel in tile_arrangement:
        for tile in tile_arrangement[channel]:
            for zplane in tile_arrangement[channel][tile]:
                file_name = pattern.format(tile=tile, zplane=zplane, channel=channel)

                arranged_listing = add_to_dict(arranged_listing, channel, {})
                arranged_listing[channel] = add_to_dict(arranged_listing[channel], tile, {zplane: file_name})

    return arranged_listing


def get_image_paths_arranged_in_dict(img_dirs: List[str]):
    img_dirs.sort(key=alpha_num_order)
    arranged_per_cycle = dict()
    for i, cycle in enumerate(img_dirs, start=1):
        img_listing = get_img_listing(cycle)
        arranged_listing = arrange_listing(img_listing)
        arranged_per_cycle[i] = arranged_listing
    return arranged_per_cycle
