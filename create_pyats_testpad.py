from environment import *

# Read Data from Hostfile
filename = "hosts.txt"
with open(filename) as f:
    devices = f.read()

# Create testbed File with data from environment and hostfile created during 'createinventory.py'    
with open("testbed.yaml","w") as f:
    f.write("---\n\n") # Needet to be yaml file
    f.write("devices:\n")
    for device in devices.split("\n"):
        if device == '':
            continue
        hostname = device.split(",")[1]
        alias = hostname
        ip = device.split(",")[0]
        protocol = device.split(",")[3]
        os = device.split(",")[2]
        if os == "cisco_ios":
            os = "ios"
        if os == "ios-xe":
            os = "iosxe"
        if os == "cisco_nxos_ssh":
            os = "nxos"
        if protocol == "ssh":
            port = 22
        if protocol == "telnet":
            port = 23
        f.write(f"  {hostname}:\n")
        f.write(f"      os: '{os}'\n      type: '{os}'\n")
        f.write(f"      alias: '{alias}'\n")
        f.write(f"      connections:\n")
        f.write(f"        cli:\n          ip: '{ip}'\n")
        f.write(f"          protocol: '{protocol}'\n")
        f.write(f"          port: '{port}'\n")
        f.write(f"      credentials:\n        default:\n")
        f.write(f"          password: {password}\n")
        f.write(f"          username: {username}\n")
        

