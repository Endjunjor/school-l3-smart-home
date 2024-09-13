from flask import Flask, render_template, redirect, request, url_for, render_template_string, flash
import led as LEDC
import file_access as FA
import requests
import json
import urllib.parse
import configparser

app = Flask(__name__)
app.secret_key = 'AkQKuw2VBLp7MTXhKlPrQ3zS3rj4pXtMqUZw6lz3CgOdkBhaljpXQg8VDSmWtHvX'  # Needed for flashing messages

config = configparser.ConfigParser()
config.read('.conf')

global api_active
global api_token
api_active = bool(config['DEFAULT']['api_active'].strip('"'))
api_token = config['DEFAULT']['api_token'].strip('"')
api_url = [] #["http://172.16.111.11:5000/", "http://127.0.0.1:5001/"]

global access_token
global access_url
access_token = config['DEFAULT']['access_token'].strip('"')  # Remove quotes
access_url = config['DEFAULT']['access_url'].strip('"')  # Remove quotes
access_url = urllib.parse.quote(access_url)

def call_all_apis(url_part):
    if api_active == True:
        full_response = []
        for single_api_url in api_url:
            url = f'{single_api_url}{api_token}/{url_part}'  # Replace with the URL you want to fetch
            response = requests.get(url)
            full_response += [json.loads(response.text)]
            
        return full_response
    
def call_api(url_part, api_url):
    if api_active == True:
        url = f'{api_url}{api_token}/{url_part}'  # Replace with the URL you want to fetch
        response = requests.get(url)
        print(url)
        print(response.text)
        return response.text

@app.route('/')
def home():
    devices = FA.get_devices()
    for device in devices:
        device['state'] = LEDC.get.led(int(device['pin']))
        # device['state'] = True

    # for device in call_api("json"):
    #     print(device)
    for response in call_all_apis("json"):
        devices += response
    # print(devices)

    return render_template('index.html', devices=devices)

@app.route('/<key>/json/')
def home_json(key):
    if key == access_token:
        devices = FA.get_devices()
        for device in devices:
            device['state'] = LEDC.state(device['pin'])
            # device['state'] = True
            device['access_url'] = access_url
        return devices
    else:
        return redirect(url_for('error'))

@app.route('/device/<pin>/')
def device(pin):
    pin = int(pin)
    device = FA.get_device(pin)
    if device is None:
        return redirect(url_for('error'))
    try:
        device['state'] = LEDC.get.led(pin)
    except:
        device['state'] = False
    # device['state'] = True
    return render_template('device.html', device=device)

@app.route('/switch/<pin>/')
def device_switch(pin):
    pin = int(pin)
    device = FA.get_device(pin)
    if device is None:
        return redirect(url_for('error'))
    LEDC.set.switch(pin)
    return redirect(f'/device/{pin}')

@app.route('/api/device/<pin>/', methods=['GET'])
def call_api_device(pin):
    call_url = request.args.get('url')
    call_api(f"switch/{pin}", call_url)
    return 'response'
    

@app.route('/api/switch/<pin>/', methods=['GET'])
def call_api_device_switch(pin):
    call_url = request.args.get('url')
    return 'response'
    

@app.route('/<key>/device/<pin>/')
def api_device(key, pin):

    return 'response'

@app.route('/<key>/switch/<pin>/')
def api_device_switch(key, pin):

    return 'response'

@app.route('/unset/<pin>/')
def unset_pin(pin):
    device = FA.get_device(pin)
    if device is None:
        return redirect(url_for('error'))
    FA.remove(pin)
    LEDC.clear_led(pin)
    
    flash(f'Pin "{pin}" is now unset and cleand.', 'success')
    return redirect(f'/')

@app.route('/add-device', methods=['POST'])
def add_device():
    device_name = request.form.get('deviceName')
    pin = int(request.form.get('pin'))
    device_type = request.form.get('deviceType')

    if FA.check_pin(pin) == False:
        FA.add_device(device_name, pin, device_type)
        
    else:
        flash(f'Error: Pin "{pin}" is already in use.', 'error')
        return redirect(url_for('home'))
    print('a')
    if device_type == 'output':
        print('b')
        # if LEDC.usable(pin) == False:
        #     print('x')
        #     flash(f'Error: Pin "{pin}" is not ready, please check wirering.', 'error')
        # else:
        print('y')
        print(LEDC.setup_led(pin))
        # Perform the desired action here
        flash(f'Device "{device_name}" added successfully.', 'success')
        pass
    elif device_type == 'input':
        print('z')
        LEDC.setup_button(pin)
        pass
    
    print('k')
    return redirect(url_for('home'))

@app.route('/test_ms/<type>')
def test_ms(type):
    flash(f'Test message', type)
    devices = FA.get_devices()
    return render_template('index.html', devices=devices)

@app.route('/<all>')
def catch(all = None):
    return render_template('error.html')

@app.route('/error')
def error():
    return render_template('error.html')

# if __name__ == '__main__':
def start():
    app.run(debug=True, port=config['DEFAULT']['port'].strip('"'), host='0.0.0.0')

start()