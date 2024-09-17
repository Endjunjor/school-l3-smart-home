from flask import Flask, render_template, redirect, request, url_for, render_template_string, flash, abort
import led as LEDC
import file_access as FA
import requests
import json
import urllib.parse
import configparser
import run_on_start as setup2

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('.conf')

if config['SYSTEM']['secret_key'].strip('"') != " ":
    app.secret_key = config['SYSTEM']['secret_key'].strip('"')  # Needed for flashing messages
else:
    secret_key = str(setup2.generate.token())
    app.secret_key = secret_key
    config.set('SYSTEM', 'secret_key', f'"{secret_key}"')

if config['SYSTEM']['system_id'].strip('"') != " ":
    system_id = config['SYSTEM']['system_id'].strip('"')  # Needed for flashing messages
else:
    system_id = str(setup2.generate.system_id())
    config.set('SYSTEM', 'system_id', f'"{system_id}"')

global api_active
global api_token
global api_list
api_active = bool(config['DEFAULT']['api_active'].strip('"'))

api_config = configparser.ConfigParser()
api_config.read('api.conf')

api_list = []
for api_group in api_config:
    if api_group != "DEFAULT":
        api_list += [{ "url": api_config[api_group]['url'].strip('"'), "token": api_config[api_group]['token'].strip('"')}]

global connect2api
global access_url
connect2api =  config['SYSTEM']['connect2api']
access_token = config['DEFAULT']['access_token'].strip('"')  # Remove quotes

if config['DEFAULT']['access_url'].strip('"') != "":
    access_url = config['DEFAULT']['access_url'].strip('"')  # Remove quotes
else:
    access_url = "http://" +setup2.get.ip() + ":" + config['DEFAULT']['port'].strip('"')
access_url = urllib.parse.quote(access_url)

with open('.conf', 'w') as configfile:
    config.write(configfile)


def call_api_info():
    for api in api_list:
        print()
        url = api['url'] + f'/api/info?code='+ api['token']
        response = requests.get(url)
        response = json.loads(response.text)[0]
        api['system_id'] = str(response['system_id'])

def get_api(api_id):
    for api in api_list:
        if api['system_id'] == api_id:
            return api
    return "[{ 'response': 'error'}]"

#  loacal functions
@app.route('/')
def home():
    devices = FA.get_devices()
    for device in devices:
        device['state'] = LEDC.get.led(int(device['pin']))

    if config['SYSTEM']['connect2api'].strip('"') == "true":
        for response in call_all_apis("json"):
            devices += response

    return render_template('index.html', devices=devices)

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
    return render_template('device.html', device=device)

@app.route('/switch/<pin>/')
def device_switch(pin):
    pin = int(pin)
    device = FA.get_device(pin)
    if device is None:
        return redirect(url_for('error'))
    LEDC.set.switch(pin)
    return redirect(f'/device/{pin}')

@app.route('/unset/<pin>/')
def unset_pin(pin):
    device = FA.get_device(pin)
    if device is None:
        return redirect(url_for('error'))
    FA.remove(pin)
    LEDC.clear_led(pin)
    
    flash(f'Pin "{pin}" is now unset and cleand.', 'success')
    return redirect('/')

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
    try:
        if device_type == 'output':
            if LEDC.setup_led(pin):
                flash(f'Device "{device_name}" added successfully.', 'success')
                pass
            else:
                FA.remove(pin)
                flash(f'Error by pin setup "{device_name}" are not created.', 'error')
        elif device_type == 'input':
            LEDC.setup_button(pin)
            pass
    except:
        FA.remove(pin)
        flash(f'Error "{device_name}" are not created.', 'error')

    return redirect("/")

@app.route('/remove/<pin>')
def remove_device(pin):
    pin = int(pin)
    LEDC.clear_led(pin)
    FA.remove_device(pin)
    flash(f'Pin "{pin}" removed successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/<all>')
def catch(all = None):
    return render_template('error.html')

@app.route('/error')
def error():
    return render_template('error.html')

