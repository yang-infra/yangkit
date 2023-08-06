from yangkit.models.cisco_ios_xr import Cisco_IOS_XR_segment_routing_ms_cfg
from yangkit.codec import Codec

# NCClient is a separate package and needs to be installed via pip
from ncclient import manager

router_info = {
    "host": "172.26.228.76",
    "port": "61680",
    "username": "cisco",
    "password": "cisco123"
}

ncclient_manager = manager.connect(host=router_info["host"],
                                   port=router_info["port"],
                                   username=router_info["username"],
                                   password=router_info["password"],
                                   hostkey_verify=False,
                                   look_for_keys=False,
                                   allow_agent=False)


sr_cfg = Cisco_IOS_XR_segment_routing_ms_cfg.Sr()
request_payload = Codec.encode(entity=sr_cfg, encoding="XML", optype="read")
print(request_payload)
response_payload = ncclient_manager.get_config(source="running",
                                               filter=("subtree", request_payload))
response_payload = response_payload.data_xml
print(response_payload)
sr_config = Codec.decode(payload=response_payload, model=sr_cfg,
                         encoding="XML")
print(sr_config.global_block.lower_bound)
print(sr_config.global_block.upper_bound)
