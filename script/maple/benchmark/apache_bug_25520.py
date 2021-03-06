"""Copyright 2011 The University of Michigan

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Authors - Jie Yu (jieyu@umich.edu)

Modified by DKeeper at 2013.11.22
"""

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
        uri_idx, num_calls = self.input_entry
        httperf_args = []
        httperf_args.append(config.benchmark_home('httperf') + '/bin/httperf')
        #httperf_args.append('--server=localhost')
        httperf_args.append('--server=DKeeper')
        httperf_args.append('--port=80')
        httperf_args.append('--uri=/test/%d.txt' % uri_idx)
        httperf_args.append('--num-calls=%d' % num_calls)
        httperf_args.append('--num-conns=1')
        logging.msg('client: uri_idx=%d, num_calls=%d\n' % (uri_idx, num_calls))
        self.fnull = open(os.devnull, 'w')
        self.proc = subprocess.Popen(httperf_args, stdout=self.fnull, stderr=self.fnull)
    def join(self):
        uri_idx, num_calls = self.input_entry
        logging.msg('client %d join\n' % uri_idx)
        self.proc.wait()
        self.fnull.close()
        self.proc = None
        self.fnull = None
        logging.msg('client %d done\n' % uri_idx)

class Test(testing.ServerTest):
    def __init__(self, input_idx):
        testing.ServerTest.__init__(self, input_idx)
        #input format: ([(uri_idx, num_calls), ...], buffer)
        self.add_input(([(1, 10), (1, 10)], True))
        #self.add_input(([(1, 50), (1, 30)], False))
        #self.add_input(([(1, 50)], True))
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
        logging.msg('starting server for apache_bug_25520\n')
        self.server = subprocess.Popen(start_cmd)
        while not os.path.exists(self.pid_file()):
            time.sleep(1)
        p = psutil.Process(self.server.pid)
	logging.msg('threads_num = %d\n' % p.get_num_threads())
        while p.get_num_threads() != 4:
            time.sleep(1)
	logging.msg('threads_num = %d\n' % p.get_num_threads())
        time.sleep(1)
    def stop(self):
        p = psutil.Process(self.server.pid)
        while p.get_cpu_percent() > 5.0:
            time.sleep(1)
        time.sleep(1)
        stop_cmd = []
        stop_cmd.append(self.bin())
        stop_cmd.extend(['-k', 'stop'])
        logging.msg('stopping server for apache_bug_25520\n')
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
        logging.msg('issuing requests for apache_bug_25520\n')
        for i in range(len(clients)):
            clients[i].start()
        for i in range(len(clients)):
            clients[i].join()
    def home(self):
        return config.benchmark_home('apache_bug_25520')
    def bin(self):
        return self.home() + '/bin/httpd'
    def pid_file(self):
        return self.home() + '/logs/httpd.pid'
    def log_file(self):
        return self.home() + '/logs/access_log'
    def conf_file(self):
        return self.home() + '/conf/httpd.conf'
#        return self.home() + '/conf/httpd.conf.buffer'
    def check_offline(self):
        s = os.stat(self.log_file())
#        if s.st_size != 1560:
        logging.msg('size of access_log = %d\n' % s.st_size)
        if s.st_size != 1520:
            return True
        else:
            return False

def get_test(input_idx='default'):
    return Test(input_idx)

