from yangkit.models.cisco_ios_xr import Cisco_IOS_XR_um_segment_routing_cfg
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


cfg = Cisco_IOS_XR_um_segment_routing_cfg.SegmentRouting.GlobalBlock()
cfg.lower_bound = int(20000)
cfg.upper_bound = int(21000)

request_payload = Codec.encode(entity=cfg, encoding="XML", optype="create")
print(request_payload)
config_response = ncclient_manager.edit_config(target="candidate", config=request_payload)
print(config_response)
commit_response = ncclient_manager.commit()
print(commit_response)
