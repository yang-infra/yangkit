from lxml import etree
from yangkit.types import YList
from yangkit.utilities.logger import log
from yangkit.types import Entity
from yangkit.utilities.entity import get_internal_node, get_top_level_class
from yangkit.errors import YCodecError


class XmlDecoder(object):
    """
    XML Decoder Class
    """

    @staticmethod
    def decode(payload, model):
        """
        Converts an XML payload to the corresponding top-level class and returns
        a child container with the same absolute path as the provided model.

        :param payload: XML Payload
        :param model: Entity object; required to find the bundle name
        """

        top_entity = get_top_level_class(model)

        if payload:
            payload_tree = etree.fromstring(payload.encode('utf-8'))
            root = payload_tree.getroottree().getroot()

            try:
                XmlDecoder._decode_helper(root, top_entity)
            except Exception as error:
                error.payload = payload
                log.error(error)
                raise YCodecError(error)
        else:
            log.debug("payload is empty")

        # fetching internal node from top_entity with path equivalent to model's absolute_path
        internal_node = get_internal_node(top_entity, model.get_absolute_path())
        if isinstance(internal_node, YList):
            return internal_node.entities()
        return internal_node

    @staticmethod
    def decode_action_response(payload, model):
        """
        decode wrapper to handle response in action operation

        :param payload: XML Payload
        :param model: An instance of yangkit.types.Entity which contains decoded information
        """

        if not payload:
            log.debug("payload is empty")
            return

        payload_tree = etree.fromstring(payload.encode('utf-8'))
        root = payload_tree.getroottree().getroot()
        try:
            XmlDecoder._decode_helper(root, model)
        except Exception as error:
            error.payload = payload
            log.error(error)
            raise YCodecError(error)

    @staticmethod
    def _decode_helper(root, entity):
        """
        Populates the entity object by traversing the element tree in a reccursive manner

        :param root: root of the element tree
        :param entity: Enitity object
        """
        if not root:
            return

        for child_node in root.getchildren():
            # separate element namespace and tag
            qual_node = etree.QName(child_node)
            yname = qual_node.localname

            entity.set_value(yname, child_node.text)

            attr, child = entity.get_child_by_name(yname, "")
            if attr and child:
                if isinstance(child, YList):
                    ylist_item = child.pop()
                    if hasattr(ylist_item, attr):
                        setattr(ylist_item, attr, child_node.text)
                    child.append(ylist_item)
                    XmlDecoder._decode_helper(child_node, ylist_item)
                elif isinstance(child, Entity):
                    XmlDecoder._decode_helper(child_node, child)

    @staticmethod
    def data_in_rpc_reply(rpc_reply_xml):
        """
        Returns data inside the rpc reply (<rpc-reply>data</rpc-reply>)

        :param rpc_reply_xml: rpc reply xml
        """
        data_tree = etree.fromstring(rpc_reply_xml.encode('utf-8'))
        if len(data_tree):
            return etree.tostring(data_tree[0], encoding='utf-8', method='xml').decode('utf-8')
        return ''
