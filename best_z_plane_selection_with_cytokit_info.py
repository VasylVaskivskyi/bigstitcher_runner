import os
import os.path as osp
from typing import List, Dict, Set, Union, Tuple
import re
import json
import argparse
import shutil

import tifffile as tif


from image_paths_arrangement import get_image_paths_arranged_in_dict, alpha_num_order


def get_info_about_best_focal_plane_per_tile(path_to_json: str):
    with open(path_to_json, 'r') as stream:
        json_file = json.load(stream)

    # dictionary where each key is index of tile, and value is index of best z plane, starts from 1
    best_z_plane_per_tile = dict()
    for tile in json_file['focal_plane_selector']:
        tile_index = tile['tile_index'] + 1
        best_z = tile['best_z'] + 1
        best_z_plane_per_tile[tile_index] = best_z

    return best_z_plane_per_tile


def change_image_file_name(original_name: str, channel_id: int) -> str:
    sub_z = re.sub(r'Z\d{3}', 'Z001', original_name)
    sub_ch = re.sub(r'CH\d+', 'CH' + format(channel_id, '03d'), sub_z)
    return sub_ch


def select_best_z_planes(img_dirs: List[str], out_dir: str,
                         arranged_listing: dict, best_z_plane_per_tile: dict) -> Dict[str, str]:

    best_z_plane_paths = dict()  # {input_path: output_path}
    first_cycle = min(list(arranged_listing.keys()))
    num_channels_per_cycle = max(list(arranged_listing[first_cycle].keys()))

    for i, cycle in enumerate(arranged_listing):
        this_cycle = arranged_listing[cycle]

        for channel in this_cycle:
            this_channel = this_cycle[channel]
            new_channel_id = i * num_channels_per_cycle + int(channel)

            for tile in this_channel:
                this_tile = this_channel[tile]
                best_focal_plane_id = best_z_plane_per_tile[tile]

                input_path = this_tile[best_focal_plane_id]
                output_path = change_image_file_name(input_path, new_channel_id)

                full_input_path = osp.join(img_dirs[i], input_path)

                full_output_path = osp.join(out_dir, output_path)

                best_z_plane_paths[full_input_path] = full_output_path

    return best_z_plane_paths


def copy_and_rename_best_z_planes(best_z_plane_paths: dict):
    for src, dst in best_z_plane_paths.items():
        # tif.imwrite(dst, tif.imread(src))
        shutil.copy(src, dst)


def make_dir_if_not_exists(dir_path: str):
    if not osp.exists(dir_path):
        os.makedirs(dir_path)


def main(img_dirs: list, out_dir: str, cytokit_json_path: str):

    make_dir_if_not_exists(out_dir)
    img_dirs.sort(key=alpha_num_order)
    best_z_plane_per_tile = get_info_about_best_focal_plane_per_tile(cytokit_json_path)
    arranged_listing = get_image_paths_arranged_in_dict(img_dirs)
    best_z_plane_paths = select_best_z_planes(img_dirs, out_dir, arranged_listing, best_z_plane_per_tile)
    copy_and_rename_best_z_planes(best_z_plane_paths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_dirs', type=str, nargs='+', help='space separated list of dirs with images')
    parser.add_argument('--out_dir', type=str, help='path to store best focused z planes')
    parser.add_argument('--cytokit_json_path', type=str, help='path to cytokit data.json file')

    args = parser.parse_args()

    main(args.img_dirs, args.out_dir, args.json_path)
