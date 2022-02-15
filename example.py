import multitor as mt
import multiprocessing as mp
import requests


def get_request(p):
    port = p[0]
    proxies = {
            'http': 'socks5://127.0.0.1:'+str(port),
            'https': 'socks5://127.0.0.1:' + str(port)
        }
    while True:
        x = requests.get('https://ifconfig.me/', proxies=proxies)
        print(x.status_code,x.text)
        if x.status_code != 200:
            mt.change_tor_circuit(port)

if __name__ == '__main__':

    NCIRCUITS = 10
    tc = mt.create_multi_tor_env(9000,NCIRCUITS)
    pool = mp.Pool(NCIRCUITS)
    results = pool.map(get_request, [p for p in tc])  
    pool.close()  
    mt.clean_tor_relays()