'''
Created on 2017. 1. 26.

@author: Hye-Churn Jang
'''

import re

from .static import *
from .session import Session

class StatActor:
    
    def __init__(self, session):
        self.session = session
        
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
            kv = re.match('^Core\s+\d+\s+(?P<five_sec>\d+\.\d+)%\s+(?P<one_min>\d+\.\d+)%\s+(?P<five_min>\d+\.\d+)%', line)
            if kv:
                result['cpu']['core'].append({'5sec' : float(kv.group('five_sec')), '1min' : float(kv.group('one_min')), '5min' : float(kv.group('five_min'))})
        
        mem = data[cli[2]]
        for line in mem:
            kv = re.match('^Free memory system:\s+(?P<bytes>\d+)\s+bytes\s+\((?P<percent>\d+)%\)', line)
            if kv:
                result['memory']['free_bytes'] = int(kv.group('bytes'))
                result['memory']['free_percent'] = int(kv.group('percent'))
                continue
            kv = re.match('^Total memory:\s+(?P<bytes>\d+)\s+bytes', line)
            if kv:
                result['memory']['total_bytes'] = int(kv.group('bytes'))
        result['memory']['used_bytes'] = result['memory']['total_bytes'] - result['memory']['free_bytes']
        result['memory']['used_percent'] = (result['memory']['used_bytes'] * 100) / result['memory']['total_bytes']
        
        disk = data[cli[3]]
        for line in disk:
            kv = re.match('^(?P<total>\d+)\s+bytes total \((?P<free>\d+)\s+bytes free\)', line)
            if kv:
                result['disk']['total'] = int(kv.group('total'))
                result['disk']['free_bytes'] = int(kv.group('free'))
        result['disk']['used_bytes'] = result['disk']['total'] - result['disk']['free_bytes']
        result['disk']['used_percent'] = (result['disk']['used_bytes'] * 100) / result['disk']['total']
        result['disk']['free_percent'] = (result['disk']['free_bytes'] * 100) / result['disk']['total']
        
        return result
    
class NATActor:
     
    def __init__(self, session):
        self.session = session
        
    def Count(self):
        cli = 'show xlate count'
        out = self.session.cli(cli)[cli]
        for line in out:
            kv = re.match('^(?P<in_use>\d+)\s+in use,\s+(?P<most_used>\d+)\s+most used', line)
            if kv:
                return {'in_use' : int(kv.group('in_use')), 'most_used' : int(kv.group('most_used'))}
        return {'in_use' : 0, 'most_used' : 0}
     
    def Detail(self):
        cli = 'show nat detail'
        nat = self.session.cli(cli)[cli]
        cur_config = None
        cur_section = None
        result = []
        while nat:
            line = nat.pop(0)
            kv = re.match('^(?P<config>\w+)\s+NAT\s+Policies\s+\(Section\s+(?P<section>\d+)\)', line)
            if kv:
                cur_config = kv.group('config')
                cur_section = kv.group('section')
                continue
            kv = re.match('^(?P<index>\d+)\s+\((?P<from>\w+)\)\s+to\s+\((?P<to>\w+)\)\s+source\s+(?P<mode>\w+)\s+(?P<o_net>[^\s]+)\s+(?P<t_net>[^\s]+)', line)
            if kv:
                index = kv.group('index')
                f = kv.group('from')
                t = kv.group('to')
                mode = kv.group('mode')
                o_net = kv.group('o_net')
                t_net = kv.group('t_net')
                o_net = o_net if o_net not in ['any', 'interface'] else 'any'
                t_net = t_net if t_net not in ['any', 'interface'] else 'any'
                
                kv = re.match('^\s+translate_hits\s+=\s+(?P<t_hits>\d+),\s+untranslate_hits\s+=\s+(?P<u_hits>\d+)', nat.pop(0))
                t_hits = kv.group('t_hits') if kv else 0
                u_hits = kv.group('u_hits') if kv else 0
                
                kv = re.match('^\s+Source\s+-\s+Origin:\s+(?P<o_addr>[^\s]+),\s+Translated:\s+(?P<t_addr>[^\s]+)', nat.pop(0))
                o_addr = kv.group('o_addr') if kv else None
                t_addr = kv.group('t_addr') if kv else None
                
                result.append({
                    'config' : cur_config, 'section' : int(cur_section), 'index' : int(index), 'mode' : mode,
                    'from' : f, 'to' : t,
                    'originalNetwork' : o_net, 'translatedNetwork' : t_net,
                    'originalAddress' : o_addr, 'translatedAddress' : t_addr,
                    'translateHits' : int(t_hits), 'untranslateHits' : int(u_hits),
                })
                continue
        return result
     
    def Pool(self):
        cli = 'show nat pool'
        pool = self.session.cli(cli)[cli]
        result = []
        for line in pool:
            kv = re.match('^(?P<proto>\w+)\s+(?P<method>\w+)\s+pool\s+(?P<intf>\w+),\s+address\s+(?P<addr>[\W\w]+),\s+range\s+(?P<range>[\W\w]+),\s+allocated\s+(?P<alloc>\d+)', line)
            if kv:
                range = kv.group('range').split('-')
                r_start = range[0]
                r_end = range[1]
                result.append({
                    'proto' : kv.group('proto'),
                    'method' : kv.group('method'),
                    'interface' : kv.group('intf'),
                    'address' : kv.group('addr'),
                    'rangeStart' : int(r_start),
                    'rangeEnd' : int(r_end),
                    'allocCount' : int(kv.group('alloc'))
                })
        return result

