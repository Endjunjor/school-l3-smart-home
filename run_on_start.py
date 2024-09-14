import random
import string
import socket
from datetime import datetime, timezone

def check():
    pass

def create():
    pass

def new():
    pass

class generate:
    def system_id():
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
        # Use random.choices() to generate a random string of the specified length
        random_string = ''.join(random.choices(characters, k=12))
        utc_time = datetime.now(timezone.utc)
        formatted_time = utc_time.strftime('%Y%m%d%H%M%S')
        hex_time = hex(int(formatted_time))
        random_string = random_string + hex_time
        return random_string

    def token():
        characters = string.ascii_uppercase + string.ascii_lowercase + string.digits
        # Use random.choices() to generate a random string of the specified length
        random_string = ''.join(random.choices(characters, k=128))
        return random_string
    
class get:
    def ip():
        try:
            # The IP address used here doesn't matter; it's just for checking the LAN IP.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]  # Get the local IP address from the socket
            s.close()
            return lan_ip
        except Exception as e:
            return f"Error: {e}"