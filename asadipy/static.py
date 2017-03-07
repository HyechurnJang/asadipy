'''
Created on 2017. 1. 26.

@author: Hye-Churn Jang
'''

ASADIPY_REFRESH_SEC = 180

#===============================================================================
# Exception & Error
#===============================================================================

class ExceptAsadipySession(Exception):
    def __init__(self, session):
        Exception.__init__(self, '[Error]Asadipy:Session:%s' % session.url)
        if session.debug: print('[Error]Asadipy:Session:%s' % session.url)

class ExceptAsadipyResponse(Exception):
    def __init__(self, session, code, text):
        Exception.__init__(self, '[Error]Asadipy:Response:%s:%s' % (code, text))
        if session.debug: print('[Error]Asadipy:Response:%s:%s' % (code, text))
