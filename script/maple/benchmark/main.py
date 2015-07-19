import os
from maple.core import logging
from maple.core import proto

def iroot_pb2():
    return proto.module('idiom.iroot_pb2')

def main(argv):
    if len(argv) < 1:
        logging.err(command_usage())
    db_name = argv[0]
    pro = iroot_pb2().iRootDBProto()
    if not os.path.exists(db_name):
        return
    f = open(db_name, 'rb')
    pro.ParseFromString(f.read())
    logging.msg('performing command: %s ...\n' % command, 2) 
