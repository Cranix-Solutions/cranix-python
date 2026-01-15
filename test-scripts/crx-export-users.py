#!/usr/bin/python3

import json
import sys
import os
sys.path.append('..')
import cranix

role=sys.argv[1]

users=cranix.get_users(role)

with open(role+".csv", 'w') as fp:
    fp.write("uid;givenName;surName;classes;birthDay\n")
    for key, user in users:
        fp.write("{};{};{};{};{}\n".format(user['uid'],user['givenName'],user['surName'],user['classes'],user['birthDay']))
