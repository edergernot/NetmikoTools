'''
Needet to find Port wher last STP-Toppology change was seen.
Works only if STP-Topology-Change was within last 24h
'''
from netmiko import Netmiko
from getpass import getpass
import ipaddress
import datetime, time
from colorama import Fore


seeddevice = input("IP-Adress of Seeddevice: ")
username = input ("Username to Connect to Network-Devices: ")
password = getpass("Password for user "+username+":")

device = {
    'device_type': 'cisco_ios',
    'host':seeddevice,
    'username': username,
    'password': password}

def isTimeFormat(input):
    try:
        time.strptime(input, '%H:%M:%S')
        return True
    except ValueError:
        return False


print ("Try to Connect to seeddevice :"+seeddevice+"\n")
try:
    while True:
        ssh = Netmiko(**device)
        hostname = ssh.find_prompt()[:-1]
        print (Fore.GREEN+"Connected to",hostname,Fore.RESET)
        spanningtree = ssh.send_command("show spanning-tree detail | include from|last")
        shortest = "23:59:59"
        my_lasttime = "23:59:58"
        my_lastfrom = ""
        neighbor_ip=""
        t_shortest = datetime.datetime.strptime( shortest, '%H:%M:%S').time()
        #print (spanningtree)
        for line in spanningtree.split("\n"):
            # print (line)
            if "last" in line:
                lasttime = line.split()[-2:-1][0]
                if not isTimeFormat(lasttime):
                    lasttime = "23:59:59"
                    # print ("Not in last 24 Hours")
                # print (lasttime)
                t_lasttime = datetime.datetime.strptime( lasttime, '%H:%M:%S').time()
            if "from" in line:
                lastfrom = line.split()[-1]
                # print (lastfrom)
                if t_lasttime < t_shortest:
                    t_lasttime = datetime.datetime.strptime( lasttime, '%H:%M:%S').time()
                    t_shortest = datetime.datetime.strptime( lasttime, '%H:%M:%S').time()
                    my_lastfrom = lastfrom
                    my_lasttime = lasttime
        print ("Shorest Spannigtree-Topology Change "+my_lasttime+" ago from "+my_lastfrom)
        print ("Try to find CDP-Neigbor on Interface "+my_lastfrom)
        port = my_lastfrom
        try:
            cdp_nei = ssh.send_command("show cdp neighbor detail",use_textfsm=True)
            if port[0:2]=="Po":
                sh_int=ssh.send_command("show int "+port)
                for line in sh_int.split("\n"):
                    if "Members in this" in line:
                        port = line.split()[-1]
                        print ("Spanningtee Change on Portchannel! One Member is ",port)
                if port[0:2]=="Fo":
                    port = port.replace("Fo", "FortyGigabitEthernet")
                if port[0:2]=="Te":
                    port = port.replace("Te", "TenGigabitEthernet")
                if port[0:2]=="Gi":
                    port = port.replace("Gi", "GigabitEthernet")
                if port[0:2]=="Fa":
                    port = port.replace("Fa", "FastEthernet")   
            for element in cdp_nei:
                if element["local_port"] == port:
                            neighbor_ip = element["management_ip"]
                            neighbor = element["destination_host"]
                            sw_version = element["software_version"]
                            if "(NX-OS)" in sw_version:
                                device_type  = "cisco_nxos"
                            if "IOS" in sw_version:
                                device_type = "cisco_ios"  
            if neighbor_ip =="":
                a=1/0
            New_Device = {"device_type":device_type,"host":neighbor_ip,'username': username, "password":password,  }
            device = New_Device 
        except Exception as e:
            # print (e)
            print ("\nNo CDP Neighbor on Switch ",hostname,)
            print ("-"*60)
            interface_cfg = ssh.send_command("show running interface "+port)
            print ("Configuration for Port "+port)
            print (interface_cfg)
            print ("-"*60)


            quit()
        ssh.cleanup()
        print ("Disconnected from Device")
        print ("Try to Connect to "+device["host"]+"\n")

except Exception as e:
    print (e) 
        
        

