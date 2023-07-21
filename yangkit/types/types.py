from decimal import Decimal
import enum
from collections import OrderedDict
import importlib
import logging
from functools import reduce
from yangkit.filters import YFilter
from yangkit.errors import YModelError, YInvalidArgumentError
from yangkit.errors.error_handler import handle_type_error as _handle_type_error
from yangkit.utilities.entity import get_bundle_name, get_bundle_yang_ns


class EncodingFormat(enum.Enum):
    """
    Contains different encoding formats
    """
    XML = 0
    JSON = 1


class Empty(object):
    """
    Represents the empty type in YANG. The empty built-in type represents a leaf that does not have any
    value, it conveys information by its presence or absence.
    """
    set = False

    def __eq__(self, rhs):
        if not isinstance(rhs, Empty):
            raise YModelError("Empty comparison error, invalid rhs\n")
        return True

    def __ne__(self, rhs):
        return not isinstance(rhs, Empty)

    __hash__ = object.__hash__


# inspired from https://github.com/robshakir/pyangbind/blob/master/pyangbind/lib/yangtypes.py
# NOTE doesn't support the fraction-digits argument of the YANG decimal64 type.
class Decimal64(Decimal):
    """
    Represents the YANG decimal64 type.
    decimal.Decimal class is extended to restrict the precision that is stored.
    """
    _precision = 10.0 ** (-18)

    def __new__(cls, *args, **kwargs):
        """
        Overloads the decimal __new__ function in order to round the input
        value to the new value.
        """
        if args:
            value = Decimal(args[0]).quantize(Decimal(str(cls._precision)))
        else:
            value = Decimal(0)
        return Decimal.__new__(cls, value, **kwargs)


class Bits:
    """
    Represents bits YANG type, which is a bit set.
    """

    def __init__(self):
        self._bitmap = {}

    def __getitem__(self, key):
        if key not in self._bitmap:
            raise YInvalidArgumentError(f"Key '{key}' doesn't exist")
        return self._bitmap[key]

    def __setitem__(self, key, value):
        self._bitmap[key] = value

    def get_bitmap(self):
        """Returns the dict, self._bitmap"""
        return self._bitmap

    def __eq__(self, other):
        return self.get_bitmap() == other.get_bitmap() if isinstance(other, Bits) else False

    def __ne__(self, other):
        return self.get_bitmap() != other.get_bitmap() if isinstance(other, Bits) else True

    def get_bits_string(self):
        """Returns a string of values seperated by ' '."""
        value = ""
        for entry in self._bitmap.items():
            if entry[1]:
                value += f"{entry[0]} "
        value = value.rstrip()
        return value


class YType(enum.Enum):
    """
    Different YANG data types
    """
    uint8 = "uint8"
    uint16 = "uint16"
    uint32 = "uint32"
    uint64 = "uint64"
    int8 = "int8"
    int16 = "int16"
    int32 = "int32"
    int64 = "int64"
    empty = "empty"
    identityref = "identityref"
    str = "str"
    boolean = "boolean"
    enumeration = "enumeration"
    bits = "bits"
    decimal64 = "decimal64"


class Enum:
    """
    Represents enumeration YANG type
    """
    class YLeaf:
        def __init__(self, value, name):
            self.value = value
            self.name = name

        def __str__(self):
            return self.name

    def __init__(self):
        pass


class Identity:
    """
    The built-in datatype "identityref" can be used to reference identities within a data model.
    """

    def __init__(self, name_space, namespace_prefix, tag):
        self.name_space = name_space
        self.namespace_prefix = namespace_prefix
        self._tag = tag

    def to_string(self):
        return self._tag

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        if isinstance(other, Identity):
            return self.to_string() == other.to_string()
        return False

    def __ne__(self, other):
        if isinstance(other, Identity):
            return self.to_string() != other.to_string()
        return False


class LeafData:
    """
    Contains information (value and metadata) about a YLeaf. get_name_leafdata() returns a tuple(name, LeafData)
    """

    def __init__(self, value, yfilter, is_set, name_space, name_space_prefix):
        self.value = value
        self.yfilter = yfilter
        self.is_set = is_set
        self.name_space = name_space
        self.name_space_prefix = name_space_prefix

    def __eq__(self, other):
        if isinstance(other, LeafData):
            return (
                self.value == other.value
                and self.yfilter == other.yfilter
                and self.is_set == other.is_set
            )
        return False

    def __str__(self):
        return self.value


