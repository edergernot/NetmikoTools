''' sends a list of commands to a list of devices an writes the output do a file per device.
uses environment.py or asks user for hostfile and login credentials
For Configure use any the Option  "config"'''


import argparse
from netmiko import ConnectHandler
import getpass
import os
from multiprocessing.dummy import Pool as ThreadPool
from time import time
from environment import *  #Use environment Files for Username, Password and File. No manual User Login
import sys

config_mode = False
# Commands that will configured when startet with 'config'
CONFIGS=["no username ojaeckel privilege 15 secret 9 $9$h2xinXv9OUpLoE$FprJVF4Gnibsn.8H/6ZIL/MCStivEjDnNNLEZNIWXmM",
        ]
# Commands that will executed 
COMMANDS = ["sh run | i usern",
            ]

OUTPUT_DIR = "./output"
DF = 15 # netmiko delay factor 


def create_list_from_file(filename):
    linelist = []
    try:
        with open(filename,"r") as file:
            filecontent=file.read()
            lines = filecontent.split("\n")
            for line in lines:
                splitline = line.split(",")
                if len(splitline) != 4:
                    print("wrong entrys in hostfile")
                    continue
                ip_addr = splitline[0]
                device_type = splitline[2]
                prot = splitline[3]
                if prot == "telnet":
                    device_type = "cisco_ios_telnet"
                if device_type == "ios-xe":
                    device_type = "cisco_ios"
                device = {"device_type":device_type, "ip":ip_addr, "username":username, "password":password}
                linelist.append(device)
        return (linelist)
    except Exception as e:
        print(f"*** Error in Hostfile Parsing ***:\n{e}")
        return (linelist)



def worker(device):
    try:    
        ssh_session = ConnectHandler(**device)
        hostfilename = str(ssh_session.find_prompt())[:-1]+"_command.txt"
        if not os.path.isdir(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        with open (f"{OUTPUT_DIR}/{hostfilename}","w") as outputfile:
            outputfile.write(f"{COMMANDS}\n")
            outputfile.write("\n")
            outputfile.write("*"*40)
            outputfile.write("\n")
            for command in COMMANDS:
                outputfile.write(command)
                outputfile.write("\n")
                outputfile.write("-"*40)
                outputfile.write("\n")
                commandoutput = ssh_session.send_command(command, delay_factor=DF)
                outputfile.write(commandoutput) 
                outputfile.write("\n")
                outputfile.write("*"*40)
                outputfile.write("\n")
        return(True)
    except Exception as e:
        IP = device["ip"]
        print(f"Error on Device :{IP}: {e}")
        return(None)



def worker_config(device):
    try:    
        ssh_session = ConnectHandler(**device)
        hostfilename = str(ssh_session.find_prompt())[:-1]+"_config.txt"
        if not os.path.isdir(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        with open (f"{OUTPUT_DIR}/{hostfilename}","w") as outputfile:
            outputfile.write(f"{CONFIGS}\n")
            outputfile.write("\n")
            outputfile.write("*"*40)
            outputfile.write("\n")
            for command in CONFIGS:
                outputfile.write(command)
                outputfile.write("\n")
                outputfile.write("-"*40)
                outputfile.write("\n")
                commandoutput = ssh_session.send_config_set(command, delay_factor=DF) # Use  cmd_verify=False if you need to confirm (for example delete user)
                outputfile.write(commandoutput) 
                outputfile.write("\n")
                outputfile.write("*"*40)
                outputfile.write("\n")
        return(True)
    except Exception as e:
        IP = device["ip"]
        print(f"Error on Device :{IP}: {e}")
        return(None)

# === Main Program ===#



devicelist = []
if filename == "":
    filename = input("IP-Host-File : ")
if username == "":
    username = input ("Username to connect to devices : ")
if password == "":
    password = getpass.getpass("Password : ")

if len(sys.argv) >= 2:
    if sys.argv[1]=="config":
        print ("Config-Mode")
        config_mode = True

devicelist = create_list_from_file(filename)


# ==== Create Treats and do SSH_Worker ==== #

if len(devicelist) <= 50 :
    num_threads=len(devicelist)
else:
    num_threads=50

#num_threads=1  # only one thread
threads = ThreadPool( num_threads )
if config_mode == True:
    results = threads.map( worker_config, devicelist )
else:
    results = threads.map( worker, devicelist )

threads.close()
threads.join()