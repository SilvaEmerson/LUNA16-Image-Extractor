import os
import re
from shutil import copy
from operator import itemgetter
from functools import partial

from rx import Observable


IMAGES_ORIGIN = "./images0_bin"
MASKS_ORIGIN = "./images0"

OUTPUT_MASK = "./images0_masks"
OUTPUT_IMAGE = "./images0_images"


def create_dirs(exam_id):
    image_output_path = os.path.join(OUTPUT_IMAGE, exam_id)
    mask_output_path = os.path.join(OUTPUT_MASK, exam_id)

    if not os.path.isdir(image_output_path):
        os.mkdir(image_output_path)

    if not os.path.isdir(mask_output_path):
        os.mkdir(mask_output_path)


def get_z(name):
    return re.findall("(\d+)", name)[0]


def get_exame_id(filename):
    matchs = re.findall(".*/.*/(.*)", filename)
    return matchs[0]


def is_in_masks(file=None, masks=None):
    return get_z(file) in masks


def copy_to(filename, origin_dir, output_dir):
    output_path = os.path.join(output_dir, get_exame_id(origin_dir))
    copy(os.path.join(origin_dir, filename), output_path)


def main(OUTPUT_IMAGE, OUTPUT_MASK, PATH_IMAGE=None, PATH_MASK=None):
    create_dirs(get_exame_id(PATH_MASK))
    create_dirs(get_exame_id(PATH_IMAGE))

    obs_mask = (
        Observable.from_(os.listdir(PATH_MASK))
        .filter(lambda value: value.endswith("color_mask.png"))
        .tap(lambda filename: copy_to(filename, PATH_MASK, OUTPUT_MASK))
        .map(get_z)
        .to_list()
    )

    obs_images = Observable.from_(os.listdir(PATH_IMAGE))

    obs_masks_repeated = obs_images.count().flat_map(
        lambda el: obs_mask.repeat(el)
    )

    return (
        obs_images.zip(
            obs_masks_repeated,
            lambda file, mask: {"file": file, "masks": mask},
        )
        .filter(lambda data: is_in_masks(**data))
        .map(itemgetter("file"))
        .tap(lambda filename: copy_to(filename, PATH_IMAGE, OUTPUT_IMAGE))
    )


if __name__ == "__main__":

    with os.scandir(MASKS_ORIGIN) as exams:
        Observable.from_(exams).map(
            lambda direc: {
                "PATH_MASK": os.path.join(MASKS_ORIGIN, direc.name),
                "PATH_IMAGE": os.path.join(IMAGES_ORIGIN, direc.name),
            }
        ).flat_map(
            lambda data: main(OUTPUT_IMAGE, OUTPUT_MASK, **data)
        ).subscribe(
            print
        )
