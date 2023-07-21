"""
Generate yangkit core library, bundle packages.
"""

from distutils import dir_util

import fileinput
import json
import logging
import os
import shutil
import tarfile
import tempfile

from .common import YangkitGenException, ispythonkeyword
from yang_generator.builder import (ApiModelBuilder, PyangModelBuilder, SubModuleBuilder)
from .resolver import bundle_resolver, bundle_translator
from yang_generator.printer import printer_factory


logger = logging.getLogger('yangkitgen')
logger.addHandler(logging.NullHandler())

classes_per_source_file = 150
YANGKIT_YANG_MODEL = 'yangkit@2016-02-26.yang'


class YangkitGenerator(object):
    """ YangkitGenerator class, based in the output_directory using the supplied
        profile description file.

        Attributes:
            output_dir (str): The output directory for generated APIs.
            yangkit_root   (str): The yangkit root directory. Relative file names in
                              the profile file are resolved relative to this.
            language (str): Language for generated APIs
            package_type (str): Package type for generated APIs.
                            Valid options for bundle approach are: 'core',
                                                                   'packages'.

        Raises:
            YangkitGenException: If an error has occurred
    """

    def __init__(self, output_dir, yangkit_root, package_type):

        _check_generator_args(output_dir, yangkit_root, package_type)

        self.output_dir = output_dir
        self.yangkit_root = yangkit_root
        self.package_type = package_type
        self.iskeyword = ispythonkeyword
        self.package_name = ""
        self.version = ""
        self.generate_meta = False

    def generate(self, description_file):
        """ Generate yangkit bundle packages or yangkit core library.

        Args:
            description_file (str): Path to description file.

        Returns:
            Generated APIs root directory for core and profile package.
            List of Generated APIs root directories for bundle packages.
        """
        if self.package_type == 'bundle':
            return self._generate_bundle(description_file)
        else:
            raise YangkitGenException('Invalid package type specified: %s' % self.package_type)

    def _generate_bundle(self, profile_file):
        """ Generate yangkit bundle package. First translate profile file to
        bundle syntax.

        Args:
            profile_file (str): Path to profile description file.

        Returns:
            gen_api_root (str): Root directory for generated APIs.
        """
        _check_description_file(profile_file)
        with open(profile_file) as f:
            profile = json.load(f)
            self.package_name = profile.get('name')
            self.version = profile.get('version')
            if self.package_name is None or self.version is None:
                raise YangkitGenException("Attribute 'name' and/or 'version' is not defined in the profile")

        if '.' in self.package_name:
            self.package_name = self.package_name.replace('.', '_')
            print("WARNING. Replacing package name from '%s' to '%s'" % (profile['name'], self.package_name))
            profile['name'] = self.package_name

        tmp_file = tempfile.mkstemp(suffix='.bundle')[-1]
        bundle_translator.translate(profile_file, tmp_file)

        resolver = bundle_resolver.Resolver(self.output_dir, self.iskeyword)
        curr_bundle, all_bundles = resolver.resolve(tmp_file)
        if not isinstance(curr_bundle, bundle_resolver.Bundle):
            raise AssertionError()
        for x in all_bundles:
            if not isinstance(x, bundle_resolver.Bundle):
                raise AssertionError()

        packages = self._get_packages(curr_bundle)
        if len(packages) == 0:
            raise YangkitGenException('No YANG models were found. Please check your JSON profile file to make sure it is valid')

        _set_original_bundle_name_for_packages(all_bundles, packages, curr_bundle)
        gen_api_root = self._init_bundle_directories(packages, curr_bundle)

        bundle_name = curr_bundle.fqn
        yang_models = _create_models_archive(curr_bundle, gen_api_root, bundle_name)
        generated_files = self._print_packages(packages, gen_api_root, curr_bundle)
        os.remove(tmp_file)

        return gen_api_root

    def _get_packages(self, bundle):
        """ Return packages for resolved YANG modules. Each module will be
            represented as an api package.

        Args:
            bundle (Bundle): Bundle package.

        Returns:
            packages (List[.api_model.Package]): List of api packages.
        """

        resolved_model_dir = bundle.resolved_models_dir
        pyang_builder = PyangModelBuilder(resolved_model_dir)
        modules = pyang_builder.parse_and_return_modules()

        # build api model packages
        packages = ApiModelBuilder(self.iskeyword, bundle.name).generate(modules)
        packages.extend(
            SubModuleBuilder().generate(pyang_builder.get_submodules(), self.iskeyword, bundle.name))

        return packages

    def _print_packages(self, pkgs, output_dir, bundle):
        """ Emit generated APIs.

        Args:
            pkgs (List[.api_model.Package]): List of api packages to print.
            output_dir (str): Output directory.
            bundle (Bundle): Bundle package
        """
        global classes_per_source_file
        factory = printer_factory.PrinterFactory()
        bundle_packages = _filter_bundle_from_packages(pkgs, bundle)
        yangkit_printer = factory.get_printer('python')(output_dir, bundle)
        yangkit_printer.generate_meta = self.generate_meta
        generated_files = yangkit_printer.emit(bundle_packages, classes_per_source_file)
        return generated_files

    # Initialize generated API directory ######################################
    def _initialize_gen_api_directories(self, package_name, package_type):
        """ Initialize and return generated APIs root directory.

            Args:
                package_name (str): Package name for generated API, if specified.
                package_type (str): Sdk template type to copied from, if specified.
                                Valid options are: core, packages.
        """
        gen_api_root = os.path.join(self.output_dir, package_name)

        # clean up gen_api_root
        if not os.path.isdir(gen_api_root):
            os.makedirs(gen_api_root)

        self._copy_sdk_template(gen_api_root, package_type)

        return gen_api_root

    def _init_bundle_directories(self, packages, bundle):
        """ Initialize generated API directory for bundle approach.

        Args:
            bundle (bundle_resolver.Bundle): Bundle instance.

        Returns:
            gen_api_root (str): Root directory for generated APIs.
        """
        gen_api_root = self._initialize_gen_api_directories(bundle.name + '-bundle', 'packages')

        _modify_python_setup(gen_api_root,
                                'yangkit-models-%s' % bundle.name,
                                bundle.str_version,
                                bundle.str_core_version,
                                bundle.dependencies,
                                bundle.description,
                                bundle.long_description)
        _modify_python_manifest(gen_api_root, bundle.name)

        # write init file for bundle models directory.
        bundle_model_dir = os.path.join(gen_api_root, 'yangkit')
        if not os.path.exists(bundle_model_dir):
            os.mkdir(bundle_model_dir)

        return gen_api_root

    def _copy_sdk_template(self, gen_api_root, package_type):
        """ Copy sdk template to gen_api_root directory.

        Args:
            gen_api_root (str): Root directory for generated APIs.
            package_type (str): Sdk template to copied from.
                            Valid options are: core, packages.
        """
        target_dir = os.path.join(self.yangkit_root, 'python_package_files')
        shutil.rmtree(gen_api_root)
        logger.debug('Copying %s to %s' % (target_dir, gen_api_root))
        dir_util.copy_tree(target_dir, gen_api_root)


