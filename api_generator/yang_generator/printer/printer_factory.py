"""
printer_factory.py

 Returns printer

"""
from yang_generator.printer.python.python_bindings_printer import PythonBindingsPrinter

class PrinterFactory(object):

    def get_printer(self, language):
        if language == 'python':
            return PythonBindingsPrinter
        else:
            raise Exception('Language {0} not yet supported'.format(language))
