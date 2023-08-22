from yangkit.models.cisco_ios_xr import Cisco_IOS_XR_um_interface_cfg

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

ifcfgs = Cisco_IOS_XR_um_interface_cfg.Interfaces()
interface_list = [
{"interface_name": "FourHundredGigE0/0/0/0", "address": "1.1.1.1", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/1", "address": "1.1.1.2", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/2", "address": "1.1.1.3", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/3", "address": "1.1.1.4", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/4", "address": "1.1.1.5", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/5", "address": "1.1.1.6", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/6", "address": "1.1.1.7", "netmask": "255.0.0.0"},
{"interface_name": "FourHundredGigE0/0/0/7", "address": "1.1.1.8", "netmask": "255.0.0.0"}]

for interface in interface_list:
    ifcfg = Cisco_IOS_XR_um_interface_cfg.Interfaces.Interface()
    ifcfg.interface_name = interface["interface_name"]
    ifcfg.ipv4.addresses.address = ifcfg.ipv4.addresses.Address()
    ifcfg.ipv4.addresses.address.address = interface["address"]
    ifcfg.ipv4.addresses.address.netmask = interface["netmask"]
    ifcfgs.interface.append(ifcfg)

request_payload = Codec.encode(entity=ifcfgs, encoding="XML", optype="create")
print(request_payload)
config_response = ncclient_manager.edit_config(target="candidate", config=request_payload)
print(config_response)
commit_response = ncclient_manager.commit()
print(commit_response)
