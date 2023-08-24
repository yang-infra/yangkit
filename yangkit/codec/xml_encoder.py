import uuid
from lxml import etree
from yangkit.utilities.logger import log
from yangkit.types import Entity, YList
from yangkit.filters import YFilter
from yangkit.errors import YInvalidArgumentError
from yangkit.utilities.entity import get_bundle_name, get_bundle_yang_ns, get_top_level_class, find_prefix_in_namespace_lookup, segmentalize

NETCONF_NS = 'urn:ietf:params:xml:ns:netconf:base:1.0'


class XmlEncoder(object):
    """
    XML Encoder Class
    """

    @staticmethod
    def encode(entity, optype):
        """
        Converts an Entity object to xml payload

        :param entity: Entity Object
        :param optype: Operation type
        """

        if not isinstance(entity, (Entity, YList)):
            error_msg = """Invalid 'entity' type. Expected types: yangkit.types.Entity; yangkit.types.YList; """
            log.error(error_msg)
            raise YInvalidArgumentError(error_msg)

        root = etree.Element('a')

        if not entity.parent:
            preamble = XmlEncoder._create_preamble(entity, root)
        else:
            if isinstance(entity, YList):
                preamble = XmlEncoder._encode_ancestors(entity.parent, root, optype)
            else:
                preamble = XmlEncoder._encode_ancestors(entity.parent, root, optype, 
                                                        entity.has_list_ancestor)

        is_filter = (optype == 'read' or optype == 'action')

        if isinstance(entity, YList):
            for item in entity:
                original_yfilter = _attach_yfilter(item, optype)
                XmlEncoder._encode_helper(item, preamble, optype, is_filter)
                item.yfilter = original_yfilter
        else:
            original_yfilter = _attach_yfilter(entity, optype)
            XmlEncoder._encode_helper(entity, preamble, optype, is_filter)
            entity.yfilter = original_yfilter

        if optype == 'action':
            XmlEncoder._remove_input_node_in_action_rpc(root[0])

        return etree.tostring(root[0],
                              method='xml', pretty_print='True',
                              encoding='utf-8').decode('utf-8')

    @staticmethod
    def encode_list(entities, optype):
        """
        Converts a list of entity objects to xml payload

        :param entity: Entity Object
        :param optype: Operation type
        """
        ret_xml_str = ""
        for entity in entities:
            ret_xml_str += XmlEncoder.encode(entity, object)
        return ret_xml_str

    @staticmethod
    def _create_preamble(entity, root):
        """
        Creates XML tags for all the nodes the top-level container up until just before the 'entity'.

        :param entity: Entity object
        :param root: root of element etree
        :return: The corresponding Element or SubElement of the parent of the specified entity.
        """

        if entity.is_top_level_class:
            return root

        segments = segmentalize(entity.get_absolute_path())

        # fetching bundle name and corresponding _yang_ns module
        bundle_name = get_bundle_name(entity)
        bundle_yang_ns = get_bundle_yang_ns(bundle_name)

        top_entity = get_top_level_class(entity)

        nsp, ns = find_prefix_in_namespace_lookup(top_entity.get_segment_path(), bundle_yang_ns)
        nsmap = {}
        if nsp and ns: nsmap[None] = ns
        root = etree.SubElement(root, top_entity.yang_name, nsmap=nsmap)

        elem = root
        curr_entity = top_entity
        for segment in segments[1:-1]:
            if '[' in segment:
                _, child = curr_entity.get_child_by_name(segment.split('[')[0], "")
            else:
                _, child = curr_entity.get_child_by_name(segment, segment)

            curr_entity = child

            nsp, ns = find_prefix_in_namespace_lookup(curr_entity.get_segment_path(), bundle_yang_ns)
            nsmap = {}
            if nsp and ns: nsmap[None] = ns
            elem = etree.SubElement(elem, curr_entity.yang_name, nsmap=nsmap)

        return elem

    @staticmethod
    def _encode_ancestors(entity, root, optype, has_list_ancestor=False):
        """
        Encodes ancestors of an entity and populates the root

        :param entity: Entity object
        :param root: etree.Element object
        :param optype: Operation type
        :param has_list_ancestor: Bool
        """
        if not entity.parent:
            p_elem = XmlEncoder._create_preamble(entity, root)
        else:
            p_elem = XmlEncoder._encode_ancestors(entity.parent, root, optype, entity.has_list_ancestor)

        bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(entity))
        nsp, ns = find_prefix_in_namespace_lookup(entity.get_segment_path(), bundle_yang_ns)
        nsmap = {}
        if nsp and ns: nsmap[None] = ns
        elem = etree.SubElement(p_elem, entity.yang_name, nsmap=nsmap)

        if has_list_ancestor:
            # encode keys
            for name_value in entity.get_name_leaf_data():
                leaf_ele = XmlEncoder._create_leaf_element(name_value, elem, entity, optype)
                if leaf_ele is not None and leaf_ele.tag.replace('-', '_') in entity.ylist_key_names:
                    elem.append(leaf_ele)

        return elem

    @staticmethod
    def _encode_helper(entity, root, optype, is_filter=False):
        """
        Populates the root element by parsing entity in a reccursive manner

        :param entity: Entity object to be encoded
        :param root: root of element tree
        :param optype: Operation type
        :param is_filter: Bool
        """
        if not is_filter and not entity.has_data():
            return

        bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(entity))
        nsp, ns = find_prefix_in_namespace_lookup(entity.get_segment_path(), bundle_yang_ns)
        nsmap = {}
        if nsp and ns: nsmap[None] = ns
        elem = etree.SubElement(root, entity.yang_name, nsmap=nsmap)

        # xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="replace"
        if optype != 'read' and entity.yfilter != YFilter.not_set and entity.yfilter != YFilter.merge:
            elem.set('{' + NETCONF_NS + '}operation', entity.yfilter.value)

        # create and append leaf elements
        for name_value in entity.get_name_leaf_data():
            leaf_ele = XmlEncoder._create_leaf_element(name_value, elem, entity, optype)
            if leaf_ele is not None:
                elem.append(leaf_ele)

        for _, child in entity.get_children().items():
            XmlEncoder._encode_helper(child, elem, optype)

    @staticmethod
    def _create_leaf_element(name_value, parent_elem, parent_entity, optype):
        """
        Creates an XML element for a leaf

        :param name_value: (leaf_name, LeafData)
        :param parent_elem: XML Element of parent_entity
        :param parent_entity: parent of leaf
        :param optype: Operation type
        """
        
        leaf_name = name_value[0]
        leaf_data = name_value[1]

        if not leaf_data.is_set and not leaf_data.yfilter != YFilter.not_set:
            return
        
        bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(parent_entity))
        nsp, ns = find_prefix_in_namespace_lookup(leaf_name, bundle_yang_ns)
        nsmap = {}
        if nsp and ns: 
            nsmap[None] = ns
            leaf_name = leaf_name.split(':')[1]

        if leaf_data.name_space and leaf_data.name_space_prefix:
            nsmap['idx'] = leaf_data.name_space
            if leaf_data.is_set and leaf_data.value.startswith(leaf_data.name_space_prefix):
                leaf_data.value = leaf_data.value.replace(leaf_data.name_space_prefix, 'idx')

        leaf_ele = etree.Element(leaf_name, nsmap=nsmap)
        if leaf_data.is_set:
            leaf_ele.text = leaf_data.value

        yfilter = leaf_data.yfilter
        if optype != 'read' and yfilter != YFilter.not_set and yfilter != YFilter.merge:
            leaf_ele.set('{' + NETCONF_NS + '}operation', yfilter.value)

        if len(parent_entity.ylist_key_names) == 1 \
            and leaf_ele.tag.replace('-', '_') == parent_entity.ylist_key_names[0] \
            and leaf_ele.tag == parent_elem.tag:

            parent_elem.text = leaf_ele.text
            return
        
        return leaf_ele

    @staticmethod
    def _remove_input_node_in_action_rpc(root):
        """
        In case of encoding action models, removes the input node and appends the input data to root node
        """
        if len(root) and root[0].tag == 'input':
            input_node = root[0]
            root.extend(input_node.getchildren())
            root.remove(input_node)

    @staticmethod
    def get_pretty(string):
        """
        returns prettier xml
        """
        parser = etree.XMLParser(remove_blank_text=True)
        element = etree.XML(string.encode('UTF-8'), parser)
        return etree.tostring(element, encoding='UTF-8', pretty_print=True).decode('UTF-8')

    @staticmethod
    def prepend_config(string):
        """
        Prepends '<config>' element to xml string
        """
        return f'''<config>{string}</config>'''

    @staticmethod
    def create_rpc(string):
        """
        Converts xml string to a valid rpc request format
        """
        message_id = f"urn:uuid:{uuid.uuid4()}"
        return f'''<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="{message_id}">{string}</rpc>'''


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
        entity.yfilter = YFilter.delete if optype == 'delete' else YFilter.merge
    return original_yfilter
