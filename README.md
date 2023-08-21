### Credits

This project is influenced by the code from the [YDK-GEN Repository](https://github.com/CiscoDevNet/ydk-gen/tree/0.8.6.4), which was/is developed and maintained by the YDK Team.

We extend our sincere appreciation to the YDK Team for their exceptional work on the YDK Project. Their dedication and expertise have significantly enriched our project.

Please note that the YDK Repository is governed by its own license, which you can find in their repository. We recommend reviewing their licensing terms to ensure compliance with the applicable licenses.

</br>

### Yangkit Repository Description

The Yangkit is a software development tool, which provides API for building applications based on YANG models. It generates YANG Model APIs and provides services to apply API Obejcts over various communication protocols.

### Utilized Components

1. Model API Generator : This component generates Python API Package for given Yang Models. The generated package is a PIP Installable tar file. Refer to [Steps to Generate Model API Python package](https://github.com/yang-infra/yangkit#steps-to-generate-model-api-python-package)
2. Codec: This component translates Python API Objects to XML/json and vice-versa.

<br>

### How to use
1. Create a Model API Package. Refer to [Steps to Generate Model API Python package](https://github.com/yang-infra/yangkit#steps-to-generate-model-api-python-package)
2. Install yangkit and the generated Model API Package in your python env using pip
```
pip install git+https://github.com/yang-infra/yangkit
pip install /auto/cafy/yang/models/7_11_1_19I/yangkit-models-cisco-ios-xr-7.11.1.tar.gz
```
3. Refer to [examples](https://github.com/yang-infra/yangkit/tree/main/examples) for code examples

<br>

### Steps to Generate Model API Python package
 
1) Clone the yangkit Github
 
2) Build and source a virtual environment 
```
cd yangkit

## Create and activate your virtual environment 
python3 -m venv yangkit_venv 
source yangkit_venv/bin/activate 
 
## Install Yangkit
pip install --upgrade pip 
pip install git+https://github.com/yang-infra/yangkit
```
 
3) Add and validate yang models 

Copy all the yang models you want to generate APIs for into a folder and compile them using 'pyang' to ensure the validity of the models. 

```
cd <yang-files-dir>
pyang *.yang
```
Note: Refer [Pyang Errors Resolution](https://github.com/yang-infra/yangkit/tree/main#pyang-related-errors-resolution) if you face any pyang related issue.

4) Create a bundle file: Example : /ws/jhanm-sjc/yang-kit/bundle.json
```
(yangkit_venv) [jhanm@sjc-ads-1025 yang-kit]$ pwd
/ws/jhanm-sjc/yang-kit
(yangkit_venv) [jhanm@sjc-ads-1025 yang-kit]$ cat bundle.json 
 {
   "name": "cisco-ios-xr", <Bundle Name>
   "version": "7.11.1", <Image Version>
   "yang_dir": "/ws/jhanm-sjc/yang-kit/yang_files" <Yang Files Directory>
}
(yangkit_venv) [jhanm@sjc-ads-1025 yang-kit]$ 
 ```

5) Generate the Model API python package using below command 

To Run the Script :
(Set Absolute Path - For Both Bundle File & Output Dir) - Mandatory Parameters

- bundle (Input Bundle File)
- output-directory (User directory where the .tar file are gonna get generated)

```
 cd <yangkit Folder Path>/api_generator
./generate.py --bundle <Abosulte Path of Bundle Json File> --output-directory <Absolute Path of Output Directory>
```

6) Generated .tar file will be present in the output directory. This is a pip installable tar file.

```
Writing yangkit-models-cisco-ios-xr-7.11.1/setup.cfg
creating dist
Creating tar archive
removing 'yangkit-models-cisco-ios-xr-7.11.1' (and everything under it)

Successfully created source distribution

=================================================
Successfully generated Python Yangkit cisco-ios-xr bundle package at /ws/jhanm-sjc/yang-kit/generated_models
Please refer to the README for information on how to install the package in your environment

Code generation completed successfully!  Manual installation required!

Total time taken: 7 minutes 23 seconds

(yangkit_venv) [jhanm@sjc-ads-1025 api_generator]$ 
(yangkit_venv) [jhanm@sjc-ads-1025 generated_models]$ pwd
/ws/jhanm-sjc/yang-kit/generated_models
(yangkit_venv) [jhanm@sjc-ads-1025 generated_models]$ ls -lrt
total 38804
-rw-r--r--. 1 jhanm eng      751 Jul  5 03:09 README.md
-rw-r--r--. 1 jhanm eng 39569865 Jul  6 08:43 yangkit-models-cisco-ios-xr-7.11.1.tar.gz
(yangkit_venv) [jhanm@sjc-ads-1025 generated_models]$ 
```

### Pyang Related Errors Resolution

1) Remove such files with this error. This means the yang file is empty.
```
Cisco-IOS-XR-sysadmin-eobc-iosxrwbd.yang:0: error: premature end of file
```

2) Remove oc-deviation files with pyang error.
```
(yangkit_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-optical-amplifier-sirius-deviations.yang
(yangkit_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-platform-deviations-spi.yang
(yangkit_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-platform-deviations-spirit.yang
(yangkit_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-terminal-device-deviations-routing.yang
(yangkit_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf cisco-xr-openconfig-platform-transceiver-deviations.yang
```

3) Fix/remove yang files with unresolved references.
```
Cisco-IOS-XR-sysadmin-controllers-iosxrwbd.yang:20: error: module "Cisco-IOS-XR-sysadmin-eobc-iosxrwbd" not found in search path

(yangkit_venv) [jhanm@sjc-ads-1025 PROD_BUILD_7_11_1_19I_DT_IMAGE]$ rm -rf Cisco-IOS-XR-sysadmin-controllers-iosxrwbd.yang
```

4) Fix/remove yang files with similar errors.
```
openconfig-optical-attenuator.yang:15: error: module "oc-xr-mapping" not found in search path
```

