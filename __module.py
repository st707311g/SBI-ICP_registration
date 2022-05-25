import os
from dataclasses import dataclass
from glob import glob
from typing import Any, Tuple

import numpy as np
import open3d as o3d
from attr import field
from scipy.ndimage import interpolation
from skimage import io, measure

try:
    import cupy as cp
    from cupyx.scipy.ndimage import interpolation as cp_interpolation

    pool = cp.cuda.MemoryPool(cp.cuda.malloc_managed)
    cp.cuda.set_allocator(pool.malloc)

    is_cupy_available = True
except:
    is_cupy_available = False

from __common import REGISTRATED_DESTINATION, logger, tqdm


@dataclass(frozen=True)
class VolumePath(object):
    directory: str
    registrated_directory: str = REGISTRATED_DESTINATION

    def __post_init__(self):
        if self.directory.endswith('/') or self.directory.endswith('\\'):
            object.__setattr__(self, 'directory', self.directory[:-1])

    @property
    def SBI_pcd_file(self):
        dir_name, base_name = os.path.split(self.directory)
        destination = dir_name+'/'+self.registrated_directory+'/'+base_name+'_SBI.pcd'
        return destination

    @property
    def registrated_volume_directory(self):
        dir_name, base_name = os.path.split(self.directory)
        destination = dir_name+'/'+self.registrated_directory+'/'+base_name
        return destination

@dataclass(frozen=True)
class VolumeLoader(object):
    source_directory: str
    minimum_file_number: int = 64
    extensions: Tuple = ('.cb', '.png', '.tif', '.tiff', '.jpg', '.jpeg')

    def __post_init__(self):
        assert os.path.isdir(self.source_directory)

    @property
    def image_file_list(self):
        img_files = [os.path.join(self.source_directory, f) for f in os.listdir(self.source_directory)]

        ext_count = []
        for ext in self.extensions:
            ext_count.append(len([f for f in img_files if f.lower().endswith(ext)]))

        target_extension = self.extensions[ext_count.index(max(ext_count))]
        return sorted([f for f in img_files if f.lower().endswith(target_extension)])

    @property
    def image_file_number(self):
        return len(self.image_file_list)

    def is_volume_directory(self):
        return self.image_file_number >= self.minimum_file_number

    def load(self) -> np.ndarray:
        assert os.path.isdir(self.source_directory)

        logger.info(f'Loading {self.image_file_number} image files: {self.source_directory}')

        ndarray = np.array(
            [io.imread(f) for f in tqdm(self.image_file_list)]
        )

        return ndarray

@dataclass(frozen=True)
class VolumeSaver(object):
    destination_directory: str
    np_volume: np.ndarray

    def __post_init__(self):
        assert len(self.np_volume) != 0

    def save(self):
        os.makedirs(self.destination_directory, exist_ok=True)

        logger.info(f'Saving {self.np_volume.shape[0]} image files: {self.destination_directory}')
        for i, img in enumerate(tqdm(self.np_volume)): #type: ignore
            image_file = os.path.join(self.destination_directory, f'img{str(i).zfill(4)}.jpg')
            io.imsave(image_file, img)

@dataclass(frozen=True)
class VolumeSeries(object):
    root_directory: str

    def __post_init__(self):
        assert os.path.isdir(self.root_directory)
        
    @property
    def volume_list(self):
        __volume_list = sorted(glob(self.root_directory+'/**/'))
        __volume_list = [source for source in __volume_list if VolumeLoader(source).is_volume_directory()]
        return __volume_list

    @property
    def volume_number(self):
        return len(self.volume_list)

    def does_contain_volumes(self):
        return self.volume_number > 0