class EntityPath:
    """
    Stores LeafData for all the leaf nodes of an Entity
    """

    def __init__(self, path, value_paths):
        self.path = path
        self.value_paths = value_paths

    def __eq__(self, other):
        if isinstance(other, EntityPath):
            return self.path == other.path and self.value_paths == other.value_paths
        return False

    def __ne__(self, other):
        if isinstance(other, EntityPath):
            return self.path != other.path or self.value_paths != other.value_paths
        return True

    def __str__(self):
        value_paths_str = ", ".join(f"{key}: {value}" for key, value in self.value_paths)
        return f"{self.path} ( {value_paths_str} )"


class YLeaf:
    """
    Represents a leaf in YANG. "name" and "type" are mandatory
    :example: YLeaf(YType.uint32, 'lower-bound')
    """

    def __init__(self, type_, name):
        self.is_set = False
        self.yfilter = YFilter.not_set
        self.name = name
        self.type = type_
        self.value = ""
        self.bits_value = Bits()
        self.enum_value = 0
        self.value_namespace = ""
        self.value_namespace_prefix = ""

    def get(self):
        if self.type == YType.bits:
            return self.get_bits_string(self.bits_value)
        return self.value

    def get_name_leafdata(self):
        """
        returns a tuple(name, leafdata), where "name" is name of the leaf;
        "leafdata" is an object of type LeafData, containing values of some relevant attributes.
        """
        return (self.name, LeafData(self.get(), self.yfilter, self.is_set, self.value_namespace, self.value_namespace_prefix))

    def __repr__(self):
        return str(self.get())

    def __str__(self):
        return str(self.get())

    def __eq__(self, other):
        return self.get() == other.get()

    def __getitem__(self, key):
        self.is_set = True
        return self.bits_value[key]

    def __setitem__(self, key, value):
        self.is_set = True
        self.bits_value[key] = value

    def set(self, val):
        """
        :param val: object of any supported built-in Yang types
        sets the value of a leaf
        """
        self.is_set = True
        if type(val) == int or type(val) == str:
            self.value = str(val)
        elif type(val) == bool:
            self.value = "true" if val is True else "false"
        elif isinstance(val, Empty):
            self.value = ""
        elif isinstance(val, Identity):
            self.value = val.to_string()
            self.value_namespace = val.name_space
            self.value_namespace_prefix = val.namespace_prefix
        elif isinstance(val, Bits):
            self.bits_value = val
            self.value = val.get_bits_string()
        elif isinstance(val, Enum.YLeaf):
            self.value = str(val.name)
            self.enum_value = val.value
        elif isinstance(val, Decimal):
            self.value = str(val.s)


class YLeafList:
    """
    Container for a list of leafs.
    """

    def __init__(self, ytype, leaf_name):
        self.ytype = ytype
        self.leaf_name = leaf_name
        self.values = []
        self.type = ytype
        self.name = leaf_name
        self.yfilter = YFilter.not_set

    def append(self, item):
        if isinstance(item, YLeaf):
            item = item.get()
        y_leaf = YLeaf(self.type, self.name)
        y_leaf.set(item)
        self.values.append(y_leaf)

    def extend(self, items):
        for item in items:
            self.append(item)

    def set(self, other):
        if not isinstance(other, YLeafList):
            raise YModelError(f"Invalid value '{other}' assigned to YLeafList '{self.leaf_name}'")
        else:
            self.clear()
            for item in other:
                self.append(item)

    def __getitem__(self, arg):
        if isinstance(arg, slice):
            indices = arg.indices(len(self))
            ret = YLeafList(self.ytype, self.leaf_name)
            values = [self.__getitem__(i).get() for i in range(*indices)]
            ret.extend(values)
        else:
            index = len(self) + arg if arg < 0 else arg
            ret = self.values[index]
        return ret

    def __str__(self):
        rep = [i for i in self.get_yleafs()]
        return f"{self.__class__.__name__}('{self.leaf_name}', {rep})"

    def __eq__(self, other):
        if isinstance(other, YLeafList):
            return self.values == other.get_yleafs()
        return False

    def __len__(self):
        return len(self.values)

    def get_name_leafdata(self):
        """
        returns a list(tuple(str, LeafData)), where each tuple contains name and leafdata of a leaf
        """
        name_values = []
        for value in self.values:
            leaf_name_data = value.get_name_leafdata()
            val = value.get()
            name_values.append(
                (
                    f'{leaf_name_data[0]}[.="{val}"]',
                    LeafData("", self.yfilter, value.is_set,
                             value.value_namespace, value.value_namespace_prefix)
                )
            )
        return name_values

    def get_yleafs(self):
        yleafs = []
        yleafs = self.values
        return yleafs

    def clear(self):
        self.values.clear()


