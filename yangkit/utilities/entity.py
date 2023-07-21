import re
import importlib
from yangkit import log
from yangkit.errors import YInvalidArgumentError


def get_internal_node(entity, absolute_path):
    """
    This method finds internal node of entity with provided absolute path
    :param entity: entity object
    :param absolute_path: absolute path
    """
    if not absolute_path:
        err_msg = f"Argument 'absolute_path' should not be empty or None"
        log.error(err_msg)
        raise YInvalidArgumentError(err_msg)

    top_absolute_path = entity.get_absolute_path()
    if not top_absolute_path:
        err_msg = f"absolute_path of {entity} should not be empty or None"
        log.error(err_msg)
        raise YInvalidArgumentError(err_msg)

    absolute_path = re.sub(r"\[(.*?)='None'\]", "", absolute_path)
    segments = re.split(r"/(?![^\[]*\])", absolute_path)

    if segments[0] != top_absolute_path:
        err_msg = f"{top_absolute_path} is not in the ancestor hierarchy of {absolute_path}"
        log.error(err_msg)
        raise YInvalidArgumentError(err_msg)

    for segment in segments[1:]:
        if '[' in segment:
            _, entity = entity.get_child_by_name(segment.split('[')[0], "")
            for ent in entity:
                if ent.get_segment_path() == segment:
                    entity = ent
                    break
        else:
            _, entity = entity.get_child_by_name(segment, segment)

    return entity


def get_bundle_name(entity):
    """
    This method finds the bundle name for provided entity object
    :param entity: entity object
    """
    mod_name = str(getattr(entity, '__module__'))
    return mod_name.split('.')[2]


def get_bundle_yang_ns(bundle_name):
    """
    Return yang namespace module for provided bundle
    :param bundle_name: bundle name
    """
    mod_yang_ns = None
    yang_namespace_path = f'yangkit.models.{bundle_name}._yang_ns'
    try:
        mod_yang_ns = importlib.import_module(yang_namespace_path)
    except ImportError as error:
        log.error(f"Yang NameSpace {yang_namespace_path} errored: {error}")
    return mod_yang_ns


def get_top_level_class(entity):
    """
    Finds the module and top level container class in the ancestor hierarchy of entity

    :param entity: Entity object
    """

    entity_absolute_path = entity.get_absolute_path()
    segments = re.split(r"/(?![^\[]*\])", entity_absolute_path)
    root_segment_path = segments[0]

    # fetching bundle name and corresponding _yang_ns module
    bundle_name = get_bundle_name(entity)
    bundle_yang_ns = get_bundle_yang_ns(bundle_name)

    root_parent_name, root_name = root_segment_path.split(":")
    module_name, clazz_name = bundle_yang_ns.ENTITY_LOOKUP[(root_parent_name,
                                                            root_name)].split('.')
    clazz = getattr(importlib.import_module(
        f'yangkit.models.{bundle_name}.{module_name}'), clazz_name)
    return clazz()
