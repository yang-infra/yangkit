""" bundle_resolver.py
    Resolve bundle description file.
    Returns current bundle being processed and list of dependency bundles.
"""
import re
import os
import json
import logging
import tempfile
from shutil import rmtree, copy
from collections import namedtuple, defaultdict
from .bundle_translator import translate
from ..common import YangkitGenException


logger = logging.getLogger('yangkitgen')
logger.addHandler(logging.NullHandler())

URI = re.compile(r"(?P<url>.+)\?commit-id=(?P<id>.+)&path=(?P<path>.+)")
Local = namedtuple('Local', ['url'])
Bundles = namedtuple('Bundles', ['curr_bundle', 'bundles'])


def nested_defaultdict():
    return defaultdict(nested_defaultdict)


def parse_uri(uri):
    """ Return Local uri.

        Args:
            uri (str): String representation for URI

        Raises:
            YangkitGenException if uri is malformed.
    """
    if uri.startswith('file'):
        return Local(uri.split('file://')[-1])


class BundleDefinition(object):
    """ Base class for Bundle and BundleDependency, with following attributes

        Attributes:
            _name (str): bundle name.
            _version (Version): bundle version.
            _core_version (Version): yangkit core library version.
            _description (str): description for bundle package
            _long_description (str): long description for bundle package

        Raises:
            KeyError if data is malformed.
    """

    def __init__(self, data):
        self._name = data['name'].replace('-', '_')
        self._version = data['version']
        self._core_version = data['core-version']
        self._description = data['description'] if 'description' in data else str()
        self._long_description = data['long-description'] if 'long-description' in data else str()

    @property
    def name(self):
        return self._name

    @property
    def fqn(self):
        """ Return fully qualified name."""
        return '@'.join([self._name, self.str_version])

    @property
    def version(self):
        """ Return bundle version."""
        return self._version

    @property
    def core_version(self):
        """ Return yangkit version."""
        return self._core_version

    @property
    def str_version(self):
        """ Return string representation of version."""
        return str(self.version)

    @property
    def str_core_version(self):
        """ Return string representation of yangkit version."""
        return str(self.core_version)

    @property
    def description(self):
        """ Return bundle description."""
        return self._description

    @property
    def long_description(self):
        """ Return bundle long description."""
        return self._long_description


class BundleDependency(BundleDefinition):
    """ BundleDependency class represent a possible unresolved bundle,
    an extra attribute uri.

        Attributes:
            uri (Local_URI): URI for a local bundle file.
        Raises:
            KeyError if data if malformed.
    """

    def __init__(self, data):
        super().__init__(data)
        self.uri = parse_uri(data['uri'])


class Model(object):
    """ Model class for models listed in bundle description file, with
        following attributes:

        Attributes:
            _name (str): model name.
            _revision (str): latest revision for this model.
            _kind (str): model type, could be 'MODULE' or 'SUBMODULE'.
            _uri (LocalURI): URI to locate this model.

        Raises:
            KeyError if data if malformed.
    """
    __slots__ = ['_name', '_revision', '_kind', '_uri', 'iskeyword']

    def __init__(self, data, iskeyword):
        self._name = data['name'].replace('.', '_')
        if 'revision' in data:
            self._revision = data['revision']
        else:
            self._revision = ''
        self._kind = data['kind']
        self._uri = parse_uri(data['uri'])
        self.iskeyword = iskeyword

    @property
    def name(self):
        return self._name

    @property
    def pkg_name(self):
        name = self._name
        name = name.replace('-', '_')
        if self.iskeyword(name):
            name = '%s_' % name
        if name[0] == '_':
            name = 'y%s' % name
        return name

    @property
    def fqn(self):
        """ Return fully qualified name."""
        return self._name + '@' + self._revision

    @property
    def uri(self):
        """ Return model uri."""
        return self._uri

    @property
    def revision(self):
        """Return model revision."""
        return self._revision


