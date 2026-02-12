from  bashconfigparser import BashConfigParser
import requests

config = None
properties = None
base_url: str = ''
config_file: str = '/etc/sysconfig/cranix'
debug: bool = False
headers = None
headers_tex = None
log_file_path: str = ""
log_file = None
property_file: str = '/opt/cranix-java/conf/cranix-api.properties'

def init(_log_file: str = '/tmp/cranix.log', _base_url: str = 'http://localhost:9080/api/' ):
    global config, properties, base_url, config_file, debug, headers, headers_tex
    global log_file_path, log_file, property_file
    properties = BashConfigParser(config_file=property_file)
    config     = BashConfigParser(config_file=config_file)
    token = properties.get('de.cranix.api.auth.localhost')
    base_url = _base_url
    log_file_path = _log_file
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": 'Bearer {0}'.format(token)
    }
    headers_text = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": 'Bearer {0}'.format(token)
    }
    log_file = open(log_file_path, "w")
    debug = config.get('CRANIX_DEBUG', 'no').lower() == 'yes'

def api(url, method='GET', timeout=10, data=None, json=None):
    resp = requests.request(method, base_url + url, headers=headers, timeout=timeout, data=data, json=json)
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        return resp.text

def debug(msg: str):
    if debug:
        print(msg)

def error(msg: str):
    print(msg)

def log(msg: str):
    log_file.write(msg)

def print_error(msg):
    return '<tr><td colspan="2"><font color="red">{0}</font></td></tr>\n'.format(msg)

def print_msg(title, msg):
    return '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(title,msg)

def check_cranixconfig() -> bool:
    try:
        return cranixconfig.CRANIX_DEBUG.lower() == "yes"
    except:
        return True
