import os
import re
from shutil import copy
from operator import itemgetter

from rx import Observable


PATH_MASK = "./images0/1.3.6.1.4.1.14519.5.2.1.6279.6001.317087518531899043292346860596"
PATH_IMAGE = (
    "./images0_bin/1.3.6.1.4.1.14519.5.2.1.6279.6001.317087518531899043292346860596"
)

OUTPUT_MASK = "./images0_masks"
OUTPUT_IMAGE = "./images0_images"


def get_z(name):
    return re.findall("(\d+)", name)[0]


def is_in_masks(file=None, masks=None):
    return get_z(file) in masks


obs_mask = (
    Observable.from_(os.listdir(PATH_MASK))
    .filter(lambda value: value.endswith("color_mask.png"))
    .tap(lambda filename: copy(PATH_MASK + "/" + filename, OUTPUT_MASK))
    .map(get_z)
    .to_list()
)


obs_images = Observable.from_(os.listdir(PATH_IMAGE))


obs_masks_repeated = obs_images.count().flat_map(lambda el: obs_mask.repeat(el))


sub = (
    obs_images.zip(obs_masks_repeated, lambda file, mask: {"file": file, "masks": mask})
    .filter(lambda data: is_in_masks(**data))
    .map(itemgetter("file"))
    .tap(lambda filename: copy(PATH_IMAGE + "/" + filename, OUTPUT_IMAGE))
    .subscribe(print)
)

sub.dispose()
