"""
 import_test_printer.py

 YANG model driven API, python emitter.
"""

import abc
import os
import logging

from yang_generator.printer import FilePrinter
from yang_generator.builder import MultiFile

logger = logging.getLogger('yangkitgen')


class MultiFilePrinter(FilePrinter):
    def __init__(self, ctx):
        super().__init__(ctx)

    def print_output(self, package, multi_file, path_prefix):
        assert isinstance(multi_file, MultiFile)
        path = path_prefix
        if multi_file.fragmented:
            path = os.path.join(path, 'fragmented')
            if not os.path.isdir(path):
                os.mkdir(path)
        path = os.path.join(path, multi_file.file_name)
        if multi_file.fragmented:
            logger.debug('Printing fragmented file {0}'.format(multi_file.file_name))
        with open(path, 'w+') as file_descriptor:
            self.ctx.fd = file_descriptor
            self._start_tab_leak_check()
            self.print_header(package, multi_file)
            self.print_body(multi_file)
            self.print_extra(package, multi_file)
            self.print_trailer(package, multi_file)
            self._check_tab_leak()

    @abc.abstractmethod
    def print_body(self, multi_file):
        pass

    def print_header(self, package, multi_file):
        pass

    def print_extra(self, package, multi_file):
        pass
