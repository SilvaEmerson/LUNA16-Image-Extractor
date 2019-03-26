import os
import re
from functools import partial

import numpy as np
from rx import Observable

import utils


def main(img_path: str) -> Observable:
    image_arr, origin, spacing = utils.load_itk_image(img_path)

    output_path = os.environ['OUTPUT_PATH']
    cand_path = os.environ['CAND_PATH']
    bin_output_path = os.environ['BIN_OUTPUT_PATH']

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

    return (
        Observable.from_(image_arr)
        .map(utils.normalize_planes)
        .zip(
            Observable.range(0, slices_num),
            lambda image, ind: {"image": image, "z_coord": ind},
        )
        .map(lambda data: partial(utils.save_scan, patient_id, **data))
        .tap(lambda save_at: save_at(output_path=patient_dir))
        .tap(
            lambda save_at: save_at(
                output_path=bin_patient_dir, file_format="npy"
            )
        )
    )


if __name__ == "__main__":
    limit, config = utils.get_running_params()

    Observable.from_(config)\
            .tap(lambda var: utils.set_environ(var, config[var]))\
            .subscribe()\
            .dispose()

    # scandir returns a iterator of os.DirEntry
    with os.scandir(os.environ['INPUT_PATH']) as subset:
        sub = (
            Observable.from_(subset)
            .filter(lambda file: file.name.endswith(".mhd"))
            .take(
                limit
                # pluck_attr get the path attribute of each emitted object
            )
            .pluck_attr("path")
            .flat_map(main)
            .subscribe(on_error=lambda err: print(err))
        )

        sub.dispose()