class LeafDataList(list):
    pass


class ChildrenMap(dict):
    pass


class Entity:
    """
    Base class for yangkit generated model
    """

    def __init__(self):

        self.parent = None

        self.yang_name = ""
        self.yang_parent_name = ""
        self.yfilter = YFilter.not_set

        self.is_presence_container = False
        self.is_top_level_class = False
        self.has_list_ancestor = False
        self.ignore_validation = False

        self.ylist_key_names = []

        self._is_frozen = False
        self.ylist_key = None

        self._logger = logging.getLogger("yangkit")

        self._children_name_map = OrderedDict()
        self._child_classes = OrderedDict()
        self._leafs = OrderedDict()
        self._segment_path = lambda: ''
        self._absolute_path = lambda: ''
        self._python_type_validation_enabled = False # NOTE has to be enabled

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        if (not self.has_data()) and (not other.has_data()):
            return True
        if (not self.has_data()) or (not other.has_data()):
            return False
        self._logger.debug(
            f"Comparing equality of '{self.get_segment_path()}' and '{other.get_segment_path()}'")

        self_children = self.get_children()
        other_children = other.get_children()

        if get_entity_path(self, self.parent) == get_entity_path(other, other.parent):
            if self_children != other_children:
                self._logger.debug(
                    f"Children are not equal '{self.__dict__}' and '{other.__dict__}'")
                return False

        else:
            self._logger.debug(
                f"Entity paths are not equal: '{self.yang_name}' and '{other.yang_name}'")
            return False

        return True

    def __ne__(self, other):
        if not isinstance(other, Entity):
            return True
        if self.has_data() and (not other.has_data()):
            return True
        if (not self.has_data()) and other.has_data():
            return True
        self._logger.debug(
            f"Comparing inequality of '{self.get_segment_path()}' and '{other.get_segment_path()}'")

        self_children = self.get_children()
        other_children = other.get_children()

        if get_entity_path(self, self.parent) == get_entity_path(other, other.parent):
            if self_children != other_children:
                self._logger.debug(
                    f"Children are not equal '{self.__dict__}' and '{other.__dict__}'")
                return True
        else:
            self._logger.debug(
                f"Entity paths are not equal: '{self.yang_name}' and '{other.yang_name}'")
            return True

        return False

    def children(self):
        return self.get_children()

    def get_children(self):
        """
        The method returns a dict{key:value} where key is name of child node,
        and the corresponding value is an Entity object representing that child node.
        """
        children = ChildrenMap()
        for name in self.__dict__:
            value = self.__dict__[name]
            if isinstance(value, Entity) and name != '_top_entity':
                if name not in self._children_name_map:
                    continue
                children[name] = value
            elif isinstance(value, YList):
                count = 0
                for val in value:
                    if isinstance(val, Entity):
                        if val.get_segment_path() not in children:
                            children[val.get_segment_path()] = val
                        else:
                            children[f"{val.get_segment_path()}{count}"] = val
                            count += 1
        return children

    def get_order_of_children(self):
        """
        The method returns a list of child node names,
        preserving the same order as in the _child_classes attribute.
        """
        order = []
        for yang_name in self._child_classes:
            name = self._child_classes[yang_name][0]
            value = self.__dict__[name]
            if isinstance(value, YList):
                for val in value:
                    if isinstance(val, Entity):
                        order.append(val.get_segment_path())
            elif isinstance(value, Entity):
                order.append(name)
        return order

    def get_child_by_name(self, child_yang_name, segment_path):
        """
        This method first tries to find a child node with "child_yang_name" or "segment_path" in "self._children_name_map";
        if child is not found, it fetches the child with "child_yang_name" from self._child_classes
        and also updates _children_name_map.

        :param child_yang_name: YANG name of the child
        :param segment_path: segment path of the child
        """

        for seg in [child_yang_name, segment_path]:
            for name in self._children_name_map:
                if seg == self._children_name_map[name]:
                    if self.__dict__[name]:
                        return name, self.__dict__[name]

        found = False
        self._logger.debug(f"Looking for '{child_yang_name}'")
        if child_yang_name in self._child_classes:
            found = True
        else:
            self._logger.debug(
                f"Could not find child '{child_yang_name}' in '{self._child_classes}'")
        if found:
            attr, clazz = self._child_classes[child_yang_name]
            is_list = isinstance(getattr(self, attr), YList)
            child = clazz()
            child.parent = self
            if not is_list:
                self._children_name_map[attr] = child_yang_name
                setattr(self, attr, child)
            else:
                getattr(self, attr).append(child)

            return attr, getattr(self, attr)

        return None, None

    def has_data(self):
        """
        Returns True, if any leaf in this entity or its child entity is assigned value; False otherwise
        """
        if hasattr(self, 'is_presence_container') and self.is_presence_container:
            return True

        for name, value in vars(self).items():
            if name == "parent":
                continue
            if isinstance(value, YFilter) and value.value != 'not_set':
                return True
            if name in self._leafs:
                leaf = _get_leaf_object(self._leafs[name])
                if _is_yleaf(leaf):
                    if value is not None:
                        if not isinstance(value, Bits) or value.get_bitmap():
                            return True
                elif _is_yleaflist(leaf) and value:
                    return True
            if isinstance(value, Entity) and value.has_data():
                return True
            elif isinstance(value, YList):
                for val in value:
                    if val.has_data():
                        return True
        return False

    def set_value(self, path, value, name_space='', name_space_prefix=''):
        """
        Sets the value of leaf with name matching "path"
        """
        for name, leaf in self._leafs.items():
            leaf = _get_leaf_object(leaf)
            if _leaf_name_matches(leaf, path):
                v = _get_decoded_value_object(self._leafs[name], self, value)
                if _is_yleaf(leaf):
                    self._assign_yleaf(name, value, v)
                elif isinstance(leaf, YLeafList):
                    self._assign_yleaflist(name, value, v)

    def get_name_leaf_data(self):
        """
        This method can be used to get the leafdata of all the leafs of a node.
        It returns an object of type LeafDataList, in which each element is LeafData of a leaf.
        """
        leaf_name_data = LeafDataList()
        for name in self._leafs:
            value = self.__dict__[name]
            leaf = _get_leaf_object(self._leafs[name])
            if isinstance(value, YFilter):
                self._logger.debug(f"YFilter assigned to '{name}', '{value}'")
                leaf.yfilter = value
                if isinstance(leaf, YLeaf):
                    leaf_name_data.append(leaf.get_name_leafdata())
                elif isinstance(leaf, YLeafList):
                    leaf_name_data.extend(leaf.get_name_leafdata())
            elif value is not None and not isinstance(value, list):
                leaf.set(value)
                leaf_name_data.append(leaf.get_name_leafdata())
            elif isinstance(value, list) and value:
                leaf_list = YLeafList(YType.str, leaf.name)
                for item in value:
                    _validate_value(self._leafs[name], name, item, self._logger)
                    if isinstance(item, bool):
                        item = 'true' if item is True else 'false'
                    leaf_list.append(item)
                leaf_name_data.extend(leaf_list.get_name_leafdata())
        self._logger.debug(
            f"Get name leaf data for '{self.yang_name}'. Count: {len(leaf_name_data)}")
        for leaf in leaf_name_data:
            leaf_value = leaf[1].value
            if "'" in leaf_value:
                leaf_value.replace("'", "\'")
            self._logger.debug(
                f'Leaf data name: "{leaf[0]}", value: "{leaf_value}", yfilter: "{leaf[1].yfilter}", is_set: "{leaf[1].is_set}"')

        return leaf_name_data

    def get_segment_path(self):
        """
        This method gives segment path of the node.
        """
        path = self._segment_path()
        if ("[" in path) and hasattr(self, 'ylist_key_names') and self.ylist_key_names:
            path = path.split('[')[0]
            for attr_name in self.ylist_key_names:
                leaf = _get_leaf_object(self._leafs[attr_name])
                if leaf is not None:
                    key = self.__dict__[attr_name]
                    attr_str = '' if isinstance(key, Empty) else format(key)
                    if isinstance(self.__dict__[attr_name], bool):
                        attr_str = 'true' if attr_str == 'True' else 'false'
                    if "'" in attr_str:
                        path += f'[{leaf.name}="{attr_str}"]'
                    else:
                        path += f"[{leaf.name}='{attr_str}']"
                else:
                    # should never get here
                    return self._segment_path()
        elif self.ylist_key is not None:
            # the entity is member of keyless YList
            try:
                index = int(self.ylist_key) % 1000000
            except:
                index = self.ylist_key
            path += f'[{index}]'
        return path

    def path(self):
        """
        This method gives segment path of the node.
        """
        return self.get_segment_path()

    def get_absolute_path(self):
        """
        This method gives absolute path of the node.
        """
        path = self.get_segment_path()
        if self.parent is not None:
            path = self.parent.get_absolute_path() + '/' + path
        elif not self.is_top_level_class:
            # it is the best available approximation
            path = self._get_absolute_path()
        return path

    def _get_absolute_path(self):
        path = self._absolute_path()
        if not path and self.is_top_level_class:
            path = self.get_segment_path()
            if '[' in path:
                path = path.split('[')[0]
        return path

    def _perform_setattr(self, clazz, leaf_names, name, value):
        """
        This method sets the value "value" to attribute "name"
        """
        with _handle_type_error():
            if name == '_is_presence':
                # support for Entity._is_presence = True
                self._perform_setattr(clazz, leaf_names, 'is_presence_container', value)
                return
            if name != 'yfilter' and name != 'parent' and name != 'ignore_validation' \
                    and hasattr(self, '_is_frozen') and self._is_frozen \
                    and name not in self.__dict__:
                raise YModelError(
                    f"Attempt to assign unknown attribute '{name}' to '{self.__class__.__name__}'.")
            if name in self.__dict__ and isinstance(self.__dict__[name], YList):
                raise YModelError(f"Attempt to assign value of '{value}' to YList ldata. "
                                  "Please use list append or extend method.")
            if name in leaf_names and name in self.__dict__:
                if self._python_type_validation_enabled:
                    _validate_value(self._leafs[name], name, value, self._logger)
                leaf = _get_leaf_object(self._leafs[name])
                prev_value = self.__dict__[name]
                self.__dict__[name] = value

                if not isinstance(value, YFilter):
                    if isinstance(leaf, YLeaf):
                        leaf.set(value)
                    elif isinstance(leaf, YLeafList):
                        for item in value:
                            leaf.append(item)
                else:
                    self._logger.debug(f'Setting "{value}" to "{name}"')
                    leaf.yfilter = value
                    if prev_value is not None:
                        self._logger.debug(f'Storing previous value "{prev_value}" to "{name}"')
                        if isinstance(leaf, YLeaf):
                            leaf.set(prev_value)
                        elif isinstance(leaf, YLeafList):
                            for item in prev_value:
                                leaf.append(item)

            elif name != 'yfilter' and isinstance(value, YFilter) and value != YFilter.not_set:
                _, child = self.get_child_by_name(self._children_name_map[name], "")
                child.yfilter = value
            else:
                if isinstance(value, Entity):
                    if hasattr(value, "parent") and name != "parent":
                        if not value.is_top_level_class:
                            value.parent = self
                self.__dict__[name] = value

    def _assign_yleaf(self, name, value, v):
        if isinstance(self.__dict__[name], Bits):
            self.__dict__[name][value] = True
        else:
            if v is not None:
                self.__dict__[name] = v
            else:
                self.__dict__[name] = value

    def _assign_yleaflist(self, name, value, v):
        if v is not None:
            self.__dict__[name].append(v)
        else:
            self.__dict__[name].append(value)

    def __str__(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}"


