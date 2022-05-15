import multitor as mt
import requests
import subprocess
import sys

if __name__ == '__main__':
    
    if len(sys.argv) == 2:
        NCIRCUITS = int(sys.argv[1])
        NCLIENTS  = 5
    elif len(sys.argv) == 3:
        NCIRCUITS = int(sys.argv[1])
        NCLIENTS  = int(sys.argv[2])
    else:
        NCIRCUITS = 10
        NCLIENTS  = 5
        
    print("Launching " + str(NCIRCUITS) + " circuits with " + str(NCLIENTS) + " clients each.")
    
    tc = mt.create_multi_tor_env(9000,NCIRCUITS)

    for client in tc:
        for k in range(1,NCLIENTS):
            subprocess.call('start python function.py ' + str(client[0]), shell=True)

    