def _filter_bundle_from_packages(pkgs, bundle):
    bundle_packages = []
    bundle_package_names = [x.name for x in bundle.models]
    for package in pkgs:
        if package.stmt.arg in bundle_package_names:
            bundle_packages.append(package)
    return bundle_packages


def _get_yang_models_filenames_from_directory(path, prefix):
    yang_models = []
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if file.endswith(".yang"):
            yang_models.append(os.path.join(prefix, file))
        elif os.path.islink(file_path):
            yang_models.extend(_get_yang_models_filenames_from_directory(file_path, file))
    return yang_models


def _create_tar(resolved_models_dir, tar_file_path):
    yang_models = _get_yang_models_filenames_from_directory(resolved_models_dir, '')
    with tarfile.open(tar_file_path, 'w:gz') as tar:
        for y in yang_models:
            yang_model_path = os.path.join(resolved_models_dir, y)
            tar.add(yang_model_path, arcname=os.path.basename(yang_model_path))
    yang_models_base_names = [os.path.basename(file) for file in yang_models]
    return yang_models_base_names


def _create_models_archive(bundle, target_dir, bundle_name):
    """
    Creates yang models archive as part of bundle package.
    Args:
        bundle (Bundle): Bundle package
        target_dir (str): Directory where archive is to be created
        bundle_name (st): Bundle name with version
    """
    global YANGKIT_YANG_MODEL
    if not isinstance(bundle, bundle_resolver.Bundle):
        raise AssertionError()
    tar_file = '{}.tar.gz'.format(bundle_name)
    tar_file_path = os.path.join(target_dir, tar_file)
    yangkit_yang = os.path.join(target_dir, YANGKIT_YANG_MODEL)
    if os.path.isfile(yangkit_yang):
        shutil.copy(yangkit_yang, bundle.resolved_models_dir)
    yang_models = _create_tar(bundle.resolved_models_dir, tar_file_path)

    logger.debug('\nCreated models archive: {}'.format(tar_file_path))
    return yang_models