def get_entity_path(entity, parent=None):
    """
    This method is used to calculate entity path. Computes absolute_path if parent is None; relative_path otherwise
    """
    ret_path = ""

    if parent is None:
        if entity.has_list_ancestor:
            raise YInvalidArgumentError(
                f"ancestor for entity cannot be nullptr as one of the ancestors is a list. Path: {entity.get_segment_path()}")

        abs_path = entity.get_absolute_path()
        if not abs_path:
            ret_path += entity.get_segment_path()
        else:
            ret_path += abs_path

    else:
        if entity.is_top_level_class:
            raise YInvalidArgumentError(
                f"ancestor has to be nullptr for top-level node. Path: {entity.get_segment_path()}")

        ret_path += get_relative_entity_path(entity, parent, ret_path)

    return EntityPath(ret_path, entity.get_name_leaf_data())


def get_relative_entity_path(curr_node, ancestor, path):
    """
    This method gives the path of entity relative to ancestor
    """
    ret_path = path

    if ancestor is None:
        raise YInvalidArgumentError("ancestor should not be null.")

    parent = curr_node.parent
    parents = []
    while parent != None and parent != ancestor:
        parents.append(parent)
        parent = parent.parent

    if parent is None:
        raise YInvalidArgumentError("parent is not in the ancestor hierarchy.")

    parents.reverse()
    parent = None
    for p1 in parents:
        if parent:
            ret_path += "/"
        else:
            parent = p1
        ret_path += p1.get_segment_path()

    if parent:
        ret_path += "/"

    ret_path += curr_node.get_segment_path()

    return ret_path


