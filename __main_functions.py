
import os
from dataclasses import dataclass
from typing import Any

import numpy as np
import open3d as o3d
from PIL import Image
from scipy.ndimage import interpolation
from skimage import filters, io, measure

import __initialize

try:
    import cupy as cp
    from cupyx.scipy.ndimage import interpolation as cp_interpolation

    pool = cp.cuda.MemoryPool(cp.cuda.malloc_managed)
    cp.cuda.set_allocator(pool.malloc)

    is_cupy_available = True
except:
    is_cupy_available = False

logger = __initialize.logger

@dataclass
class VolumePath(object):
    indir: str

    def __post_init__(self):
        if self.indir.endswith('/') or self.indir.endswith('\\'):
            self.indir = self.indir[:-1]

    def SBI_pcd_path(self):
        dir_name, base_name = os.path.split(self.indir)
        base_name = '.'+base_name+'_SBI.pcd'
        return os.path.join(dir_name, base_name)

    def registrated_volume_path(self):
        dir_name, base_name = os.path.split(self.indir)
        base_name = '.'+base_name+'_registrated'
        return os.path.join(dir_name, base_name)

@dataclass
class Volume3D(object):
    ndarray: Any

    def np_volume(self):
        return self.ndarray

    def Otsu_threshold(self):
        return filters.threshold_otsu(self.np_volume()[self.np_volume()>0])

    def histogram(self, zero_start = False):
        np_volume = self.np_volume()
        np_min = 0 if zero_start else np_volume.min()

        hist_y, _ = np.histogram(
            np_volume[np_volume>0], 
            bins=int(np_volume.max()-np_min+1),
            range=(np_min, np_volume.max())
        )

        return list(range(np_min, np_min+len(hist_y))), hist_y

    def save(self, outdir: str):
        logger.info(f'Saving registrated volume: {outdir}')
        os.makedirs(outdir, exist_ok=True)

        for i, img in enumerate(self.ndarray):
            out = os.path.join(outdir, f'img{str(i).zfill(4)}.tif')
            pil_img = Image.new(**{'mode': 'I;16', 'size': img.T.shape})
            pil_img.frombytes(img.tobytes(), 'raw', 'I;16')
            pil_img.save(out)

@dataclass
class SBI(object):
    volume: Volume3D

    def scan_interval_for_SBI(self):
        return 128

    def np_volume(self):
        return self.volume.ndarray

    def get_Otsu_threshold(self):
        return filters.threshold_otsu(self.np_volume()[self.np_volume()>0])

    def get_threshold_for_SBI(self):
        np_volume = self.volume.np_volume()
        np_volume = np_volume[len(np_volume)//4:len(np_volume)//4*3]

        target_volume = Volume3D(np_volume[np_volume>0])
        hist_x, hist_y = target_volume.histogram(zero_start=False)
        Otsu_thre = target_volume.Otsu_threshold()
        
        hist_y = hist_y[Otsu_thre-hist_x[0]:]
        hist_x = hist_x[Otsu_thre-hist_x[0]:]

        peak_index = np.argmax(hist_y)
        while(peak_index+self.scan_interval_for_SBI() < len(hist_x)):
            if hist_y[peak_index]-hist_y[peak_index+self.scan_interval_for_SBI()] <= 0:
                break
            peak_index += self.scan_interval_for_SBI()
        
        return hist_x[peak_index]

    def get_point_cloud_data(self):
        logger.info('Generating point cloud data.')

        np_volume = self.volume.np_volume()
        np_volume = np_volume[len(np_volume)//4:len(np_volume)//4*3]

        thr = self.get_threshold_for_SBI()
        mask = np.asarray((np_volume > thr))
        xyz = []

        label = measure.label(mask)
        properties = measure.regionprops(label)

        for p in properties:
            xyz.append([p.centroid[2]-np_volume.shape[2]//2, np_volume.shape[1]-p.centroid[1]-1-np_volume.shape[1]//2, 0])

        xyz = np.array(xyz)
        sbi_pcd = o3d.geometry.PointCloud()
        sbi_pcd.points = o3d.utility.Vector3dVector(xyz)
        
        logger.info(sbi_pcd.__str__())

        return sbi_pcd

@dataclass
class SBI_ICP_Registration(object):
    source_volume: Volume3D
    source_sbi: Any
    target_sbi: Any

    def __post_init__(self):
        self.parameters = {}

    def calculate(self):
        logger.info("Calculating SBI-ICP registration parameters.")

        reg_p2p = o3d.pipelines.registration.registration_icp(self.source_sbi, self.target_sbi, 100)
        try:
            degree = np.math.degrees(np.math.asin(reg_p2p.transformation[1][0]))
        except:
            degree = 0.

        shift_y = -round(reg_p2p.transformation[1][3])
        shift_x = round(reg_p2p.transformation[0][3])

        self.parameters = {'degree': round(degree, 2), 'shift_x': shift_x, 'shift_y': shift_y}
        logger.info(f'Registration parameters: {self.parameters}')

        return self.parameters

    def perform(self):
        if len(self.parameters) == 0:
            self.calculate()

        logger.info("Performing SBI-ICP registration.")

        if is_cupy_available == False:
            np_array = self.source_volume.ndarray.copy()
            mask = np_array == 0

            np_array = interpolation.rotate(np_array, self.parameters['degree'], axes=(1,2), reshape=False, prefilter=False, order=1)
            np_array[mask] = 0

            np_array = np.array(np.roll(np_array, (self.parameters['shift_y'], self.parameters['shift_x']), axis=(1,2)))

            return Volume3D(np_array)
        else:
            np_array = self.source_volume.ndarray.copy()
            cp_array = cp.array(np_array)

            mask = cp_array == 0
            cp_array = cp_interpolation.rotate(cp_array, self.parameters['degree'], axes=(1,2), reshape=False, prefilter=False, order=1)
            cp_array[mask] = 0

            cp_array = cp.roll(cp_array, (self.parameters['shift_y'], self.parameters['shift_x']), axis=(1,2))
            return Volume3D(cp_array.get())


class VolumeLoader(object):
    def __init__(self) -> None:
        super().__init__()

    def extensions(self):
        return ('.cb', '.png', '.tif', '.tiff', '.jpg', '.jpeg')

    def minimum_file_number(self):
        return 64

    def load(self, indir: str):
        error_msg = f'Failed to load image files in "{indir}".'
        if not os.path.isdir(indir):
            logger.error(error_msg)
            raise Exception(error_msg)

        img_files = [os.path.join(indir, f) for f in os.listdir(indir) if not f.startswith('.')]
        ext_count = []
        for ext in self.extensions():
            ext_count.append(len([f for f in img_files if f.lower().endswith(ext)]))

        target_ext = self.extensions()[ext_count.index(max(ext_count))]

        self.img_files = [f for f in img_files if f.lower().endswith(target_ext)]
        self.img_files.sort()

        if len(self.img_files) < self.minimum_file_number():
            logger.error(error_msg)
            raise Exception(error_msg)

        logger.info(f'Loading {len(self.img_files)} image files in "{indir}"')

        ndarray = np.array(
            [io.imread(f) for f in self.img_files]
        )

        return Volume3D(ndarray)


