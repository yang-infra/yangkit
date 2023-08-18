import re
from yangkit.types import Entity
from yangkit.utilities.entity import get_internal_node, get_top_level_class, segmentalize


class JsonDecoder:
    """
    JSON Decoder class
    """

    @staticmethod
    def decode(path_val, model):
        """
        Decodes JSON payload and returns a child container
        with the same absolute path as the provided model.

        :param path_val: Tuple(path, JSONObject)
        :param model: Entity object; required to find the bundle name
        """
        path, val = path_val["path"], path_val["val"]
        top_entity = get_top_level_class(model)

        if path and val:
            entity = JsonDecoder._decode_path_to_entity(path, top_entity)
            JsonDecoder._decode_json(val, entity)
        else:
            entity = top_entity

        return get_internal_node(top_entity, model.get_absolute_path())

    @staticmethod
    def _decode_path_to_entity(path, top_entity):
        """
        Retuns an internal node from top_entity with absolute path same as "path"

        :param path: represents "path" in json payload
        :param top_entity: top-level entity object
        """
        segments = segmentalize(path)
        entity = top_entity
        for segment in segments[1:]:
            if '[' in segment:
                attr, child = entity.get_child_by_name(segment.split('[')[0], "")
                ylist = getattr(entity, attr)
                keys = re.findall(r'\[(.*?)\]', segment)
                for key in keys:
                    k, v = key.split("=")
                    child.set_value(k, v)
                ylist.append(child)
            else:
                _, child = entity.get_child_by_name(segment, segment)
            entity = child
        return entity

    @staticmethod
    def _decode_json(val_json, entity: Entity):
        """
        Populates the entity object by traversing the JSON object in a reccursive manner

        :param val_json: JSON object
        :param entity: Enitity object
        """
        for k, v in val_json.items():
            if type(v) == dict:
                _, child = entity.get_child_by_name(k, k)
                JsonDecoder._decode_json(v, child)
            elif type(v) == list:
                attr, child = entity.get_child_by_name(k, k)
                if attr and child:
                    # ylist
                    for ylist_item in v:
                        JsonDecoder._decode_json(ylist_item, child)
                        getattr(entity, attr).append(child)
                else:
                    # yleaf list
                    for yleaf_list_item in v:
                        entity.set_value(k, yleaf_list_item)
            else:
                if type(v) == bool:
                    v = "true" if v else "false"
                entity.set_value(k, v)

    @staticmethod
    def data_in_rpc_reply(response_json):
        """
        Returns data inside the gNMI response

        :param response_json: gNMI response 
        """
        if "notification" in response_json:
            return response_json["notification"][0]["update"][0]
        return response_json