class ConnActor:
    
    def __init__(self, session):
        self.session = session

    def Count(self):
        cli = 'show conn count'
        out = self.session.cli(cli)[cli]
        for line in out:
            kv = re.match('^(?P<in_use>\d+)\s+in use,\s+(?P<most_used>\d+)\s+most used', line)
            if kv:
                return {'in_use' : int(kv.group('in_use')), 'most_used' : int(kv.group('most_used'))}
        return {'in_use' : 0, 'most_used' : 0}

    def All(self):
        return self.session.get('monitoring/connections')

class Client(Session, dict):
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, retry=3, debug=False, week=False):
        Session.__init__(self, ip, user, pwd, conns, conn_max, retry, debug, week)
        dict.__init__(self, ip=ip, user=user, pwd=pwd, conns=conns, conn_max=conn_max)
        
        self.Stat = StatActor(self)
        self.NAT = NATActor(self)
        self.Conn = ConnActor(self)
    
class MultiDomain(dict):
    
    class Actor:
        
        def __init__(self, multi_dom, actor_name):
            self.multi_dom = multi_dom
            self.actor_name = actor_name
            
        def __call__(self, *argv, **kargs):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].__getattribute__(self.actor_name)(*argv, **kargs)
            return ret
    
    class StatActor(Actor):
        
        def __init__(self, multi_dom):
            MultiDomain.Actor.__init__(self, multi_dom, 'Stat')
    
    class NATActor(Actor):
        
        def __init__(self, multi_dom):
            MultiDomain.Actor.__init__(self, multi_dom, 'NAT')
        
        def Count(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].NAT.Count()
            return ret
            
        def Detail(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].NAT.Detail()
            return ret
        
        def Pool(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].NAT.Pool()
            return ret
    
    class ConnActor(Actor):
        
        def __init__(self, multi_dom):
            MultiDomain.Actor.__init__(self, multi_dom, 'NAT')
        
        def Count(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].Conn.Count()
            return ret
        
        def All(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].Conn.All()
            return ret
        
    
    def __init__(self, conns=1, conn_max=2, retry=3, debug=False, week=False):
        dict.__init__(self)
        self.conns = conns
        self.conn_max = conn_max
        self.retry = retry
        self.debug = debug
        self.week = week
        
        self.Stat = MultiDomain.StatActor(self)
        self.NAT = MultiDomain.NATActor(self)
        self.Conn = MultiDomain.ConnActor(self)
    
    def addDomain(self, domain_name, ip, user, pwd, conns=None, conn_max=None, retry=None, debug=None, week=None):
        if domain_name in self: return False
        opts = {'ip' : ip, 'user' : user, 'pwd' : pwd}
        if conns != None: opts['conns'] = conns
        if conn_max != None: opts['conn_max'] = conn_max
        if retry != None: opts['retry'] = retry
        if debug != None: opts['debug'] = debug
        if week != None: opts['week'] = week
        try: clnt = Client(**opts)
        except: return False
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
    
    
    
    
    
    