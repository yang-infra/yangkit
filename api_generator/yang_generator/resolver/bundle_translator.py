"""
Translate profile file to profile file to bundle file.

Regular expression taken from:
https://github.com/xym-tool/symd/blob/master/symd.py.
"""

import os
import re
import json
import logging
import tempfile
from os import walk
from shutil import rmtree
from collections import namedtuple
from jinja2 import Environment
from ..common import YangkitGenException
from yangkit.__version__ import __version__

logger = logging.getLogger('yangkitgen')

MODULE_STATEMENT = re.compile(r'''^[ \t]*(sub)?module +(["'])?([-A-Za-z0-9]*(@[0-9-]*)?)(["'])? *\{.*$''')
REVISION_STATEMENT = re.compile(r'''^[ \t]*revision[\s]*(['"])?([-0-9]+)?(['"])?[\s]*\{.*$''')
Local_URI = namedtuple('Local_URI', ['url'])

Bundle = namedtuple('Bundle', ['name', 'version', 'core_version', 'description', 'long_description'])
BundleDependency = namedtuple('BundleDependency', ['name', 'version', 'core_version', 'uri'])

TEMPLATE = """{% set comma = joiner(",") %}
{
    "modules" : [{% for m in modules %}{{ comma() }}
        {
            "name" : "{{ m.name }}",
            "revision" : "{{ m.revision }}",
            "kind" : "{{ m.kind }}",
            "uri" : "{{ m.uri }}"
        }{% endfor %}
    ],

    "bundle" : {
        "name" : "{{ definition.name }}",
        "version" : "{{ definition.version}}",
        "core-version" : "{{ definition.core_version }}",
        "description" : "{{ definition.description }}",
        "long-description" : "{{ definition.long_description }}"{% if dependency is not none %},
        "dependencies" : [{% for d in dependency %}
            {
                "name" : "{{ d.name }}",
                "version" : "{{ d.version }}",
                "core-version" : "{{ d.core_version }}",
                "uri" : "{{ d.uri }}"
            }{% if not loop.last %},{% endif %}{% endfor %}
        ]{% endif %}
    }
}
"""


class Module(object):
    def __init__(self, name, revision, kind, uri):
        self.name = name
        self.revision = revision
        self.kind = kind
        self.uri = convert_uri(uri)


def convert_uri(uri):
    """ Convert uri to bundle format.

        For example:
            >>> convert_uri(Local_URI('absolute/path/to/file'))
            'file://absolute/path/to/file'

    """
    if isinstance(uri, Local_URI):
        # path relative to $YANGKITGEN_HOME
        return "file://%s" % uri.url


def get_module_attrs(module_file, remote=None):
    """ Return name, latest revision, kind and uri attribute for module."""
    name, revision, kind = None, None, None
    # rpath = os.path.relpath(module_file, root)
    with open(module_file) as f:
        for line in f:
            match = MODULE_STATEMENT.match(line)
            if match:
                name = match.groups()[2]
                if match.groups()[0] == 'sub':
                    kind = 'SUBMODULE'
                else:
                    kind = 'MODULE'
            match = REVISION_STATEMENT.match(line)
            if match:
                revision = match.groups()[1]
                break

    if remote is None:
        uri = Local_URI(module_file)

    return Module(name, revision, kind, uri)


def get_file_attrs(files, remote=None):
    for f in files:
        if f.endswith('.yang'):
            # logger.debug('Getting attrs from file: %s' % f)
            if os.path.exists(f):
                yield get_module_attrs(f, remote)
            else:
                logger.warning('File %s is not present in the directory %s; skipping' % (f, root))


def get_dir_attrs(dir, remote=None):
    for (dd, _, files) in walk(dir):
        for res in get_file_attrs((os.path.join(dd, f) for f in files),
                                    remote):
            yield res


def load_profile_attr(profile_file, attr):
    with open(profile_file) as f:
        data = json.load(f)
    if attr in data:
        if attr == 'dependency':
            dependencies = []
            for dependency in data[attr]:
                dependencies.append(BundleDependency(**dependency))
            return dependencies
        else:
            return data[attr]
    else:
        return None


def translate(in_file, out_file):
    """ Generate bundle file using profile file(in_file).
    in_file is a relative path to a local profile file.
    """
    with open(in_file) as f:
        data = json.load(f)

    modules = []
    modules.extend(globals()['get_dir_attrs'](data['yang_dir']))

    try:
        name = data['name']
        version = data['version']
        core_version = __version__
    except KeyError:
        raise YangkitGenException('Bundle profile requires to specify name, version, core_version and description.')

    description = data['description'] if 'description' in data else str()
    long_description = data['long_description'] if 'long_description' in data else str()
    definition = Bundle(name, version, core_version, description, long_description)
    dependency = load_profile_attr(in_file, 'dependency')

    output = Environment().from_string(TEMPLATE).render(
        modules=modules, definition=definition, dependency=dependency)

    with open(out_file, 'w') as f:
        f.write(output)
