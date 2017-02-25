'''
Created on 2017. 1. 26.

@author: Hye-Churn Jang
'''

import json
import time
import requests
from requests.auth import HTTPBasicAuth

from .static import *

class Session:
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, retry=3, debug=False, week=False):
        try: requests.packages.urllib3.disable_warnings()
        except: pass
        
        self.ip = ip
        self.user = user
        self.pwd = pwd
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.debug = debug
        self.week = week
        self.url = 'https://%s' % ip
        self.session = None
        self.token = None
        
        self.login()
    
    def login(self):
        if self.session != None: self.session.close()
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy' }
        try:
            self.session = requests.Session()
            self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=self.conns, pool_maxsize=self.conn_max))
            for i in range(0, self.retry):
                resp = self.session.post(self.url + '/api/tokenservices',
                                         headers=headers,
                                         data=json.dumps({}),
                                         auth=HTTPBasicAuth(self.user, self.pwd),
                                         verify=False)
                if resp.status_code == 204:
                    self.token = resp.headers['X-Auth-Token']
                    if self.debug: print('Session %s with %s' % (self.url, self.token))
                    return
            raise AsadipySessionError()
        except Exception as e: print str(e); raise AsadipySessionError()
    
    def refresh(self):
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy' }
        try:
            for i in range(0, self.retry):
                resp = self.session.post(self.url + '/api/tokenservices',
                                         headers=headers,
                                         data=json.dumps({}),
                                         auth=HTTPBasicAuth(self.user, self.pwd),
                                         verify=False)
                if resp.status_code == 204:
                    self.token = resp.headers['X-Auth-Token']
                    if self.debug: print('Session %s with %s' % (self.url, self.token))
                    return
            self.login()
        except: raise AsadipySessionError()
    
    def close(self):
        if self.session != None:
            self.session.close()
            self.session = None
            
    def cli(self, *commands):
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy', 'X-Auth-Token' : self.token }
        for i in range(0, self.retry):
            try: resp = self.session.post(self.url + '/api/cli', headers=headers, data=json.dumps({'commands' : commands}), verify=False)
            except: time.sleep(0.5); continue
            if resp.status_code == 200:
                data = resp.json()['response']
                ret = {}
                idx = 0
                for command in commands:
                    try: cdata = data[idx].split('\n')
                    except: cdata = []
                    ret[command] = cdata
                    idx += 1
                return ret
            elif resp.status_code == 401: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['messages'][0]
                        code = error['code']
                        text = error['details']
                    except: raise AsadipyError('?', 'Unknown')
                    else: raise AsadipyError(code, text)
        raise AsadipySessionError()
            
    def get(self, url):
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy', 'X-Auth-Token' : self.token }
        ret = []
        offset = 0
        load = 0
        total = None
        if self.debug:
            print('GET : {}'.format(url))
            while load != total:
                print('Offset : {}, Load : {}, Total : {}'.format(offset, load, total))
                resp = self.session.get(self.url + url + '?offset=%d' % offset, headers=headers, verify=False)
                print resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    rinfo = data['rangeInfo']
                    total = rinfo['total']
                    load += rinfo['limit']
                    offset += 100
                    ret = ret + data['items']
                elif resp.status_code == 401: self.refresh()
                else: break
            print('CODE : {}\n{}'.format(resp.status_code, ret))
            return ret
        for i in range(0, self.retry):
            try:
                while load != total:
                    resp = self.session.get(self.url + url + '?offset=%d' % offset, headers=headers, verify=False)
                    if resp.status_code == 200:
                        data = resp.json()
                        rinfo = data['rangeInfo']
                        total = rinfo['total']
                        load += rinfo['limit']
                        offset += 100
                        ret = ret + data['items']
                    elif resp.status_code == 401: self.refresh()
                return ret
            except: time.sleep(0.5); continue
            if not self.week:
                try:
                    error = resp.json()['messages'][0]
                    code = error['code']
                    text = error['details']
                except: raise AsadipyError('?', 'Unknown')
                else: raise AsadipyError(code, text)
        raise AsadipySessionError()
    
    def post(self, url, data):
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy', 'X-Auth-Token' : self.token }
        if self.debug:
            print('POST : {}'.format(url)); print(data)
            resp = self.session.post(self.url + url, headers=headers, data=data, verify=False)
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return True
        for i in range(0, self.retry):
            try: resp = self.session.post(self.url + url, headers=headers, data=data, verify=False)
            except: time.sleep(0.5); continue
            if resp.status_code == 201: return True
            elif resp.status_code == 401: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['messages'][0]
                        code = error['code']
                        text = error['details']
                    except: raise AsadipyError('?', 'Unknown')
                    else: raise AsadipyError(code, text)
        raise AsadipySessionError()
    
    def put(self, url, data):
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy', 'X-Auth-Token' : self.token }
        if self.debug:
            print('PUT : {}'.format(url)); print(data)
            resp = self.session.put(self.url + url, headers=headers, data=data, verify=False)
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return True
        for i in range(0, self.retry):
            try: resp = self.session.put(self.url + url, headers=headers, data=data, verify=False)
            except: time.sleep(0.5); continue
            if resp.status_code == 204: return True
            elif resp.status_code == 401: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['messages'][0]
                        code = error['code']
                        text = error['details']
                    except: raise AsadipyError('?', 'Unknown')
                    else: raise AsadipyError(code, text)
        raise AsadipySessionError()
    
    def delete(self, url):
        headers = { 'Content-Type': 'application/json', 'Accept': 'application/json', 'User-Agent': 'asadipy', 'X-Auth-Token' : self.token }
        if self.debug:
            print('DELETE : {}'.format(url))
            resp = self.session.delete(self.url + url, headers=headers, verify=False)
            print('CODE : {}\n{}'.format(resp.status_code, resp.text))
            return True
        for i in range(0, self.retry):
            try: resp = self.session.delete(self.url + url, headers=headers, verify=False)
            except: time.sleep(0.5); continue
            if resp.status_code == 204: return True
            elif resp.status_code == 401: self.refresh()
            else:
                if not self.week:
                    try:
                        error = resp.json()['messages'][0]
                        code = error['code']
                        text = error['details']
                    except: raise AsadipyError('?', 'Unknown')
                    else: raise AsadipyError(code, text)
        raise AsadipySessionError()
