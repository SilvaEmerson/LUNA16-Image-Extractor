import os
import re
from itertools import islice
from operator import attrgetter
from functools import partial

import numpy as np
from rx import Observable

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
            save_scan_to = partial(utils.save_scan, image, patient_id, z_coord)
            save_scan_to(output_path)
            save_scan_to(bin_output_path, file_format='npy')

    return _


if __name__ == "__main__":
    limit, config = utils.get_running_params()

    INPUT_PATH = config.get("INPUT_PATH")
    OUTPUT_PATH = config.get("OUTPUT_PATH")
    CAND_PATH = config.get("CAND_PATH")
    BIN_OUTPUT_PATH = config.get("BIN_OUTPUT_PATH")

    # scandir returns a iterator of os.DirEntry
    with os.scandir(INPUT_PATH) as subset:
        Observable.from_(subset) \
            .filter(lambda file: file.name.endswith(".mhd")) \
            .take(limit) \
            .pluck_attr('path') \
            .map(main(CAND_PATH, OUTPUT_PATH, BIN_OUTPUT_PATH)) \
            .subscribe(lambda : print("Finished!"))
