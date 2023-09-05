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

config_list = []

# Set NTP Config
ntp = openconfig_system.System.Ntp()
ntp.config.enabled = True
ntp.config.enable_ntp_auth = True
config_list.append(ntp)

# Set Syslog Config
remote_servers = openconfig_system.System.Logging.RemoteServers()
remote_server = remote_servers.RemoteServer()
remote_server.host = '192.168.1.112'
remote_server.config.host = '192.168.1.112'
remote_server.config.remote_port = 33033
remote_servers.remote_server.append(remote_server)
config_list.append(remote_servers)

# Set LACP Config
lacp_config = openconfig_lacp.Lacp.Config()
lacp_config.system_priority = int(100)
config_list.append(lacp_config)


path_val, delete_paths = Codec.encode(entity=config_list, encoding="JSON", optype="update")
response = gnmiclient.set(update=path_val, delete=delete_paths, replace=None, 
                                            prefix=None, target=None, encoding="json_ietf")
print(response)
