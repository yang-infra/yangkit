import re
import uuid
import json
from yangkit.types import Entity, YList
from yangkit.filters import YFilter
from yangkit.utilities.entity import get_bundle_name, get_bundle_yang_ns, get_top_level_class, find_prefix_in_namespace_lookup


class JsonEncoder(object):
    """
    JSON Encoder Class
    """

    @staticmethod
    def encode(entity: Entity, optype):
        """
        Converts an Entity object to JSON payload

        :param entity: Entity Object
        :param optype: Operation type
        """
        abs_path = entity.get_absolute_path()
        if not _optype_is_set(optype):
            # xpath is enough
            return abs_path
        else:
            root = {}
            JsonEncoder._encode_helper(entity, root, optype)
            return (abs_path, root)

    @staticmethod
    def _encode_helper(entity, root, optype, is_filter=False):
        """
        Populates the root element by parsing entity in a reccursive manner

        :param entity: Entity object to be encoded
        :param root: root of json
        :param optype: Operation type
        :param is_filter: Bool
        """
        if not is_filter and not entity.has_data():
            return

        # creates leaf elements
        for name_value in entity.get_name_leaf_data():
            # appends leaf json to root
            JsonEncoder._create_leaf_ele(name_value, root, entity)

        for _, child in entity.get_children().items():
            # appends child json to root
            child_elem = dict()
            JsonEncoder._encode_helper(child, child_elem, optype)
            if child_elem:
                if hasattr(child, "ylist_key") and child.ylist_key is not None:
                    # ylist item
                    if not child.yang_name in root:
                        root[child.yang_name] = []
                    root[child.yang_name].append(child_elem)
                else:
                    root[child.yang_name] = child_elem
    
    @staticmethod
    def _create_leaf_ele(name_value, parent_json, parent_entity):
        """
        creates {leaf_name: leaf_content} for a leaf and adds it to parent json object

        :param name_value: tuple(leaf_name, LeafData)
        :param parent_json: json parent_entity object
        :parent_entity: parent entity
        """
        leaf_name = name_value[0]
        leaf_data = name_value[1]
        
        if leaf_data.is_set or leaf_data.yfilter != YFilter.not_set:
            leaf_type = "leaf"

            match = re.search(r'\[.="', leaf_name)
            if match:
                span = match.span()
                leaf_data.value = leaf_name[span[1]:-2]
                leaf_name = leaf_name[:span[0]]
                leaf_type = "leaf-list"
            
            if leaf_data.is_set:
                # prefix = get_leafdata_prefix(entity, leaf_name, leaf_data)
                prefix = ""
                content = prefix + leaf_data.value
            elif leaf_data.yfilter != YFilter.not_set:
                content = ""

            if leaf_type == "leaf-list":
                if not leaf_name in parent_json:
                    parent_json[leaf_name] = []
                parent_json.append(content)
            else:
                parent_json[leaf_name] = content

    @staticmethod
    def prepend_config(json_obj):
        return json_obj

    @staticmethod
    def get_pretty(json_obj):
        """
        returns prettier json
        """
        return json.dumps(json_obj, indent=4)

    
def _optype_is_set(optype):
    """
    Checks whether the operation is "set" or not

    :param optype: operation type
    """
    if optype == 'create' or optype == 'update' or optype == 'delete':
        return True
    return False

    