"""
class_docstring_printer.py

 Printer for the docstrings.

"""
from yang_generator.printer.meta_data_util import get_class_docstring


class ClassDocstringPrinter(object):

    def __init__(self, ctx):
        """
            Class doc string printer

            :attribute ctx The printer context
        """
        self.ctx = ctx

    def print_output(self, clazz):
        """
            Prints the doc strings for the clazz

            :param `api_model.Class` clazz :- The Class object.
        """
        self.ctx.lvl_inc()
        self.ctx.writeln('"""')
        self._print_class_docstring_text(clazz)
        self._print_class_docstring_presence(clazz)
        self.ctx.writeln('"""')
        self.ctx.lvl_dec()

    def _print_class_docstring_text(self, clazz):
        class_docstring = get_class_docstring(clazz, 'py')
        if len(class_docstring) > 0:
            prev_line = ''
            for line in class_docstring.split('\n'):
                if line or prev_line:
                    self.ctx.writeln('%s' % line)
                prev_line = line

    def _print_class_docstring_presence(self, clazz):
        if clazz.stmt.search_one('presence') is not None:
            self.ctx.bline()
            line = """This class is a :ref:`presence class<presence-class>`"""
            self.ctx.writeln(line)
