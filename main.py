import os
import re
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

        z_coord = (
            cands.map(
                lambda cand: np.asarray(
                    [float(cand[3]), float(cand[2]), float(cand[1])]
                )
            ).map(get_voxel_coord)
            # get z coord. of a image
            .map(lambda coord: int(coord[0]))
        )

        # get image from z_coord observable
        image = z_coord.map(lambda z_coord: utils.normalize_planes(image_arr[z_coord]))

        # use zip operator to concatenate each image/z_coord pair
        save_image = z_coord.zip(
            image, lambda z_coord, image: {"image": image, "z_coord": z_coord}
        ).map(lambda data: partial(utils.save_scan, patient_id, **data))

        save_image.tap(lambda fn: fn(output_path=output_path))\
            .tap(lambda fn: fn(output_path=bin_output_path, file_format="npy"))\
            .subscribe()

        return "Finished!"

    return _


if __name__ == "__main__":
    limit, config = utils.get_running_params()

    INPUT_PATH = config.get("INPUT_PATH")
    OUTPUT_PATH = config.get("OUTPUT_PATH")
    CAND_PATH = config.get("CAND_PATH")
    BIN_OUTPUT_PATH = config.get("BIN_OUTPUT_PATH")

    # scandir returns a iterator of os.DirEntry
    with os.scandir(INPUT_PATH) as subset:
        Observable.from_(subset).filter(lambda file: file.name.endswith(".mhd")).take(
            limit
        # pluck_attr get the path attribute of each emitted object
        ).pluck_attr("path").map(
            main(CAND_PATH, OUTPUT_PATH, BIN_OUTPUT_PATH)
        ).subscribe(
            lambda msg: print(msg)
        )
