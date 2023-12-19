#!/usr/bin/env python

from argparse import ArgumentParser
import logging
import os
import shutil
import subprocess
import sys
import time
import glob

from yang_generator import YangkitGenerator
from yang_generator.common import YangkitGenException


logger = logging.getLogger('yangkitgen')


def init_verbose_logger():
    """ Initialize the logging infra and add a handler """
    logger.setLevel(logging.DEBUG)

    # create a console logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # add the handlers to the logger
    logger.addHandler(ch)


def create_pip_packages(out_dir):
    py_sdk_root = out_dir
    os.chdir(py_sdk_root)
    shutil.rmtree('dist', ignore_errors=True)
    args = [sys.executable, 'setup.py', 'sdist']
    exit_code = subprocess.call(args, env=os.environ.copy())

    if exit_code == 0:
        print('\nSuccessfully created source distribution')
    else:
        print('\nFailed to create source distribution')
        sys.exit(exit_code)


def copy_file(source_folder, destination_folder, file_extention):
    files = glob.glob(os.path.join(source_folder, file_extention))
    source_file = files[0]
    destination_file = os.path.join(destination_folder, os.path.basename(source_file))
    shutil.copy2(source_file, destination_file)

def _get_time_taken(start_time):
    end_time = time.time()
    uptime = end_time - start_time
    minutes = int(uptime / 60) if int(uptime) > 60 else 0
    seconds = int(uptime) % (60 * minutes) if int(uptime) > 60 else int(uptime)
    minutes_str = str(minutes) + ' minutes' if int(uptime) > 60 else ''
    seconds_str = str(seconds) + ' seconds'
    return minutes_str, seconds_str


def get_python_version():
    import sysconfig
    python_version = sysconfig.get_config_var('LDVERSION')
    if python_version is None or len(python_version) == 0:
        python_version = sysconfig.get_config_var('VERSION')
    return python_version


if __name__ == '__main__':
    start_time = time.time()

    parser = ArgumentParser(description='Generate YANGKIT artifacts:')

    parser.add_argument(
        "--bundle",
        type=str,
        required=True,
        help="Location of bundle profile JSON file")

    parser.add_argument(
        "--output-directory",
        type=str,
        required=True,
        help="The output directory where the sdk will get created.")

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Verbose mode")

    parser.add_argument(
        "-i", "--ignore_pyang_errors",
        action="store_true",
        default=False,
        help="Ignore Pyang Validation Errors")

    options = parser.parse_args()

    if options.verbose:
        init_verbose_logger()

    yangkit_root = os.getcwd()
    output_directory = options.output_directory
    ignore_pyang_errors = options.ignore_pyang_errors

    try:
        if options.bundle:
            generator = YangkitGenerator(
                output_directory,
                yangkit_root,
                'bundle',
                ignore_pyang_errors)

            output_directory, pyang_errors_list = (generator.generate(options.bundle))
    except YangkitGenException as e:
        print('\nError(s) occurred in YangkitGenerator()!\n')
        print(e.msg)
        sys.exit(1)

    create_pip_packages(output_directory)
    package = generator.package_type
    if generator.package_name != '':
        package = '%s %s' % (generator.package_name, package)
    destination_folder = os.path.dirname(output_directory)
    copy_file(f"{output_directory}/dist", destination_folder, "*.tar.gz")
    copy_file(output_directory, destination_folder, "*.md")
    shutil.rmtree(output_directory)
    print('\n=================================================')
    print('Successfully generated Python Yangkit %s package at %s' % (package, destination_folder))
    print('Please refer to the README for information on how to install the package in your environment')
    print('\nCode generation completed successfully!  Manual installation required!')

    minutes_str, seconds_str = _get_time_taken(start_time)
    print('\nTotal time taken: {0} {1}\n'.format(minutes_str, seconds_str))

    if ignore_pyang_errors and len(pyang_errors_list) > 0:
        for error_line in pyang_errors_list:
            logger.warning(error_line)





