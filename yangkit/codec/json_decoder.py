import json
from yangkit.types import YList
from yangkit.utilities.logger import log
from yangkit.types import Entity
from yangkit.utilities.entity import get_internal_node, get_top_level_class, get_bundle_name, get_bundle_yang_ns, find_prefix_in_namespace_lookup
from yangkit.errors import YCodecError

class JsonDecoder:

    @staticmethod
    def decode(paths, model):
        # top_entity = get_top_level_class(model)
        # entity = get_internal_node(top_entity, model.get_absolute_path)
        for path_val in paths:
            path = path_val["path"]
            val = path_val["val"]
            JsonDecoder._decode_json(val, model)

        return model

    @staticmethod
    def _decode_json(val_json, entity: Entity):
        for k, v in val_json.items():
            if type(v) == dict:
                _, child = entity.get_child_by_name(k, k)
                JsonDecoder._decode_json(v, child)
            elif type(v) == list:
                attr, child = entity.get_child_by_name(k, k)
                for y_item in v:
                    JsonDecoder._decode_json(y_item, child)
                    getattr(entity, attr).append(child)
            else:
                entity.set_value(k, v)

    @staticmethod
    def data_in_rpc_reply(response_json_str):
        response_json = json.loads(response_json_str)
        paths = response_json["notification"][0]["update"]
        return paths
