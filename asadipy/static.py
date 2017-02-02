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
