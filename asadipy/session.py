'''
Created on 2017. 1. 26.

@author: Hye-Churn Jang
'''

import json
from requests.auth import HTTPBasicAuth
from pygics import RestAPI
from .static import *

class Session(RestAPI):
    
    def __init__(self, ip, user, pwd, **kargs):
        RestAPI.__init__(self, ip, user, pwd, proto=RestAPI.PROTO_HTTPS, **kargs)
    
    def __login__(self, req):
        try: resp = req.post(self.url + '/api/tokenservices',
                             headers={'Content-Type' : 'application/json', 'Accept' : 'application/json', 'User-Agent' : 'asadipy' },
                             json={},
                             auth=HTTPBasicAuth(self.user, self.pwd),
                             verify=False)
        except: raise ExceptAsadipySession(self)
        if resp.status_code == 204:
            token = resp.headers['X-Auth-Token']
            if self.debug: print('ASA Session Connect to %s with %s' % (self.url, token))
            return token
        raise ExceptAsadipySession(self)
    
    def __refresh__(self, req):
        return self.__login__(self, req)
    
    def __header__(self): return {'Content-Type' : 'application/json', 'Accept' : 'application/json', 'User-Agent' : 'asadipy', 'X-Auth-Token' : self.token }
    
    def cli(self, *commands):
        resp = RestAPI.post(self, '/api/cli', json.dumps({'commands' : commands}))
        if resp.status_code == 200:
            try: data = resp.json()['response']
            except:
                try:
                    error = data['messages'][0]
                    raise ExceptAsadipyResponse(self, error['code'], error['details'])
                except: raise ExceptAsadipyResponse(self, resp.status_code, '/api/cli')
            ret = {}
            idx = 0
            for command in commands:
                try: cdata = data[idx].split('\n')
                except: cdata = []
                ret[command] = cdata
                idx += 1
            return ret
        elif resp.status_code == 401: self.refresh()
        else: raise ExceptAsadipyResponse(self, resp.status_code, '/api/cli')
            
    def get(self, url):
        ret = []
        offset = 0
        load = 0
        total = None
        while load != total:
            resp = RestAPI.get(self, url + ('?offset=%d' % offset))
            if resp.status_code == 200:
                data = resp.json()
                try: rinfo = data['rangeInfo']
                except:
                    try:
                        error = data['messages'][0]
                        raise ExceptAsadipyResponse(self, error['code'], error['details'])
                    except: raise ExceptAsadipyResponse(self, resp.status_code, url)
                total = rinfo['total']
                load += rinfo['limit']
                offset += 100
                ret = ret + data['items']
            elif resp.status_code == 401: self.refresh()
            else: raise ExceptAsadipyResponse(self, resp.status_code, url)
        return ret
