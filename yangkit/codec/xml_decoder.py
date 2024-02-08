from lxml import etree
from yangkit.types import YList
from yangkit.utilities.logger import log
from yangkit.types import Entity
from yangkit.utilities.entity import get_internal_node, get_top_level_class, get_bundle_name, get_bundle_yang_ns, find_prefix_in_namespace_lookup
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
        if not isinstance(model, Entity):
            log.error("Argument 'model' should be an Entity object")
            raise YCodecError("Argument 'model' should be an Entity object")
        else:
            internal_node = get_internal_node(top_entity, model.get_absolute_path())

        return internal_node

    @staticmethod
    def decode_action_response(payload, model):
        """
        decode wrapper to handle response in action operation

        :param payload: XML Payload
        :param model: An instance of yangkit.types.Entity which contains decoded information
        """

        if not hasattr(model, "output"):
            log.debug(f"model {model} has no attribute output")
            return

        if not payload:
            log.debug("payload is empty")
            return

        payload_tree = etree.fromstring(payload.encode('utf-8'))
        data = payload_tree.getroottree().getroot()

        bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(model))
        nsp, ns = find_prefix_in_namespace_lookup(model.get_segment_path(), bundle_yang_ns)
        nsmap = {}
        if nsp and ns: nsmap[None] = ns
        output = etree.Element("output", nsmap=nsmap)
        output.append(data)

        try:
            XmlDecoder._decode_helper(output, model.output)
        except Exception as error:
            error.payload = payload
            log.error(error)
            raise YCodecError(error)

        return model

    @staticmethod
    def _decode_helper(root, entity):
        """
        Populates the entity object by traversing the element tree in a reccursive manner

        :param root: root of the element tree
        :param entity: Enitity object
        """
        print("Root -> ")
        print(root)
        print("Entity -> ")
        print(entity)
        if root is None:
            return

        qual_root = etree.QName(root)
        print("Qual Root -> ")
        print(qual_root)
        root_namespace = qual_root.namespace
        print("Root Namespace -> ")
        print(root_namespace)
        bundle_yang_ns = get_bundle_yang_ns(get_bundle_name(entity))
        print("Bundle Yang NS -> ")
        print(bundle_yang_ns)

        for child_node in root.getchildren():
            # separate element namespace and tag
            print("Child Node -> ")
            print(child_node)
            qual_node = etree.QName(child_node)
            print("Child Qual Node ->")
            print(qual_node)
            namespace, yname = qual_node.namespace, qual_node.localname
            print("namespace -> ")
            print(namespace)
            print("yname -> ")
            print(yname)

            if namespace != root_namespace:
                print("namespace -> ")
                print(namespace)
                print("root_namespace -> ")
                print(root_namespace)
                for name_space_prefix, name_space in bundle_yang_ns.NAMESPACE_LOOKUP.items():
                    if name_space == namespace:
                        yname = f"{name_space_prefix}:{yname}"
                        break
            
            print("CN Text -> ")
            print(child_node.text)
            entity.set_value(yname, child_node.text)
            print("entity -> ")
            print(entity)

            attr, child = entity.get_child_by_name(yname, "")
            print("attr -> ")
            print(attr)
            print("child -> ")
            print(child)
            if attr and child:
                if isinstance(getattr(entity, attr), YList):
                    XmlDecoder._decode_helper(child_node, child)
                    getattr(entity, attr).append(child)
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
