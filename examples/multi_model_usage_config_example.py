from yangkit.models.cisco_ios_xr import Cisco_IOS_XR_um_segment_routing_cfg
from yangkit.models.cisco_ios_xr import Cisco_IOS_XR_um_interface_cfg
from yangkit.models.cisco_ios_xr import Cisco_IOS_XR_um_grpc_cfg

from yangkit.codec import Codec

# NCClient is a separate package and needs to be installed via pip
from ncclient import manager

router_info = {
    "host": "172.29.94.52",
    "port": "61052",
    "username": "cafyauto",
    "password": "cisco123"
}

ncclient_manager = manager.connect(host=router_info["host"],
                                   port=router_info["port"],
                                   username=router_info["username"],
                                   password=router_info["password"],
                                   hostkey_verify=False,
                                   look_for_keys=False,
                                   allow_agent=False)
config_list = []

# Set Interface Config
interface = {"interface_name": "FourHundredGigE0/0/0/0", "address": "1.1.1.1", "netmask": "255.0.0.0"}
ifcfg = Cisco_IOS_XR_um_interface_cfg.Interfaces.Interface()
ifcfg.interface_name = interface["interface_name"]
ifcfg.ipv4.addresses.address = ifcfg.ipv4.addresses.Address()
ifcfg.ipv4.addresses.address.address = interface["address"]
ifcfg.ipv4.addresses.address.netmask = interface["netmask"]
config_list.append(ifcfg)

# Set Segment Routing Config
srcfg = Cisco_IOS_XR_um_segment_routing_cfg.SegmentRouting.GlobalBlock()
srcfg.lower_bound = int(20000)
srcfg.upper_bound = int(21000)
config_list.append(srcfg)

# Set GRPC Config
grpccfg = Cisco_IOS_XR_um_grpc_cfg.Grpc()
grpccfg.port = int(57400)
config_list.append(grpccfg)

request_payload = Codec.encode(entity=config_list, encoding="XML", optype="create")
print(request_payload)
config_response = ncclient_manager.edit_config(target="candidate", config=request_payload)
print(config_response)
commit_response = ncclient_manager.commit()
print(commit_response)
