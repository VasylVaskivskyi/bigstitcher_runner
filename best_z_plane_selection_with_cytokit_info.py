import os
import os.path as osp
from typing import List, Dict, Set, Union
import re
import json
import argparse

import tifffile as tif


from image_paths_arrangement import get_image_paths_arranged_in_dict


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


def change_image_file_name(original_name: str) -> str:
    return re.sub(r'Z\d{3}', 'Z001', original_name)


def select_best_z_planes(img_dir: str, out_dir: str,
                         arranged_listing: dict, best_z_plane_per_tile: dict) -> Dict[str, str]:

    best_z_plane_paths = dict()  # {input_path: output_path}

    for channel in arranged_listing:
        for tile in arranged_listing[channel]:
            best_focal_plane_id = best_z_plane_per_tile[tile]
            input_path = arranged_listing[channel][tile][best_focal_plane_id]
            output_path = change_image_file_name(input_path)

            full_input_path = osp.join(img_dir, input_path)
            full_output_path = osp.join(out_dir, output_path)

            best_z_plane_paths[full_input_path] = full_output_path

    return best_z_plane_paths


def copy_and_rename_best_z_planes(best_z_plane_paths: dict):
    for src, dst in best_z_plane_paths.items():
        tif.imwrite(dst, tif.imread(src))
        # shutil.copy(src, dst)


def make_dir_if_not_exists(dir_path: str):
    if not osp.exists(dir_path):
        os.makedirs(dir_path)


def main(img_dir: str, out_dir: str, cytokit_json_path: str):

    make_dir_if_not_exists(out_dir)

    best_z_plane_per_tile = get_info_about_best_focal_plane_per_tile(cytokit_json_path)
    arranged_listing = get_image_paths_arranged_in_dict(img_dir)
    best_z_plane_paths = select_best_z_planes(img_dir, out_dir, arranged_listing, best_z_plane_per_tile)
    copy_and_rename_best_z_planes(best_z_plane_paths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--img_dir', type=str, help='path to directory with images')
    parser.add_argument('--out_dir', type=str, help='path to store best focused z planes')
    parser.add_argument('--cytokit_json_path', type=str, help='path to cytokit data.json file')

    args = parser.parse_args()

    main(args.img_dir, args.out_dir, args.json_path)