def _set_original_bundle_name_for_packages(bundles, packages, curr_bundle):
    """ Set original bundle name for packages.

    Args:
        bundles (List[.resolver.bundle_resolver.Bundle]): Bundle instance.
        packages (List[.api_model.Package]): List of api packages.

    """
    # add API for model being augmented to bundle
    for pkg in packages:
        pkg.curr_bundle_name = curr_bundle.name
        for bundle in bundles:
            for module in bundle.models:
                if pkg.name == module.pkg_name:
                    pkg.bundle_name = bundle.name

def normalize_version(version):
    version = version.replace('_', '.')
    version = version.replace('-', '.')
    return version


def _modify_python_setup(gen_api_root, package_name, version, core_version, dependencies, description, long_description):
    """ Modify setup.py template for python packages. Replace package name
        and version number in setup.py located in <gen_api_root>/setup.py.
        If dependencies are specified, $DEPENDENCY$ in setup.py will be replaced.
        The ``fileinput`` module redirect stdout back to input file.

    Args:
        gen_api_root (str): Root directory for generated APIs.
        package_name (str): Package name for generated APIs.
        version (str): Package version for generated APIs.
        core_version (str): yangkit core library version for generated APIs.
        dependencies (list): bundle dependencies
        description (str): description for bundle package
        long_description (str): long description for bundle package
    """
    setup_file = os.path.join(gen_api_root, 'setup.py')
    # replaced_package = False
    replaced_version = False
    replaced_core_version = False
    replaced_dependencies = False
    replaced_description = False
    replaced_long_description = False
    for line in fileinput.input(setup_file, inplace=True):
        if "$PACKAGE$" in line:
            replaced_package = True
            print(line.replace("$PACKAGE$", package_name.replace('_', '-')), end='')
        elif not replaced_version and "$VERSION$" in line:
            replaced_version = True
            print(line.replace("$VERSION$", normalize_version(version)), end='')
        elif not replaced_core_version and "$CORE_VERSION$" in line:
            replaced_core_version = True
            print(line.replace("$CORE_VERSION$", normalize_version(core_version)), end='')
        elif not replaced_dependencies and "$DEPENDENCY$" in line:
            replaced_dependencies = True
            if dependencies:
                additional_requires = ["'yangkit-models-%s>=%s'" % (d.name, normalize_version(d.str_version))
                                       for d in dependencies]
                print(line.replace("'$DEPENDENCY$'", ", ".join(additional_requires)))
            else:
                print(line.replace("'$DEPENDENCY$'", ""))
        elif not replaced_description and "$DESCRIPTION$" in line:
            replaced_description = True
            print(line.replace("$DESCRIPTION$", description), end='')
        elif not replaced_long_description and "$LONG_DESCRIPTION$" in line:
            replaced_long_description = True
            print(line.replace("$LONG_DESCRIPTION$", long_description), end='')
        else:
            print(line, end='')


def _modify_python_manifest(gen_api_root, bundle_name):
    manifest_file = os.path.join(gen_api_root, 'MANIFEST.in')
    for line in fileinput.input(manifest_file, inplace=True):
        if '$NAME$' in line:
            print(line.replace('$NAME$', bundle_name))
        else:
            print(line, end='')

# Generator checks #####################################################
def _check_generator_args(output_dir, yangkit_root, package_type):
    """ Check generator arguments.

    Args:
        output_dir (str): The output directory for generated APIs.
        yangkit_root (str): The yangkit root directory.
        language (str): Language for generated APIs.
        package_type (str): Package type for generated APIs.
                        Valid options for bundle approach are: 'core', 'packages'.
    Raises:
        YangkitGenException: If invalid arguments are passed in.
    """

    if output_dir is None or len(output_dir) == 0:
        logger.error('output_directory is None.')
        raise YangkitGenException('output_dir cannot be None.')

    if yangkit_root is None or len(yangkit_root) == 0:
        logger.error('yangkit_root is None.')
        raise YangkitGenException('YANGKITGEN_HOME is not set.')


def _check_description_file(description_file):
    """ Check if description_file is valid path to file.

    Args:
        description_file (str): Path to description file.

    Raises:
        YangkitGenException: If path to description file is not valid.
    """
    if not os.path.isfile(description_file):
        logger.error('Path to description file is not valid.')
        raise YangkitGenException('Path to description file is not valid.')