def absolute_path(entity):
    """
    This method gives the absolute path of entity from the top
    """
    path = entity.get_segment_path()
    if (not entity.is_top_level_class) and entity.parent:
        path = absolute_path(entity.parent) + "/" + path

    return path


# NOTE taken from https://github.com/CiscoDevNet/ydk-gen/blob/master/sdk/python/core/ydk/types/py_types.py
class EntityCollection(object):
    """
    EntityCollection is a wrapper class around ordered dictionary collection of type OrderedDict.
    It is created specifically to collect Entity class instances,
    Each Entity instance has unique segment path value, which is used as a key in the dictionary.
    """

    def __init__(self, *entities):
        self._logger = logging.getLogger("yangkit")
        self._entity_map = OrderedDict()
        for entity in entities:
            self.append(entity)

    def __eq__(self, other):
        if not isinstance(other, EntityCollection):
            return False
        return self._entity_map.__eq__(other._entity_map)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return self._entity_map.__len__()

    def _key(self, entity):
        return entity.path()

    def append(self, entities):
        """
        Adds new elements to the end of the dictionary. Allowed entries:
          - instance of Entity class
          - list of Entity class instances
        """
        if entities is None:
            self._logger.debug("Cannot add None object to the EntityCollection")
        elif isinstance(entities, Entity):
            key = self._key(entities)
            self._entity_map[key] = entities
        elif isinstance(entities, list):
            for entity in entities:
                if isinstance(entity, Entity):
                    key = self._key(entity)
                    self._entity_map[key] = entity
                elif entity is None:
                    self._logger.debug("Cannot add None object to the EntityCollection")
                else:
                    msg = f"Argument {type(entity)} is not supported by EntityCollection class; data ignored"
                    self._log_error_and_raise_exception(msg, YInvalidArgumentError)
        else:
            msg = f"Argument {type(entities)} is not supported by EntityCollection class; data ignored"
            self._log_error_and_raise_exception(msg, YInvalidArgumentError)

    def _log_error_and_raise_exception(self, msg, exception_class):
        self._logger.error(msg)
        raise exception_class(msg)

    def entities(self):
        """
        Returns list of all entities in the collection.
        If collection is empty, it returns an empty list.
        """
        return list(self._entity_map.values())

    def keys(self):
        """
        Returns list of keys for the collection entities.
        If collection is empty, it returns an empty list.
        """
        return list(self._entity_map.keys())

    def has_key(self, key):
        return key in self.keys()

    def get(self, item):
        return self.__getitem__(item)

    def __getitem__(self, item):
        """
        Returns entity store in the collection.
        Parameter 'item' could be:
         - a type of int (ordered number of entity)
         - type of str (segment path of entity)
         - instance of Entity class
        """
        entity = None
        if isinstance(item, int):
            if 0 <= item < len(self):
                entity = self.entities()[item]
        elif isinstance(item, str):
            if item in self.keys():
                entity = self._entity_map[item]
        elif isinstance(item, Entity):
            key = self._key(item)
            if key in self.keys():
                entity = self._entity_map[key]
        else:
            msg = f"Argument {type(item)} is not supported by EntityCollection class; data ignored"
            self._log_error_and_raise_exception(msg, YInvalidArgumentError)
        return entity

    def clear(self):
        """
        Deletes all the members of collection
        """
        self._entity_map.clear()

    def pop(self, item=None):
        """
        Deletes collection item.
        Parameter 'item' could be:
         - type of int (ordered number of entity)
         - type of str (segment path of entity)
         - instance of Entity class
        Returns entity of deleted instance or None if item is not found.
        """
        entity = None
        if len(self) == 0:
            pass
        elif item is None:
            key, entity = self._entity_map.popitem()
        elif isinstance(item, int):
            entity = self.__getitem__(item)
            if entity is not None:
                key = self._key(entity)
                entity = self._entity_map.pop(key)
        elif isinstance(item, str):
            if item in self.keys():
                entity = self._entity_map.pop(item)
        elif isinstance(item, Entity):
            key = self._key(item)
            if key in self.keys():
                entity = self._entity_map.pop(key)
        return entity

    def __delitem__(self, item):
        return self.pop(item)

    def __iter__(self):
        return iter(self.entities())

    def __str__(self):
        ent_strs = list()
        for entity in self.entities():
            ent_strs.append(format(entity))
        return f"Entities in {self.__class__.__name__}: {ent_strs}"