class Bundle(BundleDefinition):
    """ Bundle class consumes a local bundle file, with following attributes:

        Attributes:
            models (list of Model): list of models defined in this bundle.
            dependencies (list of BundelDependencies): list of dependencies for
                this bundle, this could be an empty list.
            _uri (str): uri for bundle description file.
            _resolved_models_root (str): resolved models caching directory.

        Raises:
            KeyError if data is malformed.
    """

    def __init__(self, uri, resolved_models_root, iskeyword):
        self.models = []
        self.dependencies = []
        self._uri = uri
        self._resolved_models_root = resolved_models_root
        self.iskeyword = iskeyword

        try:
            with open(uri) as json_file:
                data = json.load(json_file)
        except IOError:
            raise YangkitGenException('Cannot open bundle file %s.' % uri)

        try:
            data['bundle']['name'] = data['bundle']['name'].replace('.', '_')
            super().__init__(data['bundle'])
            if 'modules' in data:
                for m in data['modules']:
                    self.models.append(Model(m, self.iskeyword))
            if 'dependencies' in data['bundle']:
                for d in data['bundle']['dependencies']:
                    self.dependencies.append(BundleDependency(d))
        except KeyError:
            raise YangkitGenException('Bundle file is not well formatted.')

        self.children = []

    @property
    def uri(self):
        return self._uri

    @property
    def resolved_models_dir(self):
        resolved_dir = os.path.join(self._resolved_models_root, self.fqn)
        if not os.path.isdir(resolved_dir):
            os.makedirs(resolved_dir)
        return resolved_dir


class Resolver(object):
    """ Bundle resolver class, it will resolve all the model files and
        bundle files referred to by current bundle file and its dependencies.

        Attributes:
            cached_models_dir (str) : path to resolved model files.
            cached_bundles_dir(str) : path to resolved bundle files.
            bundles (dict): dictionary to hold Bunlde instances.

    """

    def __init__(self, output_dir, iskeyword, reuse_model=False, reuse_bundle=False):
        """ Initialize cached file directories.
        """
        self.cached_models_dir = ''
        self.cached_bundles_dir = ''
        self.bundles = {}
        self.iskeyword = iskeyword
        self._init_cached_directories(output_dir, reuse_model, reuse_bundle)

    def _init_cached_directories(self, output_dir, reuse_model, reuse_bundle):
        """Initialize cached directory."""
        cached_models_dir = os.path.join(output_dir, '.cache', 'models')
        cached_bundles_dir = os.path.join(output_dir, '.cache', 'bundles')
        if not reuse_model and os.path.isdir(cached_models_dir):
            rmtree(cached_models_dir)
        if not reuse_bundle and os.path.isdir(cached_bundles_dir):
            rmtree(cached_bundles_dir)
        if not os.path.isdir(cached_models_dir):
            os.makedirs(cached_models_dir)
        if not os.path.isdir(cached_bundles_dir):
            os.makedirs(cached_bundles_dir)

        self.cached_models_dir = cached_models_dir
        self.cached_bundles_dir = cached_bundles_dir

    def resolve(self, bundle_file):
        """ Resolve models defined in bundle file and its dependency files,
        return current bundle and list of related bundles.
        """
        uri = 'file://' + bundle_file
        bundle_file = self._resolve_bundle_file(parse_uri(uri))
        root = Bundle(bundle_file, self.cached_models_dir, self.iskeyword)
        self.bundles[root.fqn] = root
        self._resolve_bundles(root)
        return Bundles(root, self.bundles.values())

    def _resolve_bundles(self, root):
        """ Populate model uri."""
        for m in root.models:
            uri = m.uri
            if isinstance(uri, Local):
                _resolve_file(uri.url, root.resolved_models_dir)
        for d in root.dependencies:
            if d.fqn not in self.bundles:
                node = Bundle(self._resolve_bundle_file(d.uri),
                              self.cached_models_dir, self.iskeyword)
                self.bundles[d.fqn] = node
                _add_symlink(root, node)
                self._resolve_bundles(node)

    def _translate(self, description_file):
        """ Try to translate description file to bundle description file syntax.
        """
        tmp_file = tempfile.mkstemp('')[-1]
        try:
            translate(description_file, tmp_file)
        except KeyError:
            os.remove(tmp_file)
            return description_file
        return tmp_file

    def _resolve_bundle_file(self, uri):
        """ Resolve a local bundle file,
        return the location for resolved file.
        """
        if isinstance(uri, Local):
            src = uri.url
        resolved_file = _resolve_file(src, self.cached_bundles_dir)
        return self._translate(resolved_file)

def _add_symlink(bundle, dependency):
    source = dependency.resolved_models_dir
    link_name = os.path.basename(source)
    link_name = os.path.join(bundle.resolved_models_dir, link_name)
    os.symlink(source, link_name)


def _resolve_file(src, dst_dir, rename=''):
    """ Resolve file from src to dst directory.
    """
    fname = os.path.basename(src)
    logger.debug('Resolving file {} --> {}'.format(fname, dst_dir))
    if rename == '':
        dst = os.path.join(dst_dir, fname)
    else:
        dst = os.path.join(dst_dir, rename)
    copy(src, dst)
    return dst
