import os
import os.path as osp
import posixpath as px
from typing import List, Dict, Set, Union, Tuple
import re
import json
import argparse
import shutil
import heapq
import tifffile as tif


from image_paths_arrangement import get_image_paths_arranged_in_dict, alpha_num_order


def get_top3_best_focused_plane_ids(scores):
    top3_ids_with_scores = heapq.nlargest(3, zip(scores, range(0, len(scores))), key=lambda x: x[0])
    top3_ids = [i[1] for i in top3_ids_with_scores]
    return sorted(top3_ids)


def get_info_about_best_focal_plane_per_tile(path_to_json: str):
    with open(path_to_json, 'r') as stream:
        json_file = json.load(stream)

    # dictionary where each key is index of tile, and value is index of best z plane, starts from 1
    best_z_planes_per_tile = dict()

    for tile in json_file['focal_plane_selector']:
        tile_index = tile['tile_index'] + 1
        scores = tile['scores']
        top3_best_z = get_top3_best_focused_plane_ids(scores)
        #best_z = tile['best_z'] + 1
        top3_best_z = [i+1 for i in top3_best_z]
        best_z_planes_per_tile[tile_index] = top3_best_z

    return best_z_planes_per_tile


def change_image_file_name(original_name: str) -> str:

    sub_z = re.sub(r'Z\d{3}', 'Z001', original_name)
    sub_ch = re.sub(r'_CH\d+\.', '.', sub_z)
    return sub_ch


def select_best_z_planes(img_dir: str, out_dir: str, channel_names: List[str], channel_ids: List[int],
                         arranged_listing: dict, best_z_plane_per_tile: dict) -> Dict[str, str]:
    channels_to_ignore = ['Empty', 'Blank', 'DAPI']

    best_z_plane_paths = dict()  # {input_path: output_path}

    for i, channel in enumerate(arranged_listing):
        this_channel = arranged_listing[channel]
        this_channel_name = channel_names[i]
        if this_channel_name == 'DAPI' and channel_ids[i] == 1:
            pass
        elif channel_names[i] in channels_to_ignore:
            continue
        new_channel_id = 'CH' + format(channel_ids[i], '03d')

        for tile in this_channel:
            this_tile = this_channel[tile]
            best_focal_plane_id = best_z_plane_per_tile[tile]

            input_path = this_tile[best_focal_plane_id]
            output_path = change_image_file_name(input_path)

            full_input_path = px.join(img_dir, input_path)
            full_output_path = px.join(out_dir, new_channel_id, output_path)

            best_z_plane_paths[full_input_path] = full_output_path

    return best_z_plane_paths


def select_best_z_planes_in_this_channel(channel_paths: dict, out_dir: str, best_z_plane_per_tile: dict):
    best_z_plane_paths = list()
    for tile in channel_paths:
        this_tile_paths = channel_paths[tile]
        best_focal_plane_ids = best_z_plane_per_tile[tile]

        full_input_paths = []
        for _id in best_focal_plane_ids:
            full_input_paths.append(this_tile_paths[_id])
        file_name = osp.basename(full_input_paths[0])

        output_file_name = change_image_file_name(file_name)
        full_output_path = px.join(out_dir, output_file_name)

        best_z_plane_paths.append( (full_input_paths, full_output_path) )

    return best_z_plane_paths