class Filter(EntityCollection):
    pass


class Config(EntityCollection):
    pass


class YList(EntityCollection):
    """ Represents a list with support for hanging a parent

        All YANG based entity classes that have lists in them use YList
        to represent the list.

        The "list" statement is used to define an interior data node in the
        schema tree.  A list node may exist in multiple instances in the data
        tree.  Each such instance is known as a list entry.  The "list"
        statement takes one argument, which is an identifier, followed by a
        block of sub-statements that holds detailed list information.

        A list entry is uniquely identified by the values of the list's keys, if defined.
        The keys then could be used to get entities from the YList.
    """

    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.counter = 1000000

    def __setattr__(self, name, value):
        if name == 'yfilter' and isinstance(value, YFilter):
            for e in self:
                e.yfilter = value
        super().__setattr__(name, value)

    def _key(self, entity):
        key_list = []
        if hasattr(entity, 'ylist_key_names'):
            for key in entity.ylist_key_names:
                if hasattr(entity, key):
                    attr = entity.__dict__[key]
                    if attr is None:
                        key_list = []
                        break
                    if isinstance(attr, Empty) or not str(attr):
                        continue  # Skip empty key
                    if not isinstance(attr, str):
                        attr = format(attr)
                    key_list.append(attr)
        if not key_list:
            self.counter += 1
            key = format(self.counter)
        elif len(key_list) == 1:
            key = key_list[0]
        else:
            key = tuple(key_list)
        return key

    def append(self, entity):
        entity.parent = self.parent
        if entity is None:
            self._log_error_and_raise_exception(
                "Cannot add None object to the YList", YInvalidArgumentError)
        elif isinstance(entity, Entity):
            key = self._key(entity)
            self._entity_map[key] = entity
            entity.ylist_key = key
        else:
            msg = f"Argument {type(entity)} is not supported by YList class; data ignored"
            self._log_error_and_raise_exception(msg, YInvalidArgumentError)

    def extend(self, entity_list):
        for entity in entity_list:
            self.append(entity)

    def clear(self):
        """
        Deletes all the members of collection
        """
        self._entity_map.clear()

    def keys(self):
        return list(self._entity_map.keys())

    def entities(self):
        return list(self._entity_map.values())

    def __getitem__(self, item):
        entity = None
        if isinstance(item, int) and 0 <= item < len(self):
            entity = self.entities()[item]
        elif self.has_key(item):
            entity = self._entity_map[item]
        elif not isinstance(item, str):
            entity = self._entity_map[format(item)]
        return entity

    def __len__(self):
        return self._entity_map.__len__()


