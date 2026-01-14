import string
from curses.ascii import controlnames
from random import *
from subprocess import run, PIPE
import datetime
import re

valid_uid = re.compile(r"^[a-zA-Z0-9]+[a-zA-Z0-9\.\-\_]*[a-zA-Z0-9]$")

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


def create_secure_pw(length: int) -> str:

    if length < 4:
        raise ValueError("Password must be at least 4 characters")

    letters = string.ascii_letters
    signs = ['#', '+', '$']

    num_letters = length - 2
    pw_letters = [random.choice(letters) for _ in range(num_letters)]

    pw_letters.insert(random.randint(0, num_letters), random.choice(signs))
    pw_letters.insert(random.randint(0, num_letters + 1), random.choice(signs))

def print_error(msg):
    return '<tr><td colspan="2"><font color="red">{0}</font></td></tr>\n'.format(msg)

def print_msg(title, msg):
    return '<tr><td>{0}</td><td>{1}</td></tr>\n'.format(title,msg)

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