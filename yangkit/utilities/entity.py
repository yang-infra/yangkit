import re
import importlib
from yangkit.utilities.logger import log
from yangkit.errors import YInvalidArgumentError


def segmentalize(absolute_path):
    """
    Returns a list of segments in absoulute path
    """
    return re.split(r"/(?![^\[]*\])", absolute_path)


def get_internal_node(entity, absolute_path):
    """
    This method finds internal node from the top-level

    :param entity: entity object
    :param absolute_path: absolute path
    """
    print("absolute_path")
    print(absolute_path)
    print("entity")
    print(entity.__dict__)
    if not absolute_path:
        err_msg = f"Argument 'absolute_path' should not be empty or None"
        log.error(err_msg)
        raise YInvalidArgumentError(err_msg)

    top_absolute_path = entity.get_absolute_path()
    print("top_absolute_path")
    print(top_absolute_path)
    
    if not top_absolute_path:
        err_msg = f"absolute_path of {entity} should not be empty or None"
        log.error(err_msg)
        raise YInvalidArgumentError(err_msg)

    segments = segmentalize(absolute_path)
    print("segemnts")
    print(segments)
    print("segments 0 index")
    print(segments[0])

    if segments[0] != top_absolute_path:
        err_msg = f"{top_absolute_path} is not in the ancestor hierarchy of {absolute_path}"
        log.error(err_msg)
        raise YInvalidArgumentError(err_msg)

    for segment in segments[1:]:
        if '[' in segment:
            print("segment")
            print(segment)
            attr, child = entity.get_child_by_name(segment.split('[')[0], "")
            print("attr")
            print(attr)
            print("child")
            print(child)
            
            ylist = getattr(entity, attr)
            print("ylist")
            print(ylist)

            found = False
            for ylist_item in ylist:
                if ylist_item.ylist_key_names and ylist_item.get_segment_path() == segment:
                    found = True
                    break
            print("found")
            print(found)
            
            if found:
                entity = ylist_item
                print("entity - found true")
                print(entity)
            elif segment == segments[-1]:
                # fair assumption
                print("ylist.entities()")
                print(ylist.entities())
                return ylist.entities()
            else:
                entity = child
                print("entity - found false")
                print(entity)
        else:
            print("segment else block")
            print(segment)
            _, entity = entity.get_child_by_name(segment, segment)
            print("entity else block")
            print(entity)

    print("entity")
    print(entity.__dict__)
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
    segments = segmentalize(entity.get_absolute_path())
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


def find_prefix_in_namespace_lookup(segment_path, bundle_yang_ns):
    """
    Checks if the prefix of a container or leaf is in the bundle's YANG namespace lookup

    :param segment_path: segment_path of a container or name of a leaf
    :param bundle_yang_ns: YANG namespace module for the bundle
    :return {None: name_space} if prefix is present in the namespace_lookup; {} otherwise
    """
    try:
        prefix, _ = re.split(r":(?![^\[]*\])", segment_path)
        for name_space_prefix, name_space in bundle_yang_ns.NAMESPACE_LOOKUP.items():
            if prefix == name_space_prefix:
                return name_space_prefix, name_space
    except:
        pass

    return None, None
