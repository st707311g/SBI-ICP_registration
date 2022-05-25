import argparse
import os
import shutil
from glob import glob

from __common import DESCRIPTION, REGISTRATED_DESTINATION, logger
from __module import (SBI, SBI_ICP_Registration, VolumeLoader, VolumePath,
                      VolumeSaver, VolumeSeries)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=DESCRIPTION) 
    parser.add_argument('-s', '--source', type=str, help='Indicate source directory')

    args = parser.parse_args()

    if args.source is None:
        parser.print_help()
        exit()

    source_directory: str = args.source
    if source_directory.endswith('/') or source_directory.endswith('\\'):
        source_directory = source_directory[:-1]
    
    if not os.path.isdir(source_directory):
        logger.error(f'Indicate valid directory path.')
        exit()

    root_directory_list = sorted(glob(source_directory+'/**/', recursive=True))
    root_directory_list = [root_directory for root_directory in root_directory_list if VolumeSeries(root_directory=root_directory).does_contain_volumes()]

    for root_directory in root_directory_list:
        volume_series = VolumeSeries(root_directory=root_directory)
        
        #// **** making SBI files ****
        logger.info(f'Making SBI files: {root_directory}')
        destination_directory = os.path.join(root_directory, REGISTRATED_DESTINATION)
        os.makedirs(destination_directory, exist_ok=True)

        for volume_directory in volume_series.volume_list:
            sbi_file = VolumePath(directory=volume_directory).SBI_pcd_file
            if os.path.isfile(sbi_file):
                logger.error(f'[skip] The SBI file already exists: {sbi_file}')
                continue

            volume = VolumeLoader(source_directory=volume_directory).load()
            sbi = SBI().get_point_cloud_data(np_volume=volume)
            sbi.save(sbi_file)

        #// **** performing SBI-ICP registration ****
        logger.info(f'Performing SBI-ICP registration: {root_directory}')

        if volume_series.volume_number == 0:
            continue

        target_sbi = SBI().load(sbi_file=VolumePath(volume_series.volume_list[0]).SBI_pcd_file)
        for volume_directory in volume_series.volume_list:
            destination_directory = VolumePath(volume_directory).registrated_volume_directory
            volume_information_source = volume_directory+'/.volume_information'
            volume_information_destination = destination_directory+'/.volume_information'

            if os.path.isdir(destination_directory):
                logger.error(f'[skip] The registrated volume already exists: {destination_directory}')
                continue

            np_volume = VolumeLoader(source_directory=volume_directory).load()
            source_sbi = SBI().load(sbi_file=VolumePath(volume_directory).SBI_pcd_file)

            sbi_icp_registration = SBI_ICP_Registration(source_volume=np_volume, source_sbi=source_sbi, target_sbi=target_sbi)
            np_array = sbi_icp_registration.perform()

            VolumeSaver(
                destination_directory=destination_directory,
                np_volume=np_array
            ).save()

            if os.path.isfile(volume_information_source):
                shutil.copyfile(volume_information_source, volume_information_destination)
