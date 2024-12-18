class DBExistsException(Exception):
    def __init__(self, message, errors):            
        super().__init__(message)
        self.errors = errors

class DeviceTypeNotFoundException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
    
class DeviceNotFoundException(Exception):
    def __init__(self, message, errors):
        super().__init__(message)
    