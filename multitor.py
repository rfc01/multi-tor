import os
import requests
import subprocess
import argparse
import glob
import shutil
import json
from stem import Signal
from stem.control import Controller

PORT_OFFSET = 100
DEFAULT_PORT = 9050
TOR_PATH = '"Tor/tor.exe"'

def create_tor_env(port):
    path = str(os.getcwd())
    #create tor data sirectory
    try:
        os.mkdir(path + "/datadir")
        os.mkdir(path + "/torrc")
        os.mkdir(path + "/datadir/datadir" + str(port))
    except:
        pass
    
    #create torrc files
    filename = "torrc/torrc." + str(port)
    f = open(filename, "w+")
    f.write("SocksPort " + str(port) + "\n\r")
    f.write("ControlPort " + str(port + PORT_OFFSET) + "\n\r")
    f.write("DataDirectory ./datadir/datadir" + str(port) + "\n\r")
    f.write("HashedControlPassword 16:DF014777120B2073605D1E97A89CB003322CCD098A6A42876BA3A919D3")

    f.close()

def launch_tor(port):
    path = str(os.getcwd())
    cmd = TOR_PATH + ' -f ' + path + '/torrc/torrc.' + str(port) + ' | more'
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    return sp

def validate_tor_relay(port):
    proxies = {
        'http': 'socks5://127.0.0.1:'+str(port),
        'https': 'socks5://127.0.0.1:' + str(port)
    }
    while True:
        try:
            exit_ip = requests.get('https://ipinfo.io/', proxies=proxies).json()
            print('Launched Tor on 127.0.0.1:'+str(port),'<->', 'exit node:',exit_ip['ip'],'\t',exit_ip['country'],'-',exit_ip['region'])
            break
        except:
            pass
    return exit_ip

def clean_tor_relays():

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
    filePath = 'torcircuit.list'
    try:
        print("Removing " + filePath)
        os.remove(filePath)
    except:
        print("Error while deleting file : ", filePath)


def change_tor_circuit(port):
    with Controller.from_port(address = '127.0.0.1', port=port+PORT_OFFSET) as controller:
        controller.authenticate(password='password')
        controller.signal(Signal.NEWNYM)

def create_multi_tor_env(ports,ninst):
    print("Create DataDirectory and torrc files... ", end = '', flush=True)    
    for port in range(ports,ports+ninst):
        create_tor_env(port)
    print("Done")
    
    # launch all tor relay circuits
    print("Launching Tor nodes, this may take a few seconds. ")
    for port in range(ports,ports+ninst):    
        launch_tor(port)
        
    # Check and validate IPs and location for all tor circuits
    ret = []
    for port in range(ports,ports+ninst):    
        ret.append([port,validate_tor_relay(port)['ip']])
    
    return ret
  
def create_circuit_list(ports,ninst):
    # Create tor relay list
    filename = "torcircuit.list"
    f = open(filename, "w+")
    for port in range(args.ports,args.ports+args.ninst):
        f.write(str(port)+'\n')
    f.close()
    print("Access port list created:", filename)

if __name__ == '__main__':

    # Defines and Global Variables
    parser = argparse.ArgumentParser(description='Tor Relay Launcher')
    parser.add_argument('-c', '--clean', help='clean tor workspace', dest='clean', action='store_true', required=False)
    parser.add_argument('-n', '--ninst', type=int, help='number of Tor instances', required=False)
    parser.add_argument('-p', '--ports', type=int, help='initial port', required=False)
    parser.add_argument('-l', '--port_list', help='create ip:port access list', dest='port_list', action='store_true', required=False)
    parser.add_argument('-m', '--modify', help='modify IPs in current environment', dest='modify', action='store_true', required=False)

    parser.set_defaults(clean=False, ninst=0, ports=DEFAULT_PORT, port_list=False, modify=False)

    # Parse command-line arguments
    args = parser.parse_args()

    # Remove old workspace
    if args.clean:
        clean_tor_relays()
        
    if args.ninst > 0:
        create_multi_tor_env(args.ports,args.ninst)   
        if args.port_list:
            create_circuit_list(args.ports,args.ninst)
        
    if args.modify: 
        # Create tor relay list
        filename = "torcircuit.list"
        f = open(filename, "r")
        lines = f.readlines()
     
        # Strips the newline character
        ports = []
        for l in lines:
            ports.append(int(l))
        
        # Check and validate IPs and location for all tor circuits
        for port in ports:    
            change_tor_circuit(port)
            
        # Check and validate IPs and location for all tor circuits
        for port in ports:    
            validate_tor_relay(port)   