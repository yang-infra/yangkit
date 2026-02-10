"""Print init files for the generated Python api."""

class InitPrinter(object):
    """
    Prints init files.

        :attribute ctx The printer context
        :attribute parent The parent printer object
    """

    def __init__(self, ctx):
        self.ctx = ctx

    def print_nmsp_declare_init(self, _):
        """Print init file to declare namespace package."""
        self.ctx.str("""__path__ = __import__('pkgutil').extend_path(__path__, __name__)""")

