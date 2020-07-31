import argparse
import os
import posixpath as px
import os.path as osp
from datetime import datetime
import subprocess
import json
from typing import List
import shutil
import dask


from generate_bigstitcher_macro import BigStitcherMacro, FuseMacro
from file_manipulation import copy_best_z_planes_to_channel_dirs


def make_dir_if_not_exists(dir_path: str):
    if not px.exists(dir_path):
        os.makedirs(dir_path)


def load_submission_file(submission_file_path: str) -> dict:
    with open(submission_file_path, 'r') as s:
        submission = json.load(s)
    return submission


def get_values_from_submission_file(submission: dict) -> dict:
    info_for_bigstitcher = dict(num_cycles=submission['numCycles'],
                                num_channels=submission['numChannels'],
                                num_tiles=submission['numTiles'],
                                num_tiles_x=submission['regionWidth'],
                                num_tiles_y=submission['regionHeight'],
                                tile_width=submission['tileWidth'],
                                tile_height=submission['tileHeight'],
                                overlap_x=submission['tileOverlapX'],
                                overlap_y=submission['tileOverlapX'],
                                overlap_z=1,  # does not matter because we have only one z-plane
                                pixel_distance_x=submission['xyResolution'],
                                pixel_distance_y=submission['xyResolution'],
                                pixel_distance_z=submission['zPitch'],
                                reference_channel=submission['bestFocusReferenceChannel']
                                )
    return info_for_bigstitcher


def generate_bigstitcher_macro_for_first_channel(first_channel_dir: str, out_dir: str, info_for_bigstitcher: dict) -> str:
    macro = BigStitcherMacro()
    macro.img_dir = first_channel_dir
    macro.out_dir = out_dir
    macro.num_tiles = info_for_bigstitcher['num_tiles']
    macro.num_tiles_x = info_for_bigstitcher['num_tiles_x']
    macro.num_tiles_y = info_for_bigstitcher['num_tiles_y']
    macro.overlap_x = info_for_bigstitcher['overlap_x']
    macro.overlap_y = info_for_bigstitcher['overlap_y']
    macro.overlap_z = info_for_bigstitcher['overlap_z']
    macro.pixel_distance_x = info_for_bigstitcher['pixel_distance_x']
    macro.pixel_distance_y = info_for_bigstitcher['pixel_distance_y']
    macro.pixel_distance_z = info_for_bigstitcher['pixel_distance_z']
    macro_path = macro.generate()

    return macro_path


def run_bigstitcher(imagej_path: str, bigstitcher_macro_path: str):
    command = imagej_path + " --headless --console -macro " + bigstitcher_macro_path
    subprocess.run(command, shell=True)


def run_bigstitcher_for_first_channel(imagej_path: str, bigstitcher_macro_path_first_channel: str):
    run_bigstitcher(imagej_path, bigstitcher_macro_path_first_channel)


def copy_dataset_xml_to_other_channel_dirs(first_channel_dir: str, other_channel_dirs: List[str]):
    dataset_xml_path = px.join(first_channel_dir, 'dataset.xml')
    for dir_path in other_channel_dirs:
        dst_path = px.join(dir_path, 'dataset.xml')
        shutil.copy(dataset_xml_path, dst_path)


def copy_fuse_macro_to_other_channel_dirs(other_channel_dirs: List[str], other_channel_stitched_dirs: List[str]):
    macro = FuseMacro()
    for i, dir_path in enumerate(other_channel_dirs):
        macro.img_dir = dir_path
        macro.xml_file_name = 'dataset.xml'
        macro.out_dir = other_channel_stitched_dirs[i]
        macro.generate()


def run_bigstitcher_for_other_channels(imagej_path: str, other_channel_dirs: List[str]):
    task = []
    for dir_path in other_channel_dirs:
        macro_path = px.join(dir_path, 'fuse_only_macro.ijm')
        task.append(dask.delayed(run_bigstitcher)(imagej_path, macro_path))

    dask.compute(*task, scheduler='processes')


def make_channel_stitched_dirs(channel_dirs: dict, out_dir: str):
    channel_stitched_dirs = dict()
    for channel_id, dir_path in channel_dirs.items():
        dirname = 'CH' + format(channel_id, '03d')
        stitched_dir_path = px.join(out_dir, dirname)
        channel_stitched_dirs[channel_id] = stitched_dir_path
        make_dir_if_not_exists(stitched_dir_path)
    return channel_stitched_dirs


def main(imagej_path: str, img_dirs: List[str], out_dir: str, best_focus_dir: str, cytokit_json_path: str, submission_file_path: str):
    start = datetime.now()
    print('\nStarted', start)

    make_dir_if_not_exists(best_focus_dir)
    make_dir_if_not_exists(out_dir)

    print('\nCreating ImageJ macro file')

    submission = load_submission_file(submission_file_path)
    info_for_bigstitcher = get_values_from_submission_file(submission)
    print('\nSelecting best z-planes')

    print('\nStarting stitching')
    print('\nStitching reference channel')

    channel_dirs = copy_best_z_planes_to_channel_dirs(img_dirs, best_focus_dir, submission, cytokit_json_path)
    channel_stitched_dirs = make_channel_stitched_dirs(channel_dirs, out_dir)

    first_channel_dir = channel_dirs.pop(1)
    first_channel_stitched_dir = channel_stitched_dirs.pop(1)
    other_channel_dirs = list(channel_dirs.values())
    other_channel_stitched_dirs = list(channel_stitched_dirs.values())
    print(first_channel_dir)
    print(other_channel_dirs)

    bigstitcher_macro_path = generate_bigstitcher_macro_for_first_channel(first_channel_dir, first_channel_stitched_dir, info_for_bigstitcher)
    run_bigstitcher_for_first_channel(imagej_path, bigstitcher_macro_path)

    print('\nStitching other channels')
    copy_dataset_xml_to_other_channel_dirs(first_channel_dir, other_channel_dirs)
    copy_fuse_macro_to_other_channel_dirs(other_channel_dirs, other_channel_stitched_dirs)
    run_bigstitcher_for_other_channels(imagej_path, other_channel_dirs)

    #assemble_channels_in_one_file()
    #TODO add OME metadata
    print('\nTime elapsed', datetime.now() - start)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--imagej_path', type=str, help='path to imagej executable')
    parser.add_argument('--img_dirs', type=str, nargs='+', help='space separated list of dirs with images')
    parser.add_argument('--out_dir', type=str, help='path to store stitched images')
    parser.add_argument('--best_focus_dir', type=str, help='path to store best focused z planes')
    parser.add_argument('--submission_file_path', type=str, help='path to submission file')
    parser.add_argument('--cytokit_json_path', type=str, help='path to cytokit data.json file')

    args = parser.parse_args()

    main(args.imagej_path, args.img_dirs, args.out_dir, args.best_focus_dir, args.cytokit_json_path, args.submission_file_path)
