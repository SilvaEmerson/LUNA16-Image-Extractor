import os 
import re
from shutil import copy
from rx import Observable

PATH_MASK = "./images0/1.3.6.1.4.1.14519.5.2.1.6279.6001.105756658031515062000744821260"
PATH_IMAGE = "./images0_bin/1.3.6.1.4.1.14519.5.2.1.6279.6001.105756658031515062000744821260"

OUTPUT_MASK  = "./output/mask/exame_1"
OUTPUT_IMAGE = "./output/image/exame_1"

def get_z(name):
    return re.findall("(\d+)", name)[0]

def compare(filename, arr_filename_mask):
    return get_z(filename) in arr_filename_mask



obs_mask = Observable.from_(os.listdir(PATH_MASK))\
        .filter(lambda value: value.endswith("color_mask.png"))\
        .tap(lambda filename: copy(PATH_MASK + "/" + filename, OUTPUT_MASK))\
        .map(get_z)

obs_image = Observable.from_(os.listdir(PATH_IMAGE))  

obs_compare = obs_image.flat_map(lambda el: obs_mask.contains(get_z(el)))

obs_mask.subscribe(print)

obs_image.zip(obs_compare, lambda el, val: (el, val))\
        .filter(lambda el: el[-1])\
        .map(lambda el: el[0])\
        .tap(lambda filename: copy(PATH_IMAGE + "/" + filename, OUTPUT_IMAGE))\
        .subscribe(print)
