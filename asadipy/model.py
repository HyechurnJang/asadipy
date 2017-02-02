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
     
    def __call__(self):
        cli = 'show nat'
        nat = self.session.cli(cli)[cli]
        cur_config = None
        cur_where = None
        cur_section = None
        result = []
        while nat:
            line = nat.pop(0)
            kv = re.match('^(?P<config>\w+)\s+(?P<where>\w+)\s+Policies\s+\(Section\s+(?P<section>\d+)\)', line)
            if kv:
                cur_config = kv.group('config')
                cur_where = kv.group('where')
                cur_section = kv.group('section')
                continue
            kv = re.match('^(?P<index>\d+)\s+\((?P<o_intf>\w+)\)\s+to\s+\((?P<t_intf>\w+)\)\s+source\s+(?P<mode>\w+)\s+(?P<o_src>[\W\w]+)\s+(?P<t_src>[\W\w]+)', line)
            if kv:
                index = kv.group('index')
                o_intf = kv.group('o_intf')
                t_intf = kv.group('t_intf')
                mode = kv.group('mode')
                o_src = kv.group('o_src')
                t_src = kv.group('t_src')
                kv = re.match('^\s+translate_hits\s+=\s+(?P<t_hits>\d+),\s+untranslate_hits\s+=\s+(?P<u_hits>\d+)', nat.pop(0))
                t_hits = kv.group('t_hits') if kv else 0
                u_hits = kv.group('u_hits') if kv else 0
                result.append({
                    'config' : cur_config, 'where' : cur_where, 'section' : int(cur_section), 'index' : int(index), 'mode' : mode,
                    'originalInterface' : o_intf, 'translatedInterface' : t_intf,
                    'originalSource' : o_src, 'translatedSource' : t_src,
                    'translateHits' : int(t_hits), 'untranslateHits' : int(u_hits)
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

class Client(Session, dict):
    
    def __init__(self, ip, user, pwd, conns=1, conn_max=2, retry=3, debug=False, week=False):
        Session.__init__(self, ip, user, pwd, conns, conn_max, retry, debug, week)
        dict.__init__(self, ip=ip, user=user, pwd=pwd, conns=conns, conn_max=conn_max)
        
        self.Stat = StatActor(self)
        self.NAT = NATActor(self)
    
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
        
        def Pool(self):
            ret = {}
            for dom_name in self.multi_dom: ret[dom_name] = self.multi_dom[dom_name].NAT.Pool()
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
    
    
    
    
    
    