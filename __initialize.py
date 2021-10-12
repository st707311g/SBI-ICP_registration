import argparse
import logging
import sys
from typing import Final

logger = logging.getLogger('SBI_ICP_registration')
logger.setLevel(logging.INFO)

pil_logger = logging.getLogger('PIL')
pil_logger.setLevel(logging.INFO)

version: Final[str] = '0.1'

try:
    import coloredlogs
    coloredlogs.install(level=logging.INFO)
except:
    pass

def arg_parse():
    parser = argparse.ArgumentParser(description='SBI-ICP registration') 
    parser.add_argument('-s', '--source', type=str, help='Source volume name.')
    parser.add_argument('-t', '--target', type=str, help='Target volume name.')
    parser.add_argument('-p', '--point_cloud', action='store_true', help='Saving SBI point cloud data.')
    parser.add_argument('-r', '--registration', action='store_true', help='Saving registrated volume. Indicate target volume with "-t" option.')
    parser.add_argument('-v', '--version', action='store_true', help='Showing version information')

    args = parser.parse_args()

    if args.version:
        print(f'Version: {version}')
        sys.exit()

    if args.source is None:
        parser.print_help()
        sys.exit(1)

    return (args, parser)

