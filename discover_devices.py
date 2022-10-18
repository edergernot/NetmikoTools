
# Virtualenvironment /venv
# source venv/bin/activate
# pip install netmiko
# pip install tcpping

'''Scans IP-Network for host listening in Port 22(SSH) and 23(Telnet).
Tryes to logon with credentials and create a hostsfile for using in send_commands 
and send_configs and networkstatedump.'''




from tcpping import tcpping 
from netmiko import ConnectHandler
import ipaddress
from time import time
import getpass
from multiprocessing.dummy import Pool as ThreadPool

def check_ip_network(ip_net):
    try:
        ipaddress.IPv4Network(ip_net)
        return (True)
    except:
        return (False)


def worker_ssh_test(IP):
    if tcpping(str(IP),22,4):
        reachable.append(str(IP))
    if tcpping(str(IP),23,4):
        reachable_telnet.append(str(IP))


def worker_get_devicesinfo(IP):
    hostip=IP
    try :
#        device = {device_type': 'autodetect',
#...              'host': IP, 
#                 'username': user,
#                 'password': pwd}
        ssh_session = ConnectHandler(device_type="cisco_ios", ip=hostip, username=user, password=pwd)
        sh_ver = ssh_session.send_command("show version")
        hostname = ssh_session.find_prompt()
        if "LINUXL2" in sh_ver:
            hosttype = "Switch"
        elif "linux-l3" in sh_ver:
            hosttype = "Router"
        elif " IOS XE " in sh_ver:
            hosttype = "ios-xe"
        elif " IOS " in sh_ver:
            hosttype = "cisco_ios"
        elif "NX-OS" in sh_ver:
            hosttype = "cisco_nxos_ssh"
        else:
            hosttype = "other"
        my_inventory.append({"hostname":hostname, "ip":IP, "hosttype":hosttype, "connect":"ssh"})
        ssh_session.disconnect()
        return (None)
    except Exception as e:
        print ( hostip, " Failed: ", e)  
        return (None)


def worker_get_devicesinfo_telnet(IP):
    hostip=IP
    try :
        ssh_session = ConnectHandler(device_type="cisco_ios_telnet", ip=hostip, username=user, password=pwd)
        sh_ver = ssh_session.send_command("show version")
        hostname = ssh_session.find_prompt()
        if "LINUXL2" in sh_ver:
            hosttype = "Switch"
        elif "linux-l3" in sh_ver:
            hosttype = "Router"
        elif " IOS XE " in sh_ver:
            hosttype = "ios-xe"
        elif " IOS " in sh_ver:
            hosttype = "ios"
        elif "NX-OS" in sh_ver:
            hosttype = "nx-os"
        else:
            hosttype = "Other"
        ssh_session.disconnect()
        return (None)
    except Exception as e:
        print ( hostip, " Failed: ", e)  
        return (None)


#==============================================================================
# ---- Main: Create Inventory
#==============================================================================

# Initialize Gobal Vars
reachable=[]  #List of Hosts which answer TCP/SYN on Port 22
reachable_telnet=[]  #List of Hosts which answer TCP/SYN on Port 23
ip_net="300.300.300.300/22"

my_inventory=[]
user = ""
pwd = ""
run = True

while run:

    while not check_ip_network(ip_net):
        ip_net = input("Enter Discovery Network, like 192.168.1.0/24 : ")
    if user == "":
        user = input("Login Credentials for Device Login! \nEnter Username : ")
    if pwd == "":
        pwd = getpass.getpass("Enter Password : ")
    
    num_threads = 75
    hosts = []
    print ("-"*40)
    hosts = list(ipaddress.IPv4Network(ip_net).hosts())
   

    #----
    #---- Try TCP-SYN on Ip Network
    #---- 

    starttime=time()
    starttime1=time()

    print ('\n--- Creating threadpool with ',num_threads,' threads: Try TCP-SYN on Port 22 and on Port 23---\n')
    threads = ThreadPool( num_threads )
    results = threads.map( worker_ssh_test, hosts )

    threads.close()
    threads.join()

    print("--- Finished TCP-SYN on ",len(hosts)," Hosts in ",time()-starttime,"\n")
    print(f"--- Detected {len(reachable)} Hosts with open SSH: TCP-Port 22\n")
    print(f"--- Detected {len(reachable_telnet)} Hosts with open TELNET: TCP-Port 23\n")
    print("-"*40)
    # debug only print ("Reachable Hosts: ",reachable)

    #--------------------
    #---- Get Host Infos 
    #--------------------

    if len(reachable) != 0:
        num_threads = 50
        if num_threads >= len(reachable):
            num_threads = len(reachable)

        starttime=time()

        #SSH connect!
        print ('\n--- Creating threadpool with ',num_threads,' threads: Try get Hostinfos  on  ',len(reachable),' Hosts ---\n\n')
        threads = ThreadPool( num_threads )
        results = threads.map( worker_get_devicesinfo, reachable )

        threads.close()
        threads.join()

        print ("\n---Finished get Hostinfos  in ",time()-starttime)," ---\n"
        print ("-"*40)

    # check if device is reachable via ssh and telnet, remove from telnet list
    for item in reachable:
        if item in reachable_telnet:
            reachable_telnet.remove(item)

    if len(reachable_telnet) != 0:
        #Telnet connect!
        starttime=time()
        print ('\n--- Creating threadpool with ',num_threads,' threads: Try get Hostinfos via Telnet  on  ',len(reachable_telnet),' Hosts ---\n\n')
        threads = ThreadPool( num_threads )
        results = threads.map( worker_get_devicesinfo_telnet, reachable_telnet )

        threads.close()
        threads.join()

        print ("\n---Finished get Hostinfos  in ",time()-starttime)," ---\n"
        print ("-"*40)

    reachable = []
    reachable_telnet = []



    #----------------------------
    #----  Writing Inventory File 
    #----------------------------

    print ("\n--- writing Inventory File ---")
    with open("hosts.txt",mode="w") as myfile:
        # myfile.write("---\n")
        for device in my_inventory:
            hostname = device.get("hostname")[:-1]
            dev_ip = device.get("ip")
            dev_os = device.get("hosttype")
            dev_connect = device.get("connect")
            myfile.write(f"{dev_ip},{hostname},{dev_os},{dev_connect}\n")



    print (f"\n---- Finished creating hosts.txt with {len(my_inventory)} devices for use with Python-Scripts in {starttime1-time():.2f} seconds ----\n")
    print ("-"*40)

    oncemore = input("Do you want to scan one more IP-Range (y/n)?:")
    if oncemore.lower() != "y":
        run = False
    else:
        ip_net="300.300.300.300/22"

write_environment = input(f"Write environment file (y/n)?: ")
if write_environment.lower() == "y":
    with open("environment.py","w") as file:
        file.write(f"filename = 'hosts.txt'\nusername = '{user}'\npassword = '{pwd}'")
    print("environment file written")
else:
    print("No file written")

        