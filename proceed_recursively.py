import glob
import os
import sys

import __initialize
import proceed_single
import proceed_timeseries

logger = __initialize.logger

def make_SBI_point_cloud(source_dir: str):
    dir_list = glob.glob(
        os.path.join(source_dir, '**/'),
        recursive=True
    )

    dir_list = [d for d in sorted(dir_list) if os.path.isdir(d) and not os.path.basename(d).startswith('.')]
    for d in dir_list:
        try:
            proceed_timeseries.make_SBI_point_cloud(d)
        except:
            pass

def make_registrated_volume(source_dir: str):
    dir_list = glob.glob(
        os.path.join(source_dir, '**/'),
        recursive=True
    )
    
    for d in sorted(dir_list):
        if d.endswith('/') or d.endswith('\\'):
            d = d[:-1]

        if not os.path.isdir(d) and os.path.basename(d).startswith('.'):
            continue
        try:
            proceed_timeseries.make_registrated_volume(d)
        except:
            pass

if __name__ == "__main__":
    args, parser = __initialize.arg_parse()
    
    try:
        if args.registration:
            if args.source is None:
                parser.print_help()
                sys.exit(1)

            make_registrated_volume(args.source)
                
        elif args.point_cloud:
            make_SBI_point_cloud(args.source)
    except:
        pass

