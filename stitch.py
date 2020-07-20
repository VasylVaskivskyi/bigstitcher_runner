import argparse
import os
import os.path as osp
from datetime import datetime
import subprocess

import json

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
    info_for_bigstitcher = dict(num_z_planes=1,  # for best focus use only 1 z-plane, else submission['num_z_planes']
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
                                reference_channel=submission['bestFocusReferenceChannel'],
                                reference_z_plane=1  # because we are using best z-planes
                                )
    return info_for_bigstitcher


def generate_bigstitcher_macro(img_dir: str, out_dir: str, info_for_bigstitcher: dict) -> str:
    macro = BigStitcherMacro()
    macro.img_dir = img_dir
    macro.out_dir = out_dir
    macro.num_z_planes = info_for_bigstitcher['num_z_planes']
    macro.num_channels = info_for_bigstitcher['num_channels']
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
    macro.reference_z_plane = info_for_bigstitcher['reference_z_plane']
    macro_path = macro.generate()

    return macro_path


def run_bigstitcher(imagej_path: str, bigstitcher_macro_path: str):
    command = imagej_path + " --headless --console -macro " + bigstitcher_macro_path

    start = datetime.now()

    subprocess.run(command, shell=True)

    print('elapsed', datetime.now() - start)


def find_best_z_planes(img_dir: str, best_focus_dir: str, cytokit_json_path: str):
    best_z_plane_selection_with_cytokit_info.main(img_dir, best_focus_dir, cytokit_json_path)


def main(imagej_path: str, img_dir: str, out_dir: str, best_focus_dir: str, cytokit_json_path: str, submission_file_path: str):

    make_dir_if_not_exists(best_focus_dir)
    make_dir_if_not_exists(out_dir)

    submission = load_submission_file(submission_file_path)
    info_for_bigstitcher = get_values_from_submission_file(submission)
    bigstitcher_macro_path = generate_bigstitcher_macro(best_focus_dir, out_dir, info_for_bigstitcher)

    find_best_z_planes(img_dir, best_focus_dir, cytokit_json_path)
    run_bigstitcher(imagej_path, bigstitcher_macro_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--imagej_path', type=str, help='path to imagej executable')
    parser.add_argument('--img_dir', type=str, help='path to directory with images')
    parser.add_argument('--out_dir', type=str, help='path to store stitched images')
    parser.add_argument('--best_focus_dir', type=str, help='path to store best focused z planes')
    parser.add_argument('--submission_file_path', type=str, help='path to submission file')
    parser.add_argument('--cytokit_json_path', type=str, help='path to cytokit data.json file')

    args = parser.parse_args()

    main(args.imagej_path, args.img_dir, args.out_dir, args.best_focus_dir, args.cytokit_json_path, args.submission_file_path)
