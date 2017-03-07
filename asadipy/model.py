'''
Created on 2017. 1. 26.

@author: Hye-Churn Jang
'''

import re
import gevent

from pygics import Task, RestAPI

from .static import *
from .session import Session

#===============================================================================
# Client
#===============================================================================

class ClientActor:
    def __init__(self, session): self.session = session

class MultiDomActor:
    def __init__(self, multi_dom): self.multi_dom = multi_dom
    
class Client(Session, dict, Task):
    
    class StatActor(ClientActor):
        
        def __init__(self, session):
            ClientActor.__init__(self, session)
        
        def __call__(self):
            cli = [
                'show cpu usage | include CPU utilization',
                'show cpu core | include %',
                'show memory detail | include Total|Free memory system',
                'show disk all | include bytes total'
            ]
            data = self.session.cli(*cli)
            result = {'cpu' : {'core' : []}, 'memory' : {}, 'disk' : {}}
             
            usage = data[cli[0]]
            for line in usage:
                kv = re.match('^CPU utilization for 5 seconds = (?P<five_sec>\d+)%; 1 minute: (?P<one_min>\d+)%; 5 minutes: (?P<five_min>\d+)%', line)
                if kv:
                    result['cpu']['total'] = {'5sec' : int(kv.group('five_sec')), '1min' : int(kv.group('one_min')), '5min' : int(kv.group('five_min'))}
                    break 
             
            core = data[cli[1]]
            for line in core:
                kv = re.match('^Core \d+\s+(?P<five_sec>\d+\.\d+)%\s+(?P<one_min>\d+\.\d+)%\s+(?P<five_min>\d+\.\d+)%', line)
                if kv:
                    result['cpu']['core'].append({'5sec' : float(kv.group('five_sec')), '1min' : float(kv.group('one_min')), '5min' : float(kv.group('five_min'))})
             
            mem = data[cli[2]]
            for line in mem:
                kv = re.match('^Free memory system:\s+(?P<bytes>\d+) bytes \((?P<percent>\d+)%\)', line)
                if kv:
                    result['memory']['free_bytes'] = int(kv.group('bytes'))
                    result['memory']['free_percent'] = int(kv.group('percent'))
                    continue
                kv = re.match('^Total memory:\s+(?P<bytes>\d+) bytes', line)
                if kv:
                    result['memory']['total_bytes'] = int(kv.group('bytes'))
            result['memory']['used_bytes'] = result['memory']['total_bytes'] - result['memory']['free_bytes']
            result['memory']['used_percent'] = (result['memory']['used_bytes'] * 100) / result['memory']['total_bytes']
             
            disk = data[cli[3]]
            for line in disk:
                kv = re.match('^(?P<total>\d+) bytes total \((?P<free>\d+) bytes free\)', line)
                if kv:
                    result['disk']['total'] = int(kv.group('total'))
                    result['disk']['free_bytes'] = int(kv.group('free'))
            result['disk']['used_bytes'] = result['disk']['total'] - result['disk']['free_bytes']
            result['disk']['used_percent'] = (result['disk']['used_bytes'] * 100) / result['disk']['total']
            result['disk']['free_percent'] = (result['disk']['free_bytes'] * 100) / result['disk']['total']
             
            return result
    
    class ConnActor(ClientActor):
        
        def __init__(self, session):
            ClientActor.__init__(self, session)
        
        def count(self):
            cli = 'show conn count'
            out = self.session.cli(cli)[cli]
            for line in out:
                kv = re.match('^(?P<in_use>\d+) in use, (?P<most_used>\d+) most used', line)
                if kv: return {'in_use' : int(kv.group('in_use')), 'most_used' : int(kv.group('most_used'))}
            return {'in_use' : 0, 'most_used' : 0}
        
        def list(self):
            return self.session.get('monitoring/connections')
    
    class ObjectActor(ClientActor):
        
        def __init__(self, session):
            ClientActor.__init__(self, session)
        
        def __call__(self):
            ret = {}
            results = self.session.get('/api/objects/networkobjects')
            for result in results: ret[result['objectId']] = result['host']['value']
            return ret
    
    class ObjectGroupActor(ClientActor):
        
        def __init__(self, session):
            ClientActor.__init__(self, session)
            
        def __call__(self):
            ret = {}
            results = self.session.get('/api/objects/networkobjectgroups')
            for result in results: ret[result['objectId']] = [ member['objectId'] for member in result['members']]
            return ret
    
    class NATActor(ClientActor):
    
        class NATPoolActor(ClientActor):
            
            def __init__(self, session):
                ClientActor.__init__(self, session)
            
            def list(self):
                result = []
                cli = 'show nat pool | grep NAT pool'
                out = self.session.cli(cli)[cli]
                for line in out:
                    kv = re.match('^NAT pool (?P<target>[\W\w]+), range (?P<range>[\d\.]+-[\d\.]+), allocated (?P<allocated>\d+)', line)
                    if kv:
                        target = kv.group('target')
                        if ':' in target:
                            intf_name = target.split(':')
                            intf = intf_name[0]
                            name = intf_name[1]
                        else:
                            intf = target
                            name = 'N/A'
                        result.append({'interface' : intf, 'name' : name, 'range' : kv.group('range'), 'allocated' : int(kv.group('allocated'))})
                return result
        
        class PATPoolActor(ClientActor):
            
            def __init__(self, session):
                ClientActor.__init__(self, session)
            
            def list(self):
                result = []
                cli = 'show nat pool | grep PAT pool'
                out = self.session.cli(cli)[cli]
                for line in out:
                    kv = re.match('^(?P<proto>\w+) PAT pool (?P<target>[\W\w]+), address (?P<addr>[\d\.]+), range (?P<range>\d+-\d+), allocated (?P<allocated>\d+)', line)
                    if kv:
                        target = kv.group('target')
                        if ':' in target:
                            intf_name = target.split(':')
                            intf = intf_name[0]
                            name = intf_name[1]
                        else:
                            intf = target
                            name = 'N/A'
                        result.append({'interface' : intf, 'name' : name, 'address' : kv.group('addr'), 'protocol' : kv.group('proto'), 'range' : kv.group('range'), 'allocated' : int(kv.group('allocated'))})
                return result
        
        def __init__(self, session):
            ClientActor.__init__(self, session)
            self.NATPool = Client.NATActor.NATPoolActor(session)
            self.PATPool = Client.NATActor.PATPoolActor(session)
            
        def list(self):
            ret = []
            results = self.session.get('/api/nat/before')
            for result in results:
                patPool = result['isPatPool']
                data = {
                    'mode' : result['mode'],
                    'patPool' : patPool,
                    'oInterface' : result['originalInterface']['objectId'],
                    'tInterface' : result['translatedInterface']['objectId'],
                    'oSource' : result['originalSource']['objectId'],
                }
                if patPool: data['tSource'] = result['translatedSourcePatPool']['objectId']
                else : data['tSource'] = result['translatedSource']['objectId']
                ret.append(data)
            return ret
        
        def count(self):
            cli = 'show xlate count'
            out = self.session.cli(cli)[cli]
            for line in out:
                kv = re.match('^(?P<in_use>\d+) in use, (?P<most_used>\d+) most used', line)
                if kv: return {'in_use' : int(kv.group('in_use')), 'most_used' : int(kv.group('most_used'))}
            return {'in_use' : 0, 'most_used' : 0}
    
    def __init__(self, ip, user, pwd, refresh_sec=ASADIPY_REFRESH_SEC, **kargs):
        Session.__init__(self,
                         ip=ip,
                         user=user,
                         pwd=pwd,
                         refresh_sec=refresh_sec,
                         **kargs)
        dict.__init__(self,
                      ip=ip,
                      user=user,
                      pwd=pwd)
        
        self.Stat = Client.StatActor(self)
        self.Conn = Client.ConnActor(self)
        self.Object = Client.ObjectActor(self)
        self.ObjectGroup = Client.ObjectGroupActor(self)
        self.NAT = Client.NATActor(self)
    
