import os
import re
from functools import partial
from typing import Callable

import numpy as np
from rx import Observable

import utils


def main(
    cand_path: str, output_path: str, bin_output_path: str
) -> Callable[[str], None]:
    def _(img_path: str) -> None:
        image_arr, origin, spacing = utils.load_itk_image(img_path)

        get_voxel_coord = partial(utils.world_to_voxel_coord, origin, spacing)

        # number of scans slices
        slices_num = image_arr.shape[0]

        # capture the pacient id by regexp
        patient_id = re.findall("^.*\/(.*).mhd$", img_path)[0]

        patient_dir = os.path.join(output_path, patient_id)
        bin_patient_dir = os.path.join(bin_output_path, patient_id)

        if not os.path.isdir(patient_dir):
            os.mkdir(patient_dir)
        if not os.path.isdir(bin_patient_dir):
            os.mkdir(bin_patient_dir)

        Observable.from_(image_arr).map(utils.normalize_planes).zip(
            Observable.range(0, slices_num),
            lambda image, ind: {"image": image, "z_coord": ind},
        ).map(lambda data: partial(utils.save_scan, patient_id, **data)).tap(
            lambda fn: fn(output_path=patient_dir)
        ).tap(
            lambda fn: fn(output_path=bin_patient_dir, file_format="npy")
        ).subscribe(
            on_completed=lambda: print("Finished!"), on_error=lambda err: print(err)
        )

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
            on_error=lambda err: print(err)
        )