@dataclass(frozen=True)
class SBI(object):
    point_cloud_data: Any = field(init=False)

    def get_point_cloud_data(self, np_volume: np.ndarray):
        logger.info('Generating point cloud data.')

        np_volume = np_volume[len(np_volume)//4:len(np_volume)//4*3]

        mask = np.array(np_volume == 255)
        xyz = []

        label = measure.label(mask)
        properties = measure.regionprops(label)

        for p in properties:
            xyz.append([p.centroid[2]-np_volume.shape[2]//2, np_volume.shape[1]-p.centroid[1]-1-np_volume.shape[1]//2, 0])

        xyz = np.array(xyz)
        sbi_pcd = o3d.geometry.PointCloud()
        sbi_pcd.points = o3d.utility.Vector3dVector(xyz)
        
        logger.info(sbi_pcd.__str__())

        return SBI(sbi_pcd)

    def save(self, save_path: str):
        assert isinstance(self.point_cloud_data, o3d.geometry.PointCloud)

        logger.info(f'Point cloud data saved: {save_path}')
        o3d.io.write_point_cloud(
            save_path,
            self.point_cloud_data
        )

    def load(self, sbi_file: str):
        assert os.path.isfile(sbi_file)

        logger.info(f'Point cloud data saved: {sbi_file}')
        return SBI(point_cloud_data=o3d.io.read_point_cloud(sbi_file))


@dataclass(frozen=True)
class SBI_ICP_Registration(object):
    source_volume: np.ndarray
    source_sbi: SBI
    target_sbi: SBI

    @dataclass(frozen=True)
    class Parameters(object):
        degree:float = 0.
        shift_x: int = 0
        shift_y: int = 0

    def calculate(self):
        logger.info("Calculating SBI-ICP registration parameters.")

        reg_p2p = o3d.pipelines.registration.registration_icp(self.source_sbi.point_cloud_data, self.target_sbi.point_cloud_data, 100)
        try:
            degree = np.math.degrees(np.math.asin(reg_p2p.transformation[1][0]))
        except:
            degree = 0.

        shift_y = -round(reg_p2p.transformation[1][3])
        shift_x = round(reg_p2p.transformation[0][3])

        center = self.target_sbi.point_cloud_data.get_center()

        parameters = self.Parameters(
            degree = round(degree, 2),
            shift_x = shift_x-round(center[0]),
            shift_y = shift_y+round(center[1])
        )
        logger.info(f'Registration parameters: {parameters}')

        return parameters

    def perform(self):
        parameters = self.calculate()

        logger.info("Performing SBI-ICP registration.")

        if is_cupy_available == False:
            np_array = self.source_volume.copy()

            np_array = interpolation.rotate(np_array, parameters.degree, axes=(1,2), reshape=False, prefilter=False, order=1)

            np_array_shape = np_array.shape
            np_array = np.pad(
                np_array, 
                pad_width=(
                    (0,0),
                    (abs(parameters.shift_y),abs(parameters.shift_y)),
                    (abs(parameters.shift_x),abs(parameters.shift_x))
                )
            )
            np_array = np_array[
                :, 
                abs(parameters.shift_y)-parameters.shift_y:abs(parameters.shift_y)+np_array_shape[1]-parameters.shift_y, 
                abs(parameters.shift_x)-parameters.shift_x:abs(parameters.shift_x)+np_array_shape[2]-parameters.shift_x
            ]
            return np_array
        else:
            np_array = self.source_volume.copy()
            cp_array = cp.array(np_array)

            cp_array = cp_interpolation.rotate(cp_array, parameters.degree, axes=(1,2), reshape=False, prefilter=False, order=1)

            cp_array_shape = cp_array.shape
            cp_array = cp.pad(
                cp_array, 
                pad_width=(
                    (0,0),
                    (abs(parameters.shift_y),abs(parameters.shift_y)),
                    (abs(parameters.shift_x),abs(parameters.shift_x))
                )
            )
            cp_array = cp_array[
                :, 
                abs(parameters.shift_y)-parameters.shift_y:abs(parameters.shift_y)+cp_array_shape[1]-parameters.shift_y, 
                abs(parameters.shift_x)-parameters.shift_x:abs(parameters.shift_x)+cp_array_shape[2]-parameters.shift_x
            ]

            return cp_array.get()
