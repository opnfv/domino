#
# Autogenerated by Thrift Compiler (0.9.3)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TException, TApplicationException
from ttypes import *

HEART_BEAT = 1
REGISTER = 2
REGISTER_RESPONSE = 3
SUBSCRIBE = 4
SUBSCRIBE_RESPONSE = 5
PUBLISH = 6
PUBLISH_RESPONSE = 7
PUSH = 8
PUSH_RESPONSE = 9
QUERY = 10
QUERY_RESPONSE = 11
SUCCESS = 1
FAILED = 2
APPEND = 0
OVERWRITE = 1
DELETE = 2

THRIFT_RPC_TIMEOUT_MS = 1000

str2enum = {"APPEND":APPEND, "OVERWRITE":OVERWRITE, "DELETE":DELETE}
