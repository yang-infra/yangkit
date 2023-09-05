from yangkit.models.cisco_ios_xr import openconfig_system
from yangkit.models.cisco_ios_xr import openconfig_system_logging
from yangkit.models.cisco_ios_xr import openconfig_lacp

from yangkit.codec import Codec

# PYGNMI is a separate package and needs to be installed via pip
import pygnmi.client

router_info = {
    "host": "172.26.228.76",
    "port": "63810",
    "username": "cafyauto",
    "password": "cisco123"
}

gnmiclient = pygnmi.client.gNMIclient(target=(router_info["host"], router_info["port"]), username=router_info["username"],
                                                   password=router_info["password"], insecure=True,
                                                   path_cert=None, override=None, debug=True)

gnmiclient.connect()

# Read NTP Config
ntp = openconfig_system.System.Ntp()
path = Codec.encode(entity=ntp, encoding="JSON", optype="read")
response_payload = gnmiclient.get(prefix="openconfig://", path=[path], target=None, encoding='json_ietf', datatype='all')
response_object = Codec.decode(payload=response_payload, model=ntp, encoding="JSON")
print(response_object)
print(response_object.config.enabled)
print(response_object.config.enable_ntp_auth)
