import datetime
import json
import os
import random
import re
import string

try:
    from _logger import Logger
except:
    from . import _logger
    from ._logger import Logger

from typing import Dict, Any
from subprocess import run, PIPE

logger = Logger()
valid_uid = re.compile(r"^[a-zA-Z0-9]+[a-zA-Z0-9\.\-\_]*[a-zA-Z0-9]$")


"""
Functions to handle user
"""
def add_user(user):
    file_name = '{0}/tmp/user_add.{1}'.format(import_dir,new_user_count)
    with open(file_name, 'w') as fp:
        json.dump(user, fp, ensure_ascii=False)
    result = json.load(os.popen('/usr/sbin/crx_api_post_file.sh users/insert ' + file_name))
    logger.debug(result)
    if result['code'] == 'ERROR':
        log_error(result['value'])
    return result

def modify_user(user):
    file_name = '{0}/tmp/user_modify.{1}'.format(import_dir,user['uid'])
    with open(file_name, 'w') as fp:
        json.dump(user, fp, ensure_ascii=False)
    result = json.load(os.popen('/usr/sbin/crx_api_post_file.sh users/{0} "{1}" '.format(user['id'],file_name)))
    logger.debug(result)
    if result['code'] == 'ERROR':
        log_error(result['value'])
    return result

def move_user(user, old_classes, new_classes, debug: bool = False, cleanClassDirs: bool = False):
    uid = user['uid']
    if not cleanClassDirs and user['role'] == 'students':
        if len(old_classes) > 0 and len(new_classes) > 0 and old_classes[0] != new_classes[0]:
            cmd = '/usr/share/cranix/tools/move_user_class_files.sh "{0}" "{1}" "{2}"'.format(uid,old_classes[0],new_classes[0])
            logger.debug(cmd)
            result = os.popen(cmd).read()
            logger.debug(result)

    for g in old_classes:
       if g == '' or g.isspace():
            continue
       if not g in new_classes:
           cmd = '/usr/sbin/crx_api_text.sh DELETE "users/text/{0}/groups/{1}"'.format(uid,g)
           logger.debug(cmd)
           result = os.popen(cmd).read()
           logger.debug(result)
    for g in new_classes:
       if g == '' or g.isspace():
            continue
       if not g in old_classes:
           cmd = '/usr/sbin/crx_api_text.sh PUT "users/text/{0}/groups/{1}"'.format(uid,g)
           logger.debug(cmd)
           result = os.popen(cmd).read()
           logger.debug(result)

def delete_user(user, debug: bool = False):
    cmd = '/usr/sbin/crx_api_text.sh DELETE "users/text/{0}"'.format(user['uid'])
    if debug:
        print(cmd)
    result = os.popen(cmd).read()
    if debug:
        print(result)

def build_user_id(user: dict, identifier: str) -> str:

    if identifier == "sn-gn-bd":
        uid = f"{user['surName']}-{user['givenName']}-{user['birthDay']}"

    else:
        uid = user.get(identifier, "")

    return uid.upper().replace(" ", "_")

def get_users(role: str, identifier: str = "sn-gn-bd", debug: bool = False) -> Dict[str, Dict[str, Any]]:

    all_users = {}

    cmd = f'/usr/sbin/crx_api.sh GET users/byRole/{role}'
    users_data = []
    try:
        users_data = json.load(os.popen(cmd))
    except:
        pass

    for user in users_data:
        user_id = build_user_id(user, identifier)
        all_users[user_id] = dict(user)

    if debug:
        print("All existing users:")
        print(all_users)

    return all_users

def create_secure_pw(length: int = 10) -> str:

    if length < 4:
        raise ValueError("Password must be at least 4 characters")

    letters = string.ascii_letters
    signs = ['#', '+', '$']

    num_letters = length - 2
    pw_letters = [random.choice(letters) for _ in range(num_letters)]
    pw_letters.insert(random.randint(0, num_letters), random.choice(signs))
    pw_letters.insert(random.randint(0, num_letters + 1), random.choice(signs))
    return ''.join(pw_letters)

def check_uid(uid: str):
    if len(uid) < 2:
        return "UID must contains at last 2 characters"
    if len(uid) > 32:
        return "UID must not contains more then 32 characters"
    if not valid_uid.match(uid):
        return "UID contains invalid chracter."
    p = run(["/usr/bin/id",uid], stdout=PIPE, stderr=PIPE)
    if p.returncode == 0:
        return "uid '{}' is not unique".format(uid)
    return ""

def check_password(password):
    try:
        p = run("/usr/share/cranix/tools/check_password_complexity.sh", stdout=PIPE,  stderr=PIPE, input=password, encoding='ascii')
    except UnicodeEncodeError:
        print("Password not ascii")
    else:
        if p.stdout != "":
            (a,b) = p.stdout.split("##")
            return a.replace('%s','{}').format(b.strip())
    return ""

def read_birthday(bd: str) -> str:

    """

    Supporting formats:

      - YYYY-MM-DD
      - DD.MM.YYYY
      - YYYYMMDD

    """

    bd = bd.strip()
    formats = ["%Y-%m-%d", "%d.%m.%Y", "%Y%m%d"]

    for format in formats:

        try:

            dt = datetime.datetime.strptime(bd, format)
            return dt.strftime("%Y-%m-%d")

        except ValueError:
            continue

    raise ValueError(f"Bad birthday format: {bd}")


# Usage
if __name__ == "__main__":
    users = get_users('students')
    print('There are {0} students in the school'.format(len(users)))
    print('This is a secure password {0}'.format(create_secure_pw()))
    print('This is a bad uid "a" {0}:'.format(check_uid('a')))
    print('Good date time 20220405 {0}:'.format(read_birthday('20220405')))
    print('Bad date time 220405 {0}:'.format(read_birthday('220405')))

