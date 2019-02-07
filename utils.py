import csv
import os
import yaml
from typing import List

import numpy as np
import SimpleITK as sitk
from PIL import Image


def get_env_config(yaml_config_file: str) -> List[str]:
    """Receives a .yaml config file
    Returns the config variables in the file
    """
    with open(yaml_config_file, "r") as file:
        file_content = yaml.load(file)
    return file_content


def load_itk_image(filename):
    itkimage = sitk.ReadImage(filename)
    image_arr = sitk.GetArrayFromImage(itkimage)

    numpy_origin = np.array(list(reversed(itkimage.GetOrigin())))
    numpy_spacing = np.array(list(reversed(itkimage.GetSpacing())))

    return image_arr, numpy_origin, numpy_spacing


def read_csv(filename, cand_id):
    with open(filename, "r") as file:
        return [line for line in csv.reader(file) if line[0] == cand_id]


def world_to_voxel_coord(world_coord, origin, spacing):
    stretchedVoxelCoord = np.absolute(world_coord - origin)
    voxelCoord = stretchedVoxelCoord / spacing
    return voxelCoord


def normalize_planes(image):
    max_HU = 400.0
    min_HU = -1000.0

    image = (image - min_HU) / (max_HU - min_HU)
    image[image > 1] = 1.0
    image[image < 0] = 0.0
    return image


def save_scan(patch, output_path, patient_id, z_coord):
    Image.fromarray(patch * 255).convert("L").save(
        os.path.join(output_path, f"image_{z_coord}_{patient_id}.tiff")
    )
