import numpy as np
import os
import re
import utils


def main(cand_path, output_path):
    def _(img_path):
        numpyImage, numpyOrigin, numpySpacing = utils.load_itk_image(img_path)

        # capture the pacient id by regexp
        patient_id = re.findall("^.*\/(.*).mhd$", img_path)[0]

        # get candidates of the pacient
        cands = utils.read_csv(cand_path, patient_id)

        for cand in cands:
            worldCoord = np.asarray([float(cand[3]), float(cand[2]), float(cand[1])])
            voxelCoord = utils.world_to_voxel_coord(
                worldCoord, numpyOrigin, numpySpacing
            )

            # get z coordenate of scan
            z_coord = int(voxelCoord[0])
            image = utils.normalize_planes(numpyImage[z_coord])
            utils.save_scan(image, output_path, patient_id, z_coord)
            print("Image saved")

    return _


if __name__ == "__main__":
    OUTPUT_PATH = "./images0"
    CAND_PATH = "./CSVFILES/candidates.csv"

    # scandir returns a iterator of os.DirEntry
    with os.scandir("./subset0") as subset:
        mhd_files = filter(lambda inst: inst.name.endswith(".mhd"), subset)
        mhd_filenames = [*map(lambda inst: inst.path, mhd_files)][:2]
        [*map(main(CAND_PATH, OUTPUT_PATH), mhd_filenames)]
        print("Sucess")
