import argparse
import os
import os.path as osp
from datetime import datetime
import subprocess
import json
from typing import List

from generate_bigstitcher_macro import BigStitcherMacro
import best_z_plane_selection_with_cytokit_info


def make_dir_if_not_exists(dir_path: str):
    if not osp.exists(dir_path):
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


def generate_bigstitcher_macro(best_focus_dir: str, out_dir: str, info_for_bigstitcher: dict, num_cycles: int) -> str:
    macro = BigStitcherMacro()
    macro.img_dir = best_focus_dir
    macro.out_dir = out_dir
    macro.num_channels = num_cycles * info_for_bigstitcher['num_channels']
    macro.num_tiles = info_for_bigstitcher['num_tiles']
    macro.num_tiles_x = info_for_bigstitcher['num_tiles_x']
    macro.num_tiles_y = info_for_bigstitcher['num_tiles_y']
    macro.overlap_x = info_for_bigstitcher['overlap_x']
    macro.overlap_y = info_for_bigstitcher['overlap_y']
    macro.overlap_z = info_for_bigstitcher['overlap_z']
    macro.pixel_distance_x = info_for_bigstitcher['pixel_distance_x']
    macro.pixel_distance_y = info_for_bigstitcher['pixel_distance_y']
    macro.pixel_distance_z = info_for_bigstitcher['pixel_distance_z']
    macro.reference_channel = info_for_bigstitcher['reference_channel']
    macro_path = macro.generate()

    return macro_path


def find_best_z_planes(img_dirs: List[str], best_focus_dir: str, cytokit_json_path: str):
    best_z_plane_selection_with_cytokit_info.main(img_dirs, best_focus_dir, cytokit_json_path)


def run_bigstitcher(imagej_path: str, bigstitcher_macro_path: str):
    command = imagej_path + " --headless --console -macro " + bigstitcher_macro_path
    subprocess.run(command, shell=True)


def main(imagej_path: str, img_dirs: List[str], out_dir: str, best_focus_dir: str, cytokit_json_path: str, submission_file_path: str):
    start = datetime.now()
    print('\nStarted', start)

    make_dir_if_not_exists(best_focus_dir)
    make_dir_if_not_exists(out_dir)

    print('\nCreating ImageJ macro file')

    submission = load_submission_file(submission_file_path)
    info_for_bigstitcher = get_values_from_submission_file(submission)
    num_cycles = len(img_dirs)
    bigstitcher_macro_path = generate_bigstitcher_macro(best_focus_dir, out_dir, info_for_bigstitcher, num_cycles)

    print('\nSelecting best z-planes')
    find_best_z_planes(img_dirs, best_focus_dir, cytokit_json_path)
    print('\nStarting stitching')
    run_bigstitcher(imagej_path, bigstitcher_macro_path)

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
