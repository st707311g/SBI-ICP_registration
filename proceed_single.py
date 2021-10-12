import os
import sys

import open3d as o3d

import __initialize
from __main_functions import (SBI, SBI_ICP_Registration, VolumeLoader,
                              VolumePath)

logger = __initialize.logger

def make_SBI_point_cloud(source_dir: str):
    sbi_pcd_file = VolumePath(source_dir).SBI_pcd_path()

    if os.path.isfile(sbi_pcd_file):
        logger.info(f'[skip] SBI point cloud data already exists: {sbi_pcd_file}')
    else:
        volume = VolumeLoader().load(source_dir)
        sbi_pcd = SBI(volume).get_point_cloud_data()
        
        o3d.io.write_point_cloud(
            sbi_pcd_file,
            sbi_pcd
        )
        logger.info(f'Point cloud data saved as "{sbi_pcd_file}"')

        return (volume, sbi_pcd)

def perform_ICP_registration(source_dir: str, target_dir: str):
    sbi_pcd_file_source = VolumePath(source_dir).SBI_pcd_path()
    sbi_pcd_file_target = VolumePath(target_dir).SBI_pcd_path()

    if not os.path.isfile(sbi_pcd_file_source):
        ret = make_SBI_point_cloud(source_dir)
        assert ret is not None
        volume_source, sbi_pcd_source = ret
    else:
        volume_source = VolumeLoader().load(source_dir)
        sbi_pcd_source = o3d.io.read_point_cloud(sbi_pcd_file_source)
        logger.info(f'Point cloud data loaded :{sbi_pcd_file_source}')

    if not os.path.isfile(sbi_pcd_file_target):
        ret = make_SBI_point_cloud(target_dir)
        assert ret is not None
        volume_target, sbi_pcd_target = ret
        del volume_target
    else:
        sbi_pcd_target = o3d.io.read_point_cloud(sbi_pcd_file_target)
        logger.info(f'Point cloud data loaded :{sbi_pcd_file_target}')

    return SBI_ICP_Registration(volume_source, sbi_pcd_source, sbi_pcd_target).perform()

def make_registrated_volume(source_dir: str, target_dir: str):
    out_path = VolumePath(source_dir).registrated_volume_path()
    if os.path.isdir(out_path):
        error_msg = f'[skip] registrated volume already constructed: {out_path}'
        logger.info(error_msg)
        raise Exception(error_msg)

    registrated_volume = perform_ICP_registration(source_dir, target_dir)
    registrated_volume.save(out_path)

if __name__ == "__main__":
    args, parser = __initialize.arg_parse()
    
    try:
        if args.registration:
            if args.source is None or args.target is None:
                parser.print_help()
                sys.exit(1)

            make_registrated_volume(args.source, args.target)
                
        elif args.point_cloud:
            make_SBI_point_cloud(args.source)
    except:
        pass