class MultiDomain(dict):
    
    class StatActor(MultiDomActor):
        
        def __init__(self, multi_dom):
            MultiDomActor.__init__(self, multi_dom)
        
        def __call__(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].Stat()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
    
    class ConnActor(MultiDomActor):
        
        def __init__(self, multi_dom):
            MultiDomActor.__init__(self, multi_dom)
        
        def count(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].Conn.count()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
        
        def list(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].Conn.list()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
    
    class ObjectActor(MultiDomActor):
        
        def __init__(self, multi_dom):
            MultiDomActor.__init__(self, multi_dom)
        
        def __call__(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].Object()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
    
    class ObjectGroupActor(MultiDomActor):
        
        def __init__(self, multi_dom):
            MultiDomActor.__init__(self, multi_dom)
        
        def __call__(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].ObjectGroup()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
    
    class NATActor(MultiDomActor):
        
        class NATPoolActor(MultiDomActor):
            
            def __init__(self, multi_dom):
                MultiDomActor.__init__(self, multi_dom)
            
            def list(self):
                ret = {}; fetchs = []
                def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].NAT.NATPool.list()
                for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
                gevent.joinall(fetchs)
                return ret
        
        class PATPoolActor(MultiDomActor):
            
            def __init__(self, multi_dom):
                MultiDomActor.__init__(self, multi_dom)
            
            def list(self):
                ret = {}; fetchs = []
                def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].NAT.PATPool.list()
                for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
                gevent.joinall(fetchs)
                return ret
        
        def __init__(self, multi_dom):
            MultiDomActor.__init__(self, multi_dom)
            
            self.NATPool = MultiDomain.NATActor.NATPoolActor(multi_dom)
            self.PATPool = MultiDomain.NATActor.PATPoolActor(multi_dom)
            
        def list(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].NAT.list()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
        
        def count(self):
            ret = {}; fetchs = []
            def fetch(multi_dom, dom_name, ret): ret[dom_name] = multi_dom[dom_name].NAT.count()
            for dom_name in self.multi_dom: fetchs.append(gevent.spawn(fetch, self.multi_dom, dom_name, ret))
            gevent.joinall(fetchs)
            return ret
    
    def __init__(self,
                 conns=RestAPI.DEFAULT_CONN_SIZE,
                 conn_max=RestAPI.DEFAULT_CONN_MAX,
                 retry=RestAPI.DEFAULT_CONN_RETRY,
                 refresh_sec=ASADIPY_REFRESH_SEC,
                 debug=False):
        dict.__init__(self)
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.refresh_sec = refresh_sec
        self.debug = debug
        
        self.Stat = MultiDomain.StatActor(self)
        self.Conn = MultiDomain.ConnActor(self)
        self.Object = MultiDomain.ObjectActor(self)
        self.ObjectGroup = MultiDomain.ObjectGroupActor(self)
        self.NAT = MultiDomain.NATActor(self)
    
    def addDomain(self, domain_name, ip, user, pwd):
        if domain_name in self:
            if self.debug: print('[Error]Asadipy:Multidomain:AddDomain:Already Exist Domain %s' % domain_name)
            return False
        opts = {'ip' : ip,
                'user' : user,
                'pwd' : pwd,
                'conns' : self.conns,
                'conn_max' : self.conn_max,
                'retry' : self.retry,
                'refresh_sec' : self.refresh_sec,
                'debug' : self.debug}
        try: clnt = Client(**opts)
        except Exception as e:
            if self.debug: print('[Error]Asadipy:Multidomain:AddDomain:%s' % str(e))
            return False
        self[domain_name] = clnt
        return True
    
    def delDomain(self, domain_name):
        if domain_name not in self: return False
        self[domain_name].close()
        self.pop(domain_name)
        return True
    
    def close(self):
        dom_names = self.keys()
        for dom_name in dom_names: self.delDomain(dom_name)
    