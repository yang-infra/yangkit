from yangkit.utilities.logger import log
from yangkit.types import Entity, YList
from yangkit.errors import YInvalidArgumentError, YCodecError
from .xml_encoder import XmlEncoder
from .xml_decoder import XmlDecoder
from .json_encoder import JsonEncoder
from .json_decoder import JsonDecoder


class Codec(object):
    """
    CodecService wrapper.
    """

    SUPPORTED_ENCODING_FORMATS = ["XML", "JSON"]
    SUPPORTED_OPERATION_TYPES = ["create", "read", "update", "delete", "action"]

    @staticmethod
    def encode(entity, encoding, optype):
        """
        Encode entity or entities to string payload(s).
        :param entity: yangkit.types.Entity or list(yangkit.types.Entity)
        :param encoding: represents EncodingFormat (XML or JSON)
        :param optype: "create", "read", "update" or "delete"

        Returns:
            Payload in XML or JSON format.
            The type of return corresponds to the type of the 'entity'.
        """

        if encoding not in Codec.SUPPORTED_ENCODING_FORMATS:
            error_msg = f"""Invalid 'encoding' format. Supported formats: {Codec.SUPPORTED_ENCODING_FORMATS}."""
            log.error(error_msg)
            raise YCodecError(error_msg)

        if optype not in Codec.SUPPORTED_OPERATION_TYPES:
            error_msg = f"""Invalid 'operation' type. Supported types: {Codec.SUPPORTED_OPERATION_TYPES}."""
            log.error(error_msg)
            raise YCodecError(error_msg)

        if encoding == "XML":
            encoder = XmlEncoder
        elif encoding == "JSON":
            encoder = JsonEncoder

        if isinstance(entity, list):
            ret_encoded_str = ""
            for _entity in entity:
                ret_encoded_str += encoder.encode(_entity, optype)

        elif isinstance(entity, (Entity, YList)):
            ret_encoded_str = encoder.encode(entity, optype)

        else:
            error_msg = """Invalid 'entity' type. Expected types: yangkit.types.Entity; yangkit.types.YList; list(yangkit.types.Entity)."""
            log.error(error_msg)
            raise YInvalidArgumentError(error_msg)

        if Codec._is_edit_optype(optype):
            ret_encoded_str = encoder.prepend_config(ret_encoded_str)

        return encoder.get_pretty(ret_encoded_str)

    @staticmethod
    def decode(payload, model, encoding, is_action_response=False):
        """
        Decode payload in XML or JSON format to yangkit.types.Entity

        :param payload: payload in XML or JSON format.
        :param model: An instance of yangkit.types.Entity representing the type of decoded object
        :param encoding: represents EncodingFormat (XML or JSON)
        :param is_action_response: True, if payload is action operation response; False otherwise
        Returns: An instance of yangkit.types.Entity class.
        """

        if encoding not in Codec.SUPPORTED_ENCODING_FORMATS:
            error_msg = f"""Invalid 'encoding' format. Supported formats: {Codec.SUPPORTED_ENCODING_FORMATS}."""
            log.error(error_msg)
            raise YCodecError(error_msg)

        if not payload:
            log.error(f"payload is empty")
            raise YInvalidArgumentError(f"payload is empty")

        if encoding == "XML":
            decoder = XmlDecoder
        elif encoding == "JSON":
            decoder = JsonDecoder

        payload = decoder.data_in_rpc_reply(payload)

        if is_action_response:
            return decoder.decode_action_response(payload, model)

        return decoder.decode(payload, model)

    @staticmethod
    def _is_edit_optype(optype):
        """
        Checks whether the operation is edit-config or not

        :param optype: operation type
        """
        if optype == 'create' or optype == 'update' or optype == 'delete':
            return True
        return False
