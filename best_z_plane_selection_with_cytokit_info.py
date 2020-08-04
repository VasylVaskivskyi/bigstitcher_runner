import os
import os.path as osp
import posixpath as px
from typing import List, Dict, Set, Union, Tuple
import re
import json

import numpy as np
from scipy import interpolate


def interpolate_nans(array):
    x = np.arange(0, array.shape[1])
    y = np.arange(0, array.shape[0])
    # mask invalid values
    array = np.ma.masked_invalid(array)
    xx, yy = np.meshgrid(x, y)
    # get only the valid values
    x1 = xx[~array.mask]
    y1 = yy[~array.mask]
    newarr = array[~array.mask]

    interpolated = interpolate.griddata((x1, y1), newarr.ravel(),
                                        (xx, yy), method='linear')

    return np.round(interpolated)


def validate_best_z(array: np.ndarray, max_diff: int = 3):

    hor_diff = np.abs(np.diff(array, axis=1))
    ver_diff = np.abs(np.diff(array, axis=0))

    hd = np.append(hor_diff, hor_diff[:, -1][:, np.newaxis], axis=1)
    vd = np.append(ver_diff, ver_diff[-1, :][np.newaxis, :], axis=0)

    # coordinates of outliers
    hor_outliers = np.argwhere(hd > max_diff).tolist()
    ver_outliers = np.argwhere(vd > max_diff).tolist()

    # true outlier if it is outlier in both x and y direction
    true_outliers = []
    for x in hor_outliers:
        if x in ver_outliers:
            true_outliers.append(tuple(x))

    for out_coord in true_outliers:
        array[out_coord] = np.nan

    result = interpolate_nans(array)
    return result


def pick_z_planes_below_and_above(best_z: int, max_z: int, above: int, below: int):
    above_check = best_z + above - max_z
    if above_check > 0:
        above -= above_check

    below_check = best_z - below
    if below_check < 0:
        below += below_check

    if max_z == 1:
        return [best_z]
    elif best_z == max_z:
        below_planes = [best_z - i for i in range(1, below + 1)]
        above_planes = []
    elif best_z == 0:
        below_planes = []
        above_planes = [best_z + i for i in range(1, above + 1)]
    else:
        below_planes = [best_z - i for i in range(1, below + 1)]
        above_planes = [best_z + i for i in range(1, above + 1)]

    return below_planes + [best_z] + above_planes


def get_info_about_best_focal_plane_per_tile(path_to_json: str):
    with open(path_to_json, 'r') as stream:
        json_file = json.load(stream)

    # dictionary where each key is index of tile, and value is index of best z plane, starts from 1
    best_z_planes = []
    tile_positions = []
    tile_ids = []
    num_zplanes_per_tile = []
    for tile in json_file['focal_plane_selector']:
        best_z_planes.append(tile['best_z'])
        tile_positions.append((tile['tile_y'], tile['tile_x']))
        tile_ids.append(tile['tile_index'])
        num_zplanes_per_tile.append(len(tile['scores']))

    max_position = max(tile_positions)
    array_shape = (max_position[0] + 1, max_position[1] + 1)
    best_z_per_tile_array = np.zeros(array_shape)

    for i, tile in enumerate(tile_positions):
        best_z_per_tile_array[tile] = best_z_planes[i]

    valid_best_z_array = validate_best_z(best_z_per_tile_array, max_diff=3)

    best_z_planes_per_tile = dict()
    for i, tile_id in enumerate(tile_ids):
        best_z = valid_best_z_array[tile_positions[i]]
        top_best_z = pick_z_planes_below_and_above(best_z, num_zplanes_per_tile[i], 1, 1)
        top_best_z = [i + 1 for i in top_best_z]
        best_z_planes_per_tile[tile_id + 1] = top_best_z

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
