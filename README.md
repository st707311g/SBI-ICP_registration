# SBI-ICP_registration: a geometric registration software for time-series 3D volumetric data of planted pots

![python](https://img.shields.io/badge/Python-3.8.12-lightgreen)
![developed_by](https://img.shields.io/badge/developed%20by-Shota_Teramoto-lightgreen)
![version](https://img.shields.io/badge/version-1.0-lightgreen)
![last_updated](https://img.shields.io/badge/last_update-May_25,_2022-lightgreen)

## introduction

SBI-ICP_registration is a geometric registration software for time-series 3D volumetric data of planted pots. SBI (Soil Block Identifier) is a point cloud generated from soil particles with strong signal intensity in soils. Using ICP (Iterative Closest Point) registration of SBIs generated from time-series 3D volumetric data, allowing for the geometric registration.

## system requirements

This software is confirmed to work with Python 3.8.12 on Ubuntu 20.04. If you are using python 3.9 or later, `open3d`, which is required for ICP registration, cannot be installed with `pip`. Please compile `open3d` from source files to create an environment. I recommend creating a virtual environment for python 3.8.12 with `virtualenv`.

## installation

Run the following commands:

```
git clone https://github.com/st707311g/SBI-ICP_registration.git
cd SBI-ICP_registration
```

The following command will install the required packages.

```
pip install -U pip
pip install -r requirements.txt
```

This software can reduce processing time by using `CuPy`. Installation depends on the version of `CUDA Toolkit`. Please build the environment according to your own version of `CUDA Toolkit`. For example, if the version of `CUDA Toolkit` is 11.4, install cupy with the following command.

```
pip install cupy-cuda114
```

Please check if CuPy is available by using the following command.
```
python is_cupy_available.py
```

## demonstration

Download the demo data (1.60G), which is a time-series X-ray CT data of an upland rice cultivar from 7 to 26 days after sowing ([Teramoto et al. 2020 Plant Methods](https://plantmethods.biomedcentral.com/articles/10.1186/s13007-020-00612-6)). The intensity of this data is normalized in the way described in [a github repository](https://github.com/st707311g/RSAvis3D).

```
wget https://rootomics.dna.affrc.go.jp/data/rice_root_daily_growth_intensity_normalized.zip
unzip rice_root_daily_growth_intensity_normalized.zip
```

Run the following command.

```
python . -s rice_root_daily_growth_intensity_normalized
```

The registrated files are stored in the `.registrated` directory in `rice_root_daily_growth_intensity_normalized`.

The confirmed operating environments are shown below:

Environment 1:
- CPU: Intel<sup>(R)</sup> Core<sup>(TM)</sup> i7-8700 CPU @ 3.20 GHz
- GPU: NVIDIA GeForce RTX 2080 Ti
- CUDA Toolkit (11.4)
- Memory: 32 GB
- Ubuntu 20.04.3 LTS
- Python (3.8.12)
    - coloredlogs (15.0.1)
    - cupy-cuda114 (10.4.0)
    - numpy (1.22.4)
    - open3d (0.15.2)
    - scikit-image (0.19.2)
    - tqdm (4.64.0)

Using CPU, the processing time for the demo files was 17 minutes. Using GPU, the processing time for the demo files was 6 minutes.

## version policy

Version information consists of major and minor versions (major.minor). When the major version increases by one, it is no longer compatible with the original version. When the minor version invreases by one, compatibility will be maintained. Revisions that do not affect functionality, such as bug fixes and design changes, will not affect the version number.

## citation

Papers being submitted for publication.

## license

NARO NON-COMMERCIAL LICENSE AGREEMENT Version 1.0

This license is for 'Non-Commercial' use of software for SBI-ICP_registration

* Scientific use of SBI-ICP_registration is permitted free of charge.
* Modification of SBI-ICP_registration is only permitted to the person of downloaded and his/her colleagues.
* The National Agriculture and Food Research Organization (hereinafter referred to as NARO) does not guarantee that defects, errors or malfunction will not occur with respect to SBI-ICP_registration.
* NARO shall not be responsible or liable for any damage or loss caused or be alleged to be caused, directly or indirectly, by the download and use of SBI-ICP_registration.
* NARO shall not be obligated to correct or repair the program regardless of the extent, even if there are any defects of malfunctions in SBI-ICP_registration.
* The copyright and all other rights of SBI-ICP_registration belong to NARO.
* Selling, renting, re-use of license, or use for business purposes etc. of SBI-ICP_registration shall not be allowed. For commercial use, license of commercial use is required. Inquiries for such commercial license are directed to NARO.
* The SBI-ICP_registration may be changed, or the distribution maybe canceled without advance notification.
*In case the result obtained using SBI-ICP_registration in used for publication in academic journals etc., please refer the publication of SBI-ICP_registration and/or acknowledge the use of SBI-ICP_registration in the publication.

Copyright (C) 2022 National Agriculture and Food Research Organization. All rights reserved.

## project homepage
https://rootomics.dna.affrc.go.jp/en/

## update history

* version 1.0 (May 25, 2022)
  * initial version uploaded


