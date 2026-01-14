import json
import sys
import os

from ..python import _init_functions

role=sys.argv[1]

users=read_users(role)

with open(role+".csv", 'w') as fp:
    fp.write("uid;givenName;surName;classes;birthDay\n")
    for user in users:
        fp.write("{};{};{};{};{}\n".format(user['uid'],user['givenName'],user['surName'],user['classes'],user['birthDay']))