# next set of functions are taken from https://github.com/CiscoDevNet/ydk-gen/blob/master/sdk/python/core/ydk/types/py_types.py

def _get_class(py_mod_name, clazz_name):
    module = importlib.import_module(py_mod_name)
    return reduce(getattr, clazz_name.split('.'), module)


def _get_class_instance(py_mod_name, clazz_name):
    return _get_class(py_mod_name, clazz_name)()


def _get_decoded_value_object(leaf_tuple, entity, value):
    if not isinstance(leaf_tuple, tuple):
        return None
    typs = leaf_tuple[1]
    value_object = None
    for typ in typs:
        if _is_identity(typ):
            value_object = _decode_identity_value_object(entity, value)
        elif _is_enum(typ):
            value_object = _decode_enum_value_object(typ, value)
        elif _is_bits(typ, value):
            value_object = _decode_bits_value_object(typ, value)
        else:
            value_object = _decode_other_type_value_object(typ, value)
        if value_object is not None:
            break
    return value_object


def _validate_value(leaf_tuple, name, value, logger):
    if not isinstance(leaf_tuple, tuple):
        return
    if isinstance(value, YFilter):
        return
    typs = leaf_tuple[1]
    for typ in typs:
        if _is_identity(typ):
            if _validate_identity_value_object(typ, value):
                return
        elif _is_enum(typ):
            if _validate_enum_value_object(typ, value):
                return
        elif _is_bits(typ, value):
            return
        else:
            if _validate_other_type_value_object(typ, value):
                return
    err_msg = f"Invalid value {value} for '{name}'. Got type: '{type(value).__name__}'. Expected types: {_get_types_string(typs)}"
    logger.error(err_msg)
    raise YModelError(err_msg)


