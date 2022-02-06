import os
import requests
import subprocess
import _thread
import argparse
import glob
import shutil
import json


DEFAULT_PORT = 9050
TOR_PATH = '"Tor/tor.exe"'

# Defines and Global Variables
parser = argparse.ArgumentParser(description='Tor Relay Launcher')
parser.add_argument('-c', '--clean', help='clean tor workspace', dest='clean', action='store_true', required=False)
parser.add_argument('-n', '--ninst', type=int, help='number of Tor instances', required=False)
parser.add_argument('-p', '--ports', type=int, help='initial port', required=False)

parser.set_defaults(clean=False, ninst=0, ports=DEFAULT_PORT)

# Parse command-line arguments
args = parser.parse_args()

# Remove old workspace
if args.clean:

    # Kill running tor processes
    os.system("taskkill /f /im  tor.exe")
    
    print("Clean old workspace")
    
    # Remove DataDirectory
    filePath = 'datadir'
    try:
        print("Removing " + filePath)
        shutil.rmtree(filePath)
    except:
        print("Error while deleting file : ", filePath)
    
    # Remove torrc files
    filePath = 'torrc'
    try:
        print("Removing " + filePath)
        shutil.rmtree(filePath)
    except:
        print("Error while deleting file : ", filePath)
        
    # Remove tor relay list
    filePath = 'torrelay.list'
    try:
        print("Removing " + filePath)
        os.remove(filePath)
    except:
        print("Error while deleting file : ", filePath)
    


if args.ninst == 0:
    exit(1)



print("Create DataDirectory")
print("Creating torrc files")
for port in range(args.ports,args.ports+args.ninst):

    path = str(os.getcwd())
    try:
        os.mkdir(path + "/datadir")
        os.mkdir(path + "/torrc")
        os.mkdir(path + "/datadir/datadir" + str(port))
    except:
        pass
    
    #create torrc files
    
    filename = "torrc/torrc." + str(port)
    f = open(filename, "w")
    f.write("SocksPort " + str(port) + "\n\r")
    f.write("ControlPort " + str(port + 100) + "\n\r")
    f.write("DataDirectory ./datadir/datadir" + str(port))
    f.close()
    
print("Launching Tor nodes...")

for port in range(args.ports,args.ports+args.ninst):    

    cmd = TOR_PATH + ' -f ' + path + '/torrc/torrc.' + str(port) + ' | more'
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)


for port in range(args.ports,args.ports+args.ninst):    
    proxies = {
        'http': 'socks5://127.0.0.1:'+str(port),
        'https': 'socks5://127.0.0.1:' + str(port)
    }
    while True:
        try:
            exit_ip = requests.get('https://ipinfo.io/', proxies=proxies).json()
            print('Launched Tor on 127.0.0.1:'+str(port),'|', 'exit node:',exit_ip['ip'],'\t',exit_ip['region'],'-',exit_ip['country'])
            break
        except:
            pass


# Create tor relay list
filename = "torrelay.list"
f = open(filename, "w")
for port in range(args.ports,args.ports+args.ninst):
    f.write(str(port))
f.close()