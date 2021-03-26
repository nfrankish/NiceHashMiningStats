from datetime import datetime
from time import mktime
import uuid
import hmac
import requests
import json
from hashlib import sha256
import optparse
import sys


class private_api:

    def __init__(self, host):
        self.host = host

    def request(self, method, path):

        url = self.host + path
        s = requests.Session()
        response = s.request(method, url)
        if response.status_code == 200:
            return response.json()
        elif response.content:
            raise Exception(str(response.status_code) + ": " + response.reason + ": " + str(response.content))
        else:
            raise Exception(str(response.status_code) + ": " + response.reason)



if __name__ == "__main__":
    private_api = private_api('http://192.168.5.201:18000')
    print(private_api.request('GET','/devices_cuda'))
