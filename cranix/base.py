from  bashconfigparser import BashConfigParser
import cranixconfig
import requests

_base_url
_debug
_headers
_headers_tex
_log_file_path
_log_file
_property_file: str = '/opt/cranix-java/conf/cranix-api.properties'
_properties

def __init__():
    init()
    
def init(logfile: str = '/tmp/cranix.log', base_url: str = 'http://localhost:9080/api/' ):
    _properties = BashConfigParser()
    _properties.parse_file(property_file)
    _token = properties.get('de.cranix.api.auth.localhost')
    _headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": 'Bearer {0}'.format(self.token)
    }
    _headers_text = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": 'Bearer {0}'.format(self.token)
    }
    _log_file = open(logfile, "w")
    _debug = check_cranixconfig()

def api(url, method='GET', timeout=10, data=None, json=None):
    resp = requests.request(method=method, url=_base_url + url, headers=_headers, timeout=timeout, data=data, json=json)
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
    _log_file.write(msg)

def print_error(msg):
    return '<tr><td colspan="2"><font color="red">{0}</font></td></tr>\n'.format(msg)

def print_msg(title, msg):
    return '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(title,msg)

def check_cranixconfig() -> bool:
    try:
        return cranixconfig.CRANIX_DEBUG.lower() == "yes"
    except:
        return True
