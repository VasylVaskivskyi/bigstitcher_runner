import os
import posixpath as px
import os.path as osp
import shutil
from typing import List, Dict, Set, Union

import numpy as np
import tifffile as tif


from image_paths_arrangement import get_image_paths_arranged_in_dict, alpha_num_order
from best_z_plane_selection_with_cytokit_info import get_info_about_best_focal_plane_per_tile, select_best_z_planes_in_this_channel


def convert(img, target_type_min, target_type_max, target_type):
    imin = img.min()
    imax = img.max()

    a = (target_type_max - target_type_min) / (imax - imin)
    b = target_type_max - a * imax
    new_img = (a * img + b).astype(target_type)
    return new_img


def project_stack(path_list: List[str]):
    return convert(np.mean(np.stack(list(map(tif.imread, path_list)), axis=0), axis=0), 0, 65535, np.uint16)


def copy_to_destination(best_z_plane_paths: List[tuple]):
    for src, dst in best_z_plane_paths:
        img = project_stack(src)
        tif.imwrite(dst, img)
        #shutil.copy(src, dst)


def make_dir_if_not_exists(dir_path: str):
    if not px.exists(dir_path):
        os.makedirs(dir_path)


def get_channel_names_per_cycle(submission: dict):
    channel_names = submission['channelNames']['channelNamesArray']
    channels_per_cycle = submission['numChannels']
    channel_ids = list(range(0, len(channel_names)))
    cycle_boundaries = channel_ids[::channels_per_cycle]
    cycle_boundaries.append(len(channel_names))

    channel_names_per_cycle = dict()
    for i in range(0, len(cycle_boundaries) - 1):
        f = cycle_boundaries[i]  # from
        t = cycle_boundaries[i+1]  # to
        channel_names_per_cycle[i+1] = channel_names[f:t]

    return channel_names_per_cycle


def create_paths_for_channel_dirs(img_dirs, out_dir, channel_names_per_cycle, best_z_plane_per_tile):
    channels_to_ignore = ['Empty', 'Blank', 'DAPI']

    channel_dirs = dict()
    channel_image_paths = dict()

    channel_id = 1
    for i, dir_path in enumerate(img_dirs, start=1): # cycle level
        this_cycle_channel_names = channel_names_per_cycle[i] # cycle level
        arranged_listing = get_image_paths_arranged_in_dict(dir_path)  # channel level

        for j, channel in enumerate(arranged_listing):
            this_channel_paths = arranged_listing[channel]
            this_channel_name = this_cycle_channel_names[j]

            if this_channel_name in channels_to_ignore:
                if this_channel_name == 'DAPI' and channel_id == 1:
                    pass
                else:
                    continue
            print(this_channel_name)
            new_channel_id = 'CH' + format(channel_id, '03d')
            this_channel_out_dir = px.join(out_dir, new_channel_id)
            best_z_plane_paths = select_best_z_planes_in_this_channel(this_channel_paths, this_channel_out_dir, best_z_plane_per_tile)
            #print(this_channel_name, new_channel_id, best_z_plane_paths)
            channel_dirs[channel_id] = this_channel_out_dir
            channel_image_paths[channel_id] = best_z_plane_paths

            channel_id += 1

    return channel_dirs, channel_image_paths


def copy_best_z_planes_to_channel_dirs(img_dirs, out_dir, submission, cytokit_json_path):
    best_z_plane_per_tile = get_info_about_best_focal_plane_per_tile(cytokit_json_path)
    channel_names_per_cycle = get_channel_names_per_cycle(submission)
    channel_dirs, channel_image_paths = create_paths_for_channel_dirs(img_dirs, out_dir, channel_names_per_cycle, best_z_plane_per_tile)
    for ch_id, dir_path in channel_dirs.items():
        make_dir_if_not_exists(dir_path)
    for channel in channel_image_paths:
        copy_to_destination(channel_image_paths[channel])

    return channel_dirs


def assemble_channels_in_one_file(channel_stitched_dirs: List[str], output_path: str, ome_meta: str):
    img_name = 'fused_tp_0_ch_0.tif'
    with tif.TiffWriter(output_path, bigtiff=True) as TW:
        for dir_path in channel_stitched_dirs:
            img_path = osp.join(dir_path, img_name)
            TW.save(tif.imread(img_path), photometric='minisblack', description=ome_meta)

