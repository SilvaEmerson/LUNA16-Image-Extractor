import os
import re
import argparse
from itertools import islice
from operator import attrgetter
from functools import partial

import numpy as np

import utils


def main(cand_path, output_path, bin_output_path):
    def _(img_path):
        image_arr, origin, spacing = utils.load_itk_image(img_path)

        get_voxel_coord = partial(utils.world_to_voxel_coord, origin, spacing)

        # capture the pacient id by regexp
        patient_id = re.findall("^.*\/(.*).mhd$", img_path)[0]

        # get candidates of the pacient
        cands = utils.read_csv(cand_path, patient_id)

        for cand in cands:
            world_coord = np.asarray([float(cand[3]), float(cand[2]), float(cand[1])])
            voxel_coord = get_voxel_coord(world_coord)

            # get z coordenate of scan
            z_coord = int(voxel_coord[0])
            image = utils.normalize_planes(image_arr[z_coord])

            # generalizing save_scan to any output path
            save_scan = partial(utils.save_scan, image, patient_id, z_coord)
            save_scan(output_path)
            save_scan(bin_output_path, file_format='npy')

    return _


if __name__ == "__main__":
    # Adding --config and --limit command line parameter
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group("required arguments")

    required.add_argument(
        "--config",
        metavar="*.yaml",
        type=str,
        required=True,
        help="The relative path for .yaml config file",
    )

    required.add_argument(
        "--limit",
        metavar="N",
        type=int,
        required=True,
        help="The limit of files to be run",
    )

    params = vars(parser.parse_args())

    limit = params.get("limit")
    config_file = params.get("config")

    config = utils.get_env_config(config_file)

    INPUT_PATH = config.get("INPUT_PATH")
    OUTPUT_PATH = config.get("OUTPUT_PATH")
    CAND_PATH = config.get("CAND_PATH")
    BIN_OUTPUT_PATH = config.get("BIN_OUTPUT_PATH")


    # scandir returns a iterator of os.DirEntry
    with os.scandir(INPUT_PATH) as subset:
        mhd_files = filter(lambda filename: filename.name.endswith(".mhd"), subset)
        mhd_filenames = islice(map(attrgetter('path'), mhd_files), limit)
        [*map(main(CAND_PATH, OUTPUT_PATH, BIN_OUTPUT_PATH), mhd_filenames)]
        print("Sucess")
