#!/usr/bin/python3.13

import sys

sys.path.append('../')
from  cranix import *


users = get_users('students')
print('There are {0} students in the school'.format(len(users)))
print('This is a secure password {0}'.format(create_secure_pw()))
print('This is a bad uid "a" {0}:'.format(check_uid('a')))
print('Good date time 20220405 {0}:'.format(read_birthday('20220405')))
print('Bad date time 220405 {0}:'.format(read_birthday('220405')))