#--------------------------------------------------------------
# call_api's

def call_all_apis(url_part):
    if api_active == True:
        full_response = []
        for api in api_list:
            try:
                url = api['url'] + f'/api/get/{url_part}?code='+ api['token']  
                response = requests.get(url)
                if str(response) == "<Response [401]>":
                    flash( '"'+ api['url'] +'" Authorisation failed', 'error')
                else:
                    full_response += [json.loads(response.text)]
            except:
                flash( api['url'] +' is not available', 'error')
                pass
            
        return full_response
    
def call_api(url_part, use_api):
    if api_active == True:
        url = use_api['url'] + f'/api/{url_part}?code='+use_api['token']  
        response = json.loads(requests.get(url).text)[0]
        return response

@app.route('/api/device/<pin>/', methods=['GET'])
def call_api_device(pin):
    api_id = request.args.get('system_id')
    api_call = get_api(api_id)
    response = call_api(f"get/device/{pin}", api_call)
    return render_template('device.html', device=response)
    

@app.route('/api/switch/<pin>/', methods=['GET'])
def call_api_device_switch(pin):
    api_id = request.args.get('system_id')
    api_call = get_api(api_id)
    response = call_api(f"set/switch/{pin}", api_call)
    return redirect(f'/api/device/'+str(response['pin'])+'?system_id='+str(response['system_id']))

@app.route('/api/unset/<pin>/', methods=['GET'])
def call_unset_device(pin):
    api_id = request.args.get('system_id')
    api_call = get_api(api_id)
    pin = int(pin)
    if call_api(f"set/unset/{pin}", api_call)['response'] == 'success':
        flash(f'Pin "{pin}" removed successfully.', 'success')
    else:
        flash(f'Pin "{pin}" could not be removed.', 'error')

    return redirect('/')

#--------------------------------------------------------------
# api response

@app.route('/api/info/')
def info():
    return '[{ "system_id": "'+system_id+'", "version": "0.0.1", "allow_connection": "'+str(api_active)+'"}]'

def auth_check(code):
    if code == access_token:
        return True
    else:
        return False

@app.route('/api/get/json/')
def home_json():
    code = request.args.get('code')
    if auth_check(code):
        devices = FA.get_devices()
        for device in devices:
            try:
                device['state'] = LEDC.state(device['pin'])
            except:
                device['state'] = False
            device['system_id'] = system_id
        return devices
    else:
        abort(401)

@app.route('/api/get/device/<pin>/')
def api_device(pin):
    code = request.args.get('code')
    if auth_check(code):
        pin = int(pin)
        if LEDC.get.led(pin):
            return '[{ "devicename": "API", "pin": '+str(pin)+', "device_type": "output", "state": true, "system_id": "'+system_id+'" }]'
        else:
            return '[{ "devicename": "API", "pin": '+str(pin)+', "device_type": "output", "state": false, "system_id": "'+system_id+'" }]'
    abort(401)

@app.route('/api/set/switch/<pin>/')
def api_device_switch(pin):
    code = request.args.get('code')
    if auth_check(code):
        pin = int(pin)
        device = FA.get_device(pin)
        if device is None:
            return '[{ "state": false}]'
        LEDC.set.switch(pin)
        return '[{ "pin": '+str(pin)+', "system_id": "'+system_id+'" }]'
    return "[{ 'error': 'Authorisation failed' }]"

@app.route('/api/set/unset/<pin>')
def api_set_unset_device(pin):
    code = request.args.get('code')
    if auth_check(code):
        pin = int(pin)
        call_url = request.args.get('url')
        try:
            LEDC.clear_led(pin)
            FA.remove_device(pin)
            return [{"response": "success"}]
        except:
            return [{"response": "error"}]
    return "[{ 'error': 'Authorisation failed' }]"

#--------------------------------------------------------------

call_api_info()

def start():
    app.run(debug=True, port=config['DEFAULT']['port'].strip('"'), host='0.0.0.0')

start()