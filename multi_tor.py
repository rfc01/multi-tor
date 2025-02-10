import os
import subprocess
import time
import socket
import requests
from stem import Signal
from stem import CircStatus
from stem.control import Controller

BS = '\033[1m'
BF = '\033[0m'
BE = '\033[1m\033[91m'

# Configuration
BASE_DATA_DIR = "./tor_data"  # Base directory for Tor data
TOR_BINARY = "tor"  # Path to the Tor executable
NUM_NODES = 20  # Number of parallel Tor nodes to create
START_SOCKS_PORT = 9050  # Base SOCKS port
START_CONTROL_PORT = 9051  # Base control port
TOR_PASSWORD = "mypassword"  # Password for Tor control ports

def generate_torrc(data_dir, socks_port, control_port, hashed_password):
    """Generates a Tor configuration file for a single node."""
    torrc_content = f"""
SocksPort {socks_port}
ControlPort {control_port}
DataDirectory {data_dir}
HashedControlPassword {hashed_password}
Log notice stdout
"""
    torrc_path = os.path.join(data_dir, "torrc")
    with open(torrc_path, "w") as f:
        f.write(torrc_content)
    return torrc_path

def start_tor_instance(data_dir, torrc_path):
    """Starts a Tor process using the specified configuration."""
    print(f"Starting Tor instance in {data_dir}...")
    try:
        subprocess.Popen(
            [TOR_BINARY, "-f", torrc_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(f"Error starting Tor instance: {e}")

def is_port_open(port):
    """Check if a port is open."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def create_hashed_password(password):
    """Creates a hashed password for Tor control port."""
    try:
        hashed = subprocess.check_output([TOR_BINARY, "--hash-password", password])
        return hashed.decode("utf-8").strip()
    except Exception as e:
        print(f"Failed to hash password: {e}")
        return None

def signal_newnym(control_port, password):
    """Sends a NEWNYM signal to a Tor control port to request a new circuit."""
    if not is_port_open(control_port):
        print(f"Control port {BE}{control_port}{BF} is not open yet. Skipping.")
        return

    try:
        with Controller.from_port(port=control_port) as controller:
            controller.authenticate(password=password)
            controller.signal(Signal.NEWNYM)

            for circ in controller.get_circuits():
                if circ.status != CircStatus.BUILT:
                    continue

                exit_fp, exit_nickname = circ.path[-1]

                exit_desc = controller.get_network_status(exit_fp, None)
                exit_address = exit_desc.address if exit_desc else 'unknown'

            print(f"New circuit on Control Port {BS}{control_port}{BF} with exit node {BS}{exit_address}{BF}")
    except Exception as e:
        print(f"Failed to signal NEWNYM on port {BE}{control_port}{BF}: {e}")

def check_country(socks_port):
    """Checks the country of the current Tor exit node using a SOCKS proxy."""
    try:
        proxies = {
            "http": f"socks5h://127.0.0.1:{socks_port}",
            "https": f"socks5h://127.0.0.1:{socks_port}",
        }
        response = requests.get("https://ipinfo.io", proxies=proxies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            country = data.get("country", "Unknown")
            print(f"Socks Port {socks_port} - Exit Node Country: {country}")
            return country
        else:
            print(f"Failed to get country for SOCKS port {socks_port}")
            return None
    except requests.RequestException as e:
        print(f"Error checking country for SOCKS port {socks_port}: {e}")
        return None

def main():
    print("Starting multiple Tor nodes...\n")

    hashed_password = create_hashed_password(TOR_PASSWORD)
    if not hashed_password:
        print("Failed to generate hashed password. Exiting.")
        return

    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    tor_processes = []

    for i in range(NUM_NODES):
        socks_port = START_SOCKS_PORT + (i*2)
        control_port = START_CONTROL_PORT + (i*2)
        data_dir = os.path.join(BASE_DATA_DIR, f"node_{i}")

        # Create a data directory for each node
        os.makedirs(data_dir, exist_ok=True)

        # Generate torrc file
        torrc_path = generate_torrc(data_dir, socks_port, control_port, hashed_password)

        # Start Tor instance
        start_tor_instance(data_dir, torrc_path)
        tor_processes.append((socks_port, control_port))

    # Allow time for the instance to start
    time.sleep(5)

    print("\nAll Tor nodes started successfully!")
    print("Node SOCKS and Control Ports:")
    for socks_port, control_port in tor_processes:
        print(f"- SOCKS Port: {socks_port}, Control Port: {control_port}")

    print("\nTesting circuit renewal on all nodes...")
    for _, control_port in tor_processes:
        signal_newnym(control_port, TOR_PASSWORD)

    #print("Node Country:")
    #for socks_port, control_port in tor_processes:
    #    check_country(socks_port)

    while(True):
        cmd = input("\nOptions: c - country, x - close \nPress to change IPs: ")
        
        if(cmd == 'c'):
            for socks_port, control_port in tor_processes:
                check_country(socks_port)
        elif(cmd == 'x'):
            subprocess.Popen(['pkill', '^' + TOR_BINARY])
            return
        else:    
            print("\nRenew on all nodes...")
            for socks_port, control_port in tor_processes:
                signal_newnym(control_port, TOR_PASSWORD)
        

    print("\nScript completed. Tor nodes are running.")

if __name__ == "__main__":
    main()
