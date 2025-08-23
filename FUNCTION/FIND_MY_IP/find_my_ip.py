import requests

def find_my_ip():
    ip_address = requests.get('https://api.ipify.org?format=json').json()
    return ip_address['ip']
