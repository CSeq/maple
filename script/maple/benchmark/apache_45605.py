import os
import time
import subprocess
import psutil
from maple.core import config
from maple.core import logging
from maple.core import testing

class Client(object):
    def __init__(self, input_entry):
        self.input_entry = input_entry
    def start(self):
        uri_idx = self.input_entry
        test_args = []
        test_args.append(config.benchmark_home('apache_45605') + '/test2/trigger-con' + '%d.sh' % uri_idx)
	test_args.append('0')
        logging.msg('client %d start\n' % uri_idx)
	#logging.msg('%s\n' % test_args)
        self.fnull = open(os.devnull, 'w')
        self.proc = subprocess.Popen(test_args, stdout=self.fnull, stderr=self.fnull)
    def join(self):
        uri_idx = self.input_entry
        #logging.msg('client %d wait\n' % uri_idx)
        #self.proc.wait()
        self.proc.terminate()
        self.fnull.close()
        self.proc = None
        self.fnull = None
        logging.msg('client %d terminate\n' % uri_idx)
        #logging.msg('client %d done\n' % uri_idx)

class Test(testing.ServerTest):
    def __init__(self, input_idx):
        testing.ServerTest.__init__(self, input_idx)
        self.add_input(([0, 1, 2, 3], True))
    def setup(self):
        if os.path.exists(self.pid_file()):
            os.remove(self.pid_file())
        f = open(self.log_file(), 'w')
        f.close()
    def start(self):
        start_cmd = []
        if self.prefix != None:
            start_cmd.extend(self.prefix)
        start_cmd.append(self.bin())
        start_cmd.extend(['-k', 'start', '-D', 'ONE_PROCESS'])
	#start_cmd.extend(['-k', 'start'])
        ipt, buf = self.input()
        if buf == True:
            start_cmd.extend(['-f', self.conf_file()])
        logging.msg('starting server for apache_45605\n')
        self.server = subprocess.Popen(start_cmd)
        while not os.path.exists(self.pid_file()):
            time.sleep(1)
        p = psutil.Process(self.server.pid)
	logging.msg('num_threads = %d\n' % p.get_num_threads())
        while p.get_num_threads() != 5:
            time.sleep(1)
            logging.msg('num_threads = %d\n' % p.get_num_threads())
        time.sleep(1)
    def stop(self):
        p = psutil.Process(self.server.pid)
	logging.msg('cpu_percent = %d\n' % p.get_cpu_percent())
        while p.get_cpu_percent() > 5.0:
            time.sleep(1)
            logging.msg('cpu_percent = %d\n' % p.get_cpu_percent())
        time.sleep(1)
        stop_cmd = []
        stop_cmd.append(self.bin())
        stop_cmd.extend(['-k', 'stop'])
        logging.msg('stopping server for apache_45605\n')
        subprocess.call(stop_cmd)
        self.server.wait()
        self.server = None
    def kill(self):
        self.stop()
    def issue(self):
        clients = []
        ipt, buf = self.input()
        for idx in range(len(ipt)):
            clients.append(Client(ipt[idx]))
        logging.msg('issuing requests for apache_45605\n')
        for i in range(len(clients)):
            clients[i].start()
	time.sleep(10)
        for i in range(len(clients)):
            clients[i].join()
    def home(self):
        return config.benchmark_home('apache_45605')
    def bin(self):
        return self.home() + '/bin/httpd'
    def pid_file(self):
        return self.home() + '/logs/httpd.pid'
    def log_file(self):
        return self.home() + '/logs/access_log'
    def error_file(self):
        return self.home() + '/logs/error_log'
    def conf_file(self):
        return self.home() + '/conf/httpd.conf'
    def check_offline(self):
        s = os.stat(self.error_file())
        if s.st_size != 0:
            return True
        else:
            return False

def get_test(input_idx='default'):
    return Test(input_idx)

