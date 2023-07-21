"""
 Yangkit PY converter
"""

import os
import shutil
from distutils import dir_util

from yang_generator.api_model import Bits, Class, Enum, Package, get_property_name
from yang_generator.common import get_rst_file_name

from .import_test_printer import ImportTestPrinter
from .module_printer import ModulePrinter
from .namespace_printer import NamespacePrinter
from .init_file_printer import InitPrinter
from ..doc import DocPrinter
from yang_generator.printer.language_bindings_printer import LanguageBindingsPrinter, _EmitArgs

import logging

logger = logging.getLogger('yangkitgen')


class PythonBindingsPrinter(LanguageBindingsPrinter):

    def __init__(self, yangkit_root_dir, bundle):
        super().__init__(yangkit_root_dir, bundle)
        self.bundle = bundle
        self.bundle_name = bundle.name
        self.bundle_version = bundle.str_version
        self.generate_meta = False

    def print_files(self):
        self._print_init_file(self.models_dir)
        self._print_yang_ns_file()
        self._print_modules()
        self._print_import_tests_file()

        # Sub package
        if self.sub_dir != '':
            self._print_nmsp_declare_init_files()

        # YANG models
        self._copy_yang_files()
        return ()

    def _print_modules(self):
        only_modules = [package.stmt for package in self.packages]
        size = len(only_modules)

        for index, package in enumerate(self.packages):
            self._print_module(index, package, size)

    def _print_module(self, index, package, size):
        print('Processing %d of %d %s' % (index + 1, size, package.stmt.pos.ref))

        # Skip generating module for empty modules
        if len(package.owned_elements) == 0:
            logger.debug("    Skipping module, because it does not contain top level containers")
            return

        sub = package.sub_name
        test_output_dir = self.initialize_output_directory(self.test_dir)
        self._print_python_module(package, index, self.models_dir, size, sub)

    def _print_python_modules(self, element, index, path, size, sub):
        for c in [clazz for clazz in element.owned_elements if isinstance(clazz, Class)]:
            if not c.is_identity():
                self._print_python_module(c, index, os.path.join(path, get_property_name(c, c.iskeyword)), size, sub)

    def _print_python_module(self, package, index, path, size, sub):
        self._print_init_file(path)

        package.parent_pkg_name = sub
        extra_args = {'one_class_per_module': False,
                      'generate_meta': self.generate_meta,
                      'identity_subclasses': self.identity_subclasses,
                      'module_namespace_lookup' : self.module_namespace_lookup}
        python_module_file_name = get_python_module_file_name(path, package)
        logger.debug("    Printing python module %s" % python_module_file_name)
        self.print_file(python_module_file_name,
                        emit_module,
                        _EmitArgs(self.ypy_ctx, package, extra_args))

    def _print_yang_ns_file(self):
        packages = self.packages

        self.print_file(get_yang_ns_file_name(self.models_dir),
                        emit_yang_ns,
                        _EmitArgs(self.ypy_ctx, packages, (self.bundle_name, False)))

    def _print_import_tests_file(self):
        self.print_file(get_import_test_file_name(self.test_dir),
                        emit_importests,
                        _EmitArgs(self.ypy_ctx, self.packages))

    def _print_init_file(self, path):
        file_name = get_init_file_name(path)
        if not os.path.isfile(file_name):
            self.print_file(file_name)

    def _print_nmsp_declare_init_files(self):
        self._print_nmsp_declare_init(self.yangkit_dir)
        self._print_nmsp_declare_init(os.path.join(self.yangkit_dir, 'models'))
        self._print_nmsp_declare_init(self.models_dir)

    def _print_nmsp_declare_init(self, path):
        file_name = get_init_file_name(path)
        self.print_file(file_name,
                        emit_nmsp_declare_init,
                        _EmitArgs(self.ypy_ctx, self.packages))

    def _copy_yang_files(self):
        yang_files_dir = os.path.sep.join([self.models_dir, '_yang'])
        os.mkdir(yang_files_dir)
        dir_util.copy_tree(self.bundle.resolved_models_dir, yang_files_dir)
        _copy_yang_files_from_subdirectories(yang_files_dir)


def _copy_yang_files_from_subdirectories(yang_files_dir):
    subdirs = [os.path.join(yang_files_dir, o) for o in os.listdir(yang_files_dir) if os.path.isdir(os.path.join(yang_files_dir, o))]
    for subdir in subdirs:
        files = os.listdir(subdir)
        for file in files:
            file_path = os.path.join(subdir, file)
            if os.path.isfile(file_path):
                shutil.copy(file_path, yang_files_dir)


def get_init_file_name(path):
    return path + '/__init__.py'


def get_yang_ns_file_name(path):
    return path + '/_yang_ns.py'


def get_import_test_file_name(path):
    return path + '/import_tests.py'


def get_python_module_documentation_file_name(path, named_element):
    return '%s/%s.rst' % (path, get_rst_file_name(named_element))


def get_table_of_contents_file_name(path):
    return '%s/yangkit.models.rst' % path


def get_python_module_file_name(path, package):
    if isinstance(package, Package):
        return '%s/%s.py' % (path, package.name)
    else:
        return '%s/%s.py' % (path, get_property_name(package, package.iskeyword))


def get_meta_module_file_name(path, package):
    return '%s/_%s.py' % (path, package.name)


def get_test_module_file_name(path, package):
    return '%s/test_%s.py' % (path, package.stmt.arg.replace('-', '_'))


def emit_yang_ns(ctx, packages, extra_args):
    bundle_name = extra_args[0]
    one_class_per_module = extra_args[1]
    NamespacePrinter(ctx, one_class_per_module).print_output(packages, bundle_name)


def emit_importests(ctx, packages):
    ImportTestPrinter(ctx).print_import_tests(packages)


def emit_module_documentation(ctx, named_element, identity_subclasses):
    DocPrinter(ctx, 'py').print_module_documentation(named_element, identity_subclasses)


def emit_table_of_contents(ctx, packages, extra_args):
    bundle_name, bundle_version = extra_args
    DocPrinter(ctx, 'py', bundle_name, bundle_version).print_table_of_contents(packages)


def emit_module(ctx, package, extra_args):
    ModulePrinter(ctx, extra_args).print_output(package)


def emit_nmsp_declare_init(ctx, package):
    InitPrinter(ctx).print_nmsp_declare_init(package)
