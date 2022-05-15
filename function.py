import multitor as mt
import requests
import sys

def get_request(p):
    port = p
    proxies = {
            'http': 'socks5://127.0.0.1:' + str(port),
            'https': 'socks5://127.0.0.1:' + str(port)
        }
    while True:
        x = requests.get('https://ifconfig.me/', proxies=proxies)
        print(x.status_code,x.text)
        if x.status_code != 200:
            mt.change_tor_circuit(port)

if __name__ == '__main__':

    print(sys.argv[1])
    get_request(sys.argv[1])