def _get_types_string(typs):
    typs_string = []
    for typ in typs:
        if isinstance(typ, tuple):
            s = '.'.join(typ)
            if s.endswith('.'):
                s = s[:-1]
            typs_string.append(f"'{s}'")
        else:
            typs_string.append(f"'{typ}'")
    return ' or '.join(typs_string)


def _is_identity(typ):
    return isinstance(typ, tuple) and len(typ) == 2


def _is_enum(typ):
    return isinstance(typ, tuple) and len(typ) == 3


def _is_bits(typ, value):
    return typ == 'Bits' and ((isinstance(value, Bits) and value.get_bitmap()) or isinstance(value, str))


def _validate_identity_value_object(typ, value):
    if not _is_identity(typ):
        return False
    mod = importlib.import_module(typ[0])
    base_identity_class = getattr(mod, typ[1])
    return isinstance(value, base_identity_class)


def _decode_identity_value_object(entity, value):
    bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(entity))
    if 'IDENTITY_LOOKUP' in bundle_yang_ns.__dict__:
        identity_lookup = bundle_yang_ns.__dict__['IDENTITY_LOOKUP']
        if value in identity_lookup:
            (py_mod_name, identity_clazz_name) = identity_lookup[value]
            return _get_class_instance(py_mod_name, identity_clazz_name)
    return None


def _get_enum_class(module_name, class_name, nested_class_name):
    mod = importlib.import_module(module_name)
    if not nested_class_name:
        tmp = ''
    else:
        tmp = f'.{nested_class_name}'
    clazz_name = f'{class_name}{tmp}'
    enum_clazz = None
    for clazz in clazz_name.split('.'):
        if enum_clazz is None:
            enum_clazz = getattr(mod, clazz)
        else:
            enum_clazz = getattr(enum_clazz, clazz)
    return enum_clazz


def _validate_enum_value_object(typ, value):
    if not isinstance(value, Enum.YLeaf):
        return False
    if not _is_enum(typ):
        return False
    enum_clazz = _get_enum_class(typ[0], typ[1], typ[2])
    for _, val in enum_clazz.__dict__.items():
        if isinstance(val, Enum.YLeaf) and value.name == val.name:
            return True
    return False


def _decode_enum_value_object(typ, value):
    if not _is_enum(typ):
        return None
    enum_clazz = _get_enum_class(typ[0], typ[1], typ[2])
    for _, v in enum_clazz.__dict__.items():
        if isinstance(v, Enum.YLeaf) and value == v.name:
            return v
    return None


def _decode_bits_value_object(typ, value):
    if not _is_bits(typ, value):
        return None
    if isinstance(value, Bits):
        v = value
    else:
        v = Bits()
        v[value] = True
    return v


def _validate_other_type_value_object(typ, value):
    if typ == 'Empty':
        return isinstance(value, Empty)
    if typ == 'str' and isinstance(value, (bytes, str)):
        return True
    if typ == 'int' and isinstance(value, int):
        return True
    typ = eval(typ)
    return isinstance(value, typ)


def _decode_other_type_value_object(typ, value):
    value_object = None
    if typ == 'bool':
        return True if value == 'true' else False
    elif typ == 'Empty':
        return Empty()
    typ = eval(typ)
    try:
        value_object = typ(value)
    except:
        pass
    return value_object


def _get_leaf_object(leaf):
    # Backward compatibility
    if isinstance(leaf, tuple):
        return leaf[0]
    return leaf


def _leaf_name_matches(leaf, path):
    return leaf.name == path


def _is_yleaf(leaf):
    return isinstance(leaf, YLeaf)


def _is_yleaflist(leaf):
    return isinstance(leaf, YLeafList)
