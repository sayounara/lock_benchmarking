#!/usr/bin/python

import sys
import os
import datetime
import subprocess
import re
import sys
from os.path import join
import shutil
import multiprocessing


bin_dir_path = os.path.dirname(os.path.realpath(__file__))

sys.argv.pop(0)

lock_subfix = sys.argv.pop(0)

result = ''

print lock_subfix

print sys.argv

if len(sys.argv) == 0:
    subprocess.call(['perf', 
                     'record',
                     '-g',
                     join(bin_dir_path, 'rw_bench_clone_' + lock_subfix), 
                     str(multiprocessing.cpu_count()), 
                     '0.8',
                     '10',
                     '4',
                     '4',
                     '0'])
else:
    subprocess.call(['perf',
                     'record',
                     '-g',
                     join(bin_dir_path, 'rw_bench_clone_' + lock_subfix)] + sys.argv)

out_dir = 'perf_data'

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

the_date = datetime.datetime.now().strftime("%Y.%m.%d.%H.%M.%S")

out_file = join(out_dir, 'perf.data_' + the_date + result)

shutil.copy2('perf.data', out_file)

print "The profile data can be found in the file: " + out_file

print ""

print "Analyze modules:  perf report --stdio -g none --sort comm,dso -i " + out_file

print ""

print "Analyze functions:  perf report --stdio -g none -i " + out_file + " | c++filt"

print ""

print "Analyze call graph:  perf report --stdio -g graph -i " + out_file + " | c++filt"
