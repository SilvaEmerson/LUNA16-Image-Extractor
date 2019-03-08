import os
import re
import asyncio
import multiprocessing
from functools import partial
from typing import Callable

import numpy as np
from rx import Observable
from rx.concurrency import AsyncIOScheduler

import utils


def main(
    candidates: Observable, output_path: str, bin_output_path: str
) -> Callable[[str], None]:
    def _main(img_path: str) -> Observable:
        image_arr, origin, spacing = utils.load_itk_image(img_path)

        get_voxel_coord = partial(utils.world_to_voxel_coord, origin, spacing)

        # number of scans slices
        slices_num = image_arr.shape[0]

        # capture the pacient id by regexp
        patient_id = re.findall("^.*\/(.*).mhd$", img_path)[0]

        candidates_regions = candidates.filter(lambda line: line[0] == patient_id)
        no_nodules = candidates_regions.filter(lambda line: line[-1] == '0')
        nodules = candidates_regions.filter(lambda line: line[-1] == '1')

        candidates_regions = (
            nodules.count().flat_map(lambda nodules_count: no_nodules.take(nodules_count))
            .concat(nodules)
            .map(utils.gen_world_coord)
            .map(get_voxel_coord)
        )

        slices = Observable.from_(image_arr).map(utils.normalize_planes)
        
        print(f"Processing exam {patient_id}")
        return (
            # group candidates by z coord
            candidates_regions.group_by(lambda el: el[0])
            .flat_map(
            # build dictionaire with z coord as key and x,y coords and class as values
                lambda obs: obs.reduce(
                    lambda acc, curr: {
                        curr[0]: [*acc.get(curr[0], []), curr[1:]]
                    },
                    {},
                )
            )
            .tap(lambda el: print(f"Saved slice {[*el.keys()][0]}"))
            .flat_map(
                lambda el: slices.element_at([*el.keys()][0]).map(
                    lambda image: {
                        "coords": el[[*el.keys()][0]],
                        "image": (image * 255).astype("uint8"),
                    }
                )
            )
            .to_list()
            .tap(lambda lst: np.save(f"./{output_path}/{patient_id}.npy", np.array(lst)) if lst != [] else None)
        )

    return _main


if __name__ == "__main__":
    limit, config = utils.get_running_params()

    INPUT_PATH = config.get("INPUT_PATH")
    OUTPUT_PATH = config.get("OUTPUT_PATH")
    CAND_PATH = config.get("CAND_PATH")
    BIN_OUTPUT_PATH = config.get("BIN_OUTPUT_PATH")

    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(loop)
    candidates = utils.read_csv(CAND_PATH)

    # scandir returns a iterator of os.DirEntry
    with os.scandir(INPUT_PATH) as subset:
        sub = (
            Observable.from_(subset, scheduler=scheduler)
            .filter(lambda file: file.name.endswith(".mhd"))
            .take(
                limit
                # pluck_attr get the path attribute of each emitted object
            )
            .buffer_with_count(2)
            .flat_map(lambda el, ind: Observable.from_(el).delay(1e4 * ind))
            .pluck_attr("path")
            .flat_map(main(candidates, OUTPUT_PATH, BIN_OUTPUT_PATH))
            .subscribe(on_completed=lambda: loop.call_soon_threadsafe(loop.stop))
        )

        loop.run_forever()
        sub.dispose()
