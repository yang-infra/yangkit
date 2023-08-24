import re
import json
import logging
from yangkit.types import YList
from yangkit.filters import YFilter
from yangkit.utilities.entity import get_bundle_name, get_bundle_yang_ns, find_prefix_in_namespace_lookup, segmentalize

log = logging.getLogger("yangkit")

class JsonEncoder(object):
    """
    JSON Encoder Class
    """

    @staticmethod
    def encode(entity, optype):
        """
        Converts an Entity object to JSON payload

        :param entity: Entity Object
        :param optype: Operation type
        """

        if isinstance(entity, YList):
            return JsonEncoder.encode_list(entity.entities(), optype)

        if not _is_edit_optype(optype):
            return JsonEncoder._format_xpath(entity.get_absolute_path())

        original_yfilter = _attach_yfilter(entity, optype)
        top_entity = JsonEncoder._traverse_to_top_entity(entity)

        root, update_paths, delete_paths = {}, [], []
        xpath = JsonEncoder._format_xpath(top_entity.get_absolute_path())
        JsonEncoder._encode_helper(top_entity, root, delete_paths, optype)

        entity.yfilter = original_yfilter

        if root:
            update_paths.append((xpath, root))
        return update_paths, delete_paths

    @staticmethod
    def encode_list(entities, optype):
        """
        Converts an list of Entity objects to JSON payload

        :param entity: Entity Object
        :param optype: Operation type
        """

        if not _is_edit_optype(optype):
            get_paths = []
            for entity in entities:
                get_paths.append(JsonEncoder._format_xpath(entity.get_absolute_path()))
            return get_paths

        update_paths, delete_paths = [], []
        for entity in entities:
            update_paths_, delete_paths_ = JsonEncoder.encode(entity, optype)
            update_paths.extend(update_paths_)
            delete_paths.extend(delete_paths_)

        return update_paths, delete_paths

    @staticmethod
    def _traverse_to_top_entity(entity):
        """
        Traverse upwards the hierarchy until entity is not a list member

        :param entity: Entity Object
        """
        while entity.has_list_ancestor and entity.parent is not None:
            entity = entity.parent
        return entity

    @staticmethod
    def _encode_helper(entity, root, delete_paths, optype):
        """
        Populates the root element by parsing entity in a reccursive manner

        :param entity: Entity object to be encoded
        :param root: root of json
        :param optype: Operation type
        :param is_filter: Bool
        """
        if not entity.has_data():
            return

        if entity.yfilter == YFilter.delete:
            delete_paths.append(JsonEncoder._format_xpath(entity.get_absolute_path()))
            return

        # creates leaf elements
        for name_value in entity.get_name_leaf_data():
            leaf_name = name_value[0]
            leaf_data = name_value[1]

            if leaf_data.yfilter == YFilter.delete:
                delete_paths.append(JsonEncoder._format_xpath(f"{entity.get_absolute_path()}/{leaf_name}"))
            elif leaf_data.is_set:
                JsonEncoder._create_leaf_ele(leaf_name, leaf_data, root)

        for _, child in entity.get_children().items():
            # appends child json to root
            child_elem = {}
            JsonEncoder._encode_helper(child, child_elem, delete_paths, optype)
            if child_elem:
                # add prefix to child name if child's prefix is different from that of parent
                bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(child))
                prefix, _ = find_prefix_in_namespace_lookup(child.get_segment_path(), bundle_yang_ns)
                if prefix:
                    child_name_with_prefix = f"{prefix}:{child.yang_name}"
                else:
                    child_name_with_prefix = child.yang_name

                if hasattr(child, "ylist_key") and child.ylist_key is not None:
                    # ylist item
                    if not child_name_with_prefix in root:
                        root[child_name_with_prefix] = []
                    root[child_name_with_prefix].append(child_elem)
                else:
                    root[child_name_with_prefix] = child_elem
    
    @staticmethod
    def _create_leaf_ele(leaf_name, leaf_data, parent_json):
        """
        creates {leaf_name: leaf_content} for a leaf and adds it to parent json object

        :param name_value: tuple(leaf_name, LeafData)
        :param parent_json: json for parent_entity
        """
        
        if not leaf_data.is_set:
            return

        leaf_type = "leaf"

        match = re.search(r'\[.="', leaf_name)
        if match:
            span = match.span()
            leaf_data.value = leaf_name[span[1]:-2]
            leaf_name = leaf_name[:span[0]]
            leaf_type = "leaf-list"

        # prefix = get_leafdata_prefix(entity, leaf_name, leaf_data)
        prefix = ""
        content = prefix + leaf_data.value

        if leaf_type == "leaf-list":
            if not leaf_name in parent_json:
                parent_json[leaf_name] = []
            parent_json[leaf_name].append(content)
        else:
            parent_json[leaf_name] = content

    @staticmethod
    def _format_xpath(path):
        """
        Removes the char "'" from xpath.

        Example:
            "openconfig-interfaces:interfaces/interface[name='1/1/c1/2'][id='None']" is converted to \
            "openconfig-interfaces:interfaces/interface[name=1/1/c1/2]"
        """
        segments = segmentalize(path)
        ret_segments = []
        for segment in segments:
            segment_ = segment.split('[')[0]
            keys = re.findall(r'\[(.*?)\]', segment)
            for key in keys:
                key_name, key_value = key.split("=")
                if key_value != "'None'":
                    key_value = key_value.replace("'", "")
                    segment_ += f"[{key_name}={key_value}]"
            ret_segments.append(segment_)

        return '/'.join(ret_segments)

    @staticmethod
    def get_pretty(json_obj):
        """
        returns prettier json
        """
        return json.dumps(json_obj, indent=4)


def _is_edit_optype(optype):
    """
    Checks whether the operation is edit-config or not

    :param optype: operation type
    """
    if optype == 'create' or optype == 'update' or optype == 'delete':
        return True
    return False


def _attach_yfilter(entity, optype):
    """
    Sets the yfilter attribute of entity when the operation type is edit

    :param optype: operation type
    """
    original_yfilter = entity.yfilter
    if _is_edit_optype(optype) and original_yfilter == YFilter.not_set:
        entity.yfilter = YFilter.delete if optype == 'delete' else YFilter.update
    return original_yfilter
