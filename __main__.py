import argparse
import logging
import os
from dataclasses import dataclass
from glob import glob
from typing import Final

from attr import field

from module import (SBI, SBI_ICP_Registration, VolumeLoader, VolumePath,
                    VolumeSaver, VolumeSeries, logger)

try:
    import coloredlogs
    coloredlogs.install(level=logging.INFO)
except:
    pass

version: Final[str] = '0.1'

@dataclass
class CommandParameters(object):
    source: str = field(init=False)

    def __init__(self, args):
        assert args.source is not None
        self.source = args.source

        if self.source.endswith('/') or self.source.endswith('\\'):
            self.source = self.source[:-1]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SBI-ICP registration') 
    parser.add_argument('-s', '--source', type=str, help='indicate source directory.')
    parser.add_argument('-v', '--version', action='store_true', help='show version information')

    args = parser.parse_args()

    if args.version == True:
        logger.info(f'SBI-ICP registration version {version}. Author: Shota Teramoto. Copyright (C) 2022 National Agriculture and Food Research Organization. All rights reserved.')
        exit()

    if args.source is None:
        logger.error(f'Specify the directory to be processed.')
        exit(1)

    command_params = CommandParameters(args=args)

    root_directory_list = sorted(glob(command_params.source+'/**/', recursive=True))
    root_directory_list = [root_directory for root_directory in root_directory_list if VolumeSeries(root_directory=root_directory).does_contain_volumes()]

    for root_directory in root_directory_list:
        volume_series = VolumeSeries(root_directory=root_directory)
        
        #// **** making SBI files ****
        logger.info(f'Making SBI files: {root_directory}')
        for volume_path in volume_series.volume_list:
            if os.path.isfile(VolumePath(directory_name=volume_path).SBI_pcd_name):
                logger.error(f'[skip] SBI file of "{volume_path}" already exists.')
                continue

            volume = VolumeLoader(source=volume_path).load()
            sbi = SBI().get_point_cloud_data(np_volume=volume)
            sbi.save(VolumePath(directory_name=volume_path).SBI_pcd_name)

        #// **** performing SBI-ICP registration ****
        logger.info(f'Performing SBI-ICP registration: {root_directory}')

        if len(volume_series.volume_list) == 0:
            continue

        target_sbi = SBI().load(load_path=VolumePath(volume_series.volume_list[0]).SBI_pcd_name)
        for volume_name in volume_series.volume_list:
            destination_directory = VolumePath(volume_name).registrated_volume_directory_name
            if os.path.isdir(destination_directory):
                logger.error(f'[skip] The registrated volume already exists: {destination_directory}')
                continue

            np_volume = VolumeLoader(source=volume_name).load()
            source_sbi = SBI().load(load_path=VolumePath(volume_name).SBI_pcd_name)
            
            sbi_icp_registration = SBI_ICP_Registration(source_volume=np_volume, source_sbi=source_sbi, target_sbi=target_sbi)
            np_array = sbi_icp_registration.perform()

            VolumeSaver(
                destination_directory=destination_directory,
                np_volume=np_array
            ).save()
