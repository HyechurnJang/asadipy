'''
Created on 2017. 1. 26.

@author: Hye-Churn Jang
'''

#===============================================================================
# Exception & Error
#===============================================================================

class AsadipyError(Exception):
    def __init__(self, code, text):
        self.code = code
        self.text = text
    def __str__(self): return 'code:%s-text:%s' % (self.code, self.text)

class AsadipySessionError(Exception): 
    def __str__(self): return 'Asadipy Session Error'

class AsadipyNonExistData(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Non exist data of %s' % self.target_name
    
class AsadipyCreateError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Create failed with %s' % self.target_name
    
class AsadipyUpdateError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Update failed with %s' % self.target_name
    
class AsadipyDeleteError(Exception):
    def __init__(self, target_name): self.target_name = target_name
    def __str__(self): return 'Delete failed with %s' % self.target_name


class AsadipyFlags:
    
    @classmethod
    def Conn(cls, flags):
        ret = []
        for f in flags:
            if f == 'A' : ret.append('awaiting inside ACK to SYN')
            elif f == 'a' : ret.append('awaiting outside ACK to SYN')
            elif f == 'B' : ret.append('initial SYN from outside')
            elif f == 'b' : ret.append('TCP state-bypass or nailed')
            elif f == 'C' : ret.append('CTIQBE media')
            elif f == 'c' : ret.append('cluster centralized')
            elif f == 'D' : ret.append('DNS')
            elif f == 'd' : ret.append('dump')
            elif f == 'E' : ret.append('outside back connection')
            elif f == 'e' : ret.append('semi-distributed')
            elif f == 'F' : ret.append('outside FIN')
            elif f == 'f' : ret.append('inside FIN')
            elif f == 'G' : ret.append('group')
            elif f == 'g' : ret.append('MGCP')
            elif f == 'H' : ret.append('H.323')
            elif f == 'h' : ret.append('H.225.0')
            elif f == 'I' : ret.append('inbound data')
            elif f == 'i' : ret.append('incomplete')
            elif f == 'J' : ret.append('GTP')
            elif f == 'j' : ret.append('GTP data')
            elif f == 'K' : ret.append('GTP t3-response')
            elif f == 'k' : ret.append('Skinny media')
            elif f == 'L' : ret.append('LISP triggered flow owner mobility')
            elif f == 'M' : ret.append('SMTP data')
            elif f == 'm' : ret.append('SIP media')
            elif f == 'N' : ret.append('inspected by Snort')
            elif f == 'n' : ret.append('GUP')
            elif f == 'O' : ret.append('outbound data')
            elif f == 'o' : ret.append('offloaded')
            elif f == 'P' : ret.append('inside back connection')
            elif f == 'Q' : ret.append('Diameter')
            elif f == 'q' : ret.append('SQL*Net data')
            elif f == 'R' : ret.append('outside acknowledged FIN')
            elif f == 'r' : ret.append('inside acknowledged FIN')
            elif f == 'S' : ret.append('awaiting inside SYN')
            elif f == 's' : ret.append('awaiting outside SYN')
            elif f == 'T' : ret.append('SIP')
            elif f == 't' : ret.append('SIP transient')
            elif f == 'U' : ret.append('up')
            elif f == 'V' : ret.append('VPN orphan')
            elif f == 'W' : ret.append('WAAS')
            elif f == 'w' : ret.append('secondary domain backup')
            elif f == 'X' : ret.append('inspected by service module')
            elif f == 'x' : ret.append('per session')
            elif f == 'Y' : ret.append('director stub flow')
            elif f == 'y' : ret.append('backup stub flow')
            elif f == 'Z' : ret.append('Scansafe redirection')
            elif f == 'z' : ret.append('forwarding stub flow')
        return ret