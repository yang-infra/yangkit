### Credits

This project incorporates code from the YDK-GEN Repository (https://github.com/CiscoDevNet/ydk-gen/tree/0.8.6.4), developed and maintained by the YDK-GEN Team.

### YDK-GEN Repository Description

The YANG Development Kit (YDK) is a software development tool, which provides API for building applications based on YANG models. The YDK allows generate YANG model API and provides services to apply generated API over various communication protocols.

### Utilized Components

We have leveraged the following components from the YDK-GEN Repository (https://github.com/CiscoDevNet/ydk-gen/tree/0.8.6.4) in our project:

1. [Model API Generator](https://github.com/CiscoDevNet/ydk-gen/blob/0.8.6.4/generate.py): This ydk-gen component provides a module bundle, consisting of python programming language APIs derived from YANG models. Each module bundle is generated using a bundle profile and the ydk-gen tool. Developers can either use pre-packaged generated bundles, or define their own bundle, consisting of a set of YANG models, using a bundle profile. This gives the developer an ability to customize scope of their bundle based on their requirements. We made specific modifications to meet our project's requirements - Took the Python Model API Generator Code Base.


### Acknowledgements

We extend our sincere appreciation to the YDK-GEN Team for their exceptional work on the YDK-GEN Project - (https://github.com/CiscoDevNet/ydk-gen/tree/0.8.6.4). Their dedication and expertise have significantly enriched our project.

We would also like to express our gratitude to the broader community of contributors who have contributed to the YDK-GEN Repository (https://github.com/CiscoDevNet/ydk-gen/tree/0.8.6.4). Their collaborative efforts have made the repository an invaluable resource for developers.

### License

Please note that the YDK-GEN Repository (https://github.com/CiscoDevNet/ydk-gen/tree/0.8.6.4) is governed by its own license, which you can find in their repository. We recommend reviewing their licensing terms to ensure compliance with the applicable licenses.

### Steps to Generate Model Tar File
 
1) Clone the yangkit Github

git clone https://wwwin-github.cisco.com/cafy/yangkit.git
 
2) Build and source a virtual environment 
```
cd yangkit

## Create and activate your virtual environment 
python3 -m venv yang_venv 
source yang_venv/bin/activate 
 
## Install python packages 
## May require additional libraries.  
pip install --upgrade pip 
pip install -r api_generator/requirements.txt
```
 
3) Add and validate yang models 

Get a local copy of the yang models from catchyang repository and compile them using 'pyang' to ensure the validity of the models. 
 
Example: If you want to create bundle tar file for - PROD_BUILD_7_11_1_12I_DT_IMAGE 

Catchyang location (Has all the .yang files): /auto/xmpi/xr-yang/schemas/catchyang/ 
 
Commands: 
 ```
cp /auto/xmpi/xr-yang/schemas/catchyang/PROD_BUILD_7_11_1_12I_DT_IMAGE/consolidated/*.yang <yang-files-dir>
cd <yang-files-dir>
pyang *.yang   
 ```
Example: 
 ```
cp /auto/xmpi/xr-yang/schemas/catchyang/PROD_BUILD_7_11_1_12I_DT_IMAGE/consolidated/*.yang /ws/jhanm-sjc/yang-files 
cd /ws/jhanm-sjc/yang-files
pyang *.yang 
``` 
(Refer to the Note Section at the end of this Readme Doc – If you face any Pyang Related Issues.) 

4) Create a bundle file: Example : /ws/jhanm-sjc/yang-kit/bundle.json
```
(yangkit_venv) [jhanm@sjc-ads-1025 yang-kit]$ pwd
/ws/jhanm-sjc/yang-kit
(yangkit_venv) [jhanm@sjc-ads-1025 yang-kit]$ cat bundle.json 
 {
   "name": "cisco-ios-xr", <Bundle Name>
   "version": "7.11.1", <Image Version>
   "core_version": "0.8.6",
   "yang_dir": "/ws/jhanm-sjc/yang-kit/yang_files" <Yang Files Directory>
}
(yangkit_venv) [jhanm@sjc-ads-1025 yang-kit]$ 
 ```

5) Generate the image using below command 

To Run the Script :
(Set Absolute Path - For Both Bundle File & Output Dir) - Mandatory Parameters

- bundle (Input Bundle File)
- output-directory (User directory where the .tar file are gonna get generated)

 cd <yangkit Folder Path>
./generate.py --bundle <Bundle Json File> --output-directory <Output Directory> -v
 

6) Genetated .tar file will be present in the output directory.

```
Writing ydk-models-cisco-ios-xr-7.11.1/setup.cfg
creating dist
Creating tar archive
removing 'ydk-models-cisco-ios-xr-7.11.1' (and everything under it)

Successfully created source distribution

=================================================
Successfully generated Python YDK cisco-ios-xr bundle package at /ws/jhanm-sjc/yang-kit/generated_models
Please refer to the README for information on how to install the package in your environment

Code generation completed successfully!  Manual installation required!

Total time taken: 7 minutes 23 seconds

(yangkit_venv) [jhanm@sjc-ads-1025 api_generator]$ 
(yangkit_venv) [jhanm@sjc-ads-1025 generated_models]$ pwd
/ws/jhanm-sjc/yang-kit/generated_models
(yangkit_venv) [jhanm@sjc-ads-1025 generated_models]$ ls -lrt
total 38804
-rw-r--r--. 1 jhanm eng      751 Jul  5 03:09 README.md
-rw-r--r--. 1 jhanm eng 39569865 Jul  6 08:43 ydk-models-cisco-ios-xr-7.11.1.tar.gz
(yangkit_venv) [jhanm@sjc-ads-1025 generated_models]$ 
```

### Some Pyang Related Errors Resolution

1) Delete such files with this error
```
Cisco-IOS-XR-sysadmin-eobc-iosxrwbd.yang:0: error: premature end of file
```

2) Removed deviation files with pyang error
```
(086_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-optical-amplifier-sirius-deviations.yang
(086_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-platform-deviations-spi.yang
(086_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-platform-deviations-spirit.yang
(086_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-terminal-device-deviations-routing.yang
(086_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-platform-transceiver-deviations.yang
```

3) Delete these files with such errors
```
Cisco-IOS-XR-sysadmin-controllers-iosxrwbd.yang:20: error: module "Cisco-IOS-XR-sysadmin-eobc-iosxrwbd" not found in search path

(086_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf Cisco-IOS-XR-sysadmin-controllers-iosxrwbd.yang
```

4) Delete the .yang files with similar errors
```
openconfig-optical-attenuator.yang:15: error: module "oc-xr-mapping" not found in search path
```

