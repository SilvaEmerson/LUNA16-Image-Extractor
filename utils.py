import csv
import os
import argparse
import json
from typing import List, Tuple, Dict

import yaml
import numpy as np
import SimpleITK as sitk
from rx import Observable
from PIL import Image

# import keras as K


# KerasModel = K.engine.training.Model


def persist_json(images):
    with open("./images.json", "w+") as file:
        json.dump(images, file)


def split_image(image, n_dim_x, n_dim_y):
    """receive images and split
    n_dim_x = number of slices in vertical axis
    n_dim_y = number of slices in vertical axis
    """
    new_arr = []
    try:
        arr = np.array_split(image, n_dim_y, axis=1)
        [
            [
                new_arr.append(nest_piece)
                for nest_piece in np.array_split(piece, n_dim_x)
            ]
            for piece in arr
        ]
    except Exception as e:
        print(e)
    return new_arr


def get_file_configs(yaml_config_file: str) -> List[str]:
    """Read a `.yaml` config file and returns such configs variables
    Parameters
    ----------
    yaml_config_file : A `.yaml` config file

    Returns
    -------
    The config variables in the file
    """
    with open(yaml_config_file, "r") as file:
        file_content = yaml.load(file)
    return file_content


def load_itk_image(filename: str) -> Tuple["NpArray", "NpArray", "NpArray"]:
    itkimage = sitk.ReadImage(filename)
    image_arr = sitk.GetArrayFromImage(itkimage)

    numpy_origin = np.array(list(reversed(itkimage.GetOrigin())))
    numpy_spacing = np.array(list(reversed(itkimage.GetSpacing())))

    return image_arr, numpy_origin, numpy_spacing


def read_csv(filename: str, cand_id: str) -> Observable:
    file = open(filename, "r")
    return (
        Observable.from_(csv.reader(file))
        .filter(lambda line: line[0] == cand_id)
        .finally_action(lambda: file.close())
    )


def world_to_voxel_coord(
    origin: "NpArray", spacing: "NpArray", world_coord: "NpArray"
) -> "NpArray":
    is_nodule = world_coord[-1]
    world_coord = world_coord[:-1]
    stretched_voxel_coord = np.absolute(world_coord - origin)
    voxel_coord = stretched_voxel_coord // spacing
    return np.append(voxel_coord, is_nodule)


def gen_world_coord(cand):
    """
    Returns the candidate global coord
    """
    return np.asarray(
        [float(cand[3]), float(cand[2]), float(cand[1]), float(cand[-1])]
    )


def normalize_planes(image: "NpArray") -> "NpArray":
    max_HU = 400.0
    min_HU = -1000.0

    image = (image - min_HU) / (max_HU - min_HU)
    image[image > 1] = 1.0
    image[image < 0] = 0.0
    return image


def save_scan(
    patient_id: str,
    image: "NpArray" = None,
    z_coord: int = None,
    output_path: str = None,
    file_format: str = "tiff",
) -> None:
    """Receive a patient id and save on disk a image of a slice at a z coord 
    Parameters
    ----------
    patient_id : A `.yaml` config file
    image: Numpy array
    z_coord: the slice z coord
    output_path: file path to save the image
    file_format: output file format
    """

    image_name = f"image_{z_coord}_{patient_id}.{file_format}"

    if not os.path.isfile(os.path.join(output_path, image_name)):
        if file_format != "npy":
            Image.fromarray(image * 255).convert("L").save(
                os.path.join(output_path, image_name)
            )
        else:
            np.save(os.path.join(output_path, image_name), image * 255)

        print(f"{image_name} saved!")


def get_running_params() -> Tuple[int, Dict[str, str]]:
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

    return limit, get_file_configs(config_file)
