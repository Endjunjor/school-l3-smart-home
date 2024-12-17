import json

# Read the JSON file into memory (the file will not be modified when calling functions)
def get_devices():
    try:
        with open('device.json', 'r') as file:
            devices = json.load(file)
    except FileNotFoundError:
        print("device.json file not found. Starting with an empty list.")
        devices = []
    except json.JSONDecodeError:
        print("device.json file is empty or corrupted. Starting with an empty list.")
        devices = []
    return devices
    

def get_device(pin):
    try:
        with open('device.json', 'r') as file:
            devices = json.load(file)
    except FileNotFoundError:
        print("device.json file not found. Starting with an empty list.")
        return None
    except json.JSONDecodeError:
        print("device.json file is empty or corrupted. Starting with an empty list.")
        return None

    # Search for the device by pin
    for device in devices:
        if device['pin'] == pin:
            return device

    # If no device with the given pin was found
    print(f"No device found with pin {pin}.")
    return None

# Write the updated devices back to the JSON file
def _save_devices(devices):
    with open('device.json', 'w') as file:
        json.dump(devices, file, indent=4)

# Check if a pin is already in use
def check_pin(pin):
    devices = get_devices()
    for device in devices:
        if device["pin"] == pin:
            return True
    return False

# Remove a device by its pin
def remove(pin):
    devices = get_devices()
    updated_devices = [device for device in devices if device["pin"] != pin]

    # Check if any device was removed
    if len(devices) == len(updated_devices):
        print(f"No device found on pin {pin}.")
    else:
        _save_devices(updated_devices)
        print(f"Device on pin {pin} has been removed.")

# Add a new device to the JSON file
def add_device(devicename, pin, device_type):
    devices = get_devices()

    # Check if the pin is already in use
    if check_pin(pin) == True:
        return False

    # Create a new device dictionary
    new_device = {
        "devicename": devicename,
        "pin": pin,
        "device_type": device_type
    }

    # Add the new device to the list
    devices.append(new_device)

    # Save the updated device list back to the JSON file
    _save_devices(devices)
    print(f"Device '{devicename}' added successfully on pin {pin}.")
    return True