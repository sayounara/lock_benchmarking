from collections import OrderedDict
import multiprocessing

import sys
sys.path.append('../src/lock')
sys.path.append('src/lock')
from extract_numa_structure import numa_structure_defines


############
#Definitions
############

Import('mode')
std_cc_flags = ['-std=gnu99',
                '-Wall',
                '-pthread']

std_link_flags = ['-pthread']

debug_flags = ['-O1',
               '-g']

optimization_flags = ['-O3']

profile_flags = ['-fno-omit-frame-pointer -O2']

if(mode=='debug'):
    std_cc_flags = std_cc_flags + debug_flags
    std_link_flags = std_link_flags + debug_flags
elif(mode=='profile'):
    std_cc_flags = std_cc_flags + profile_flags
    std_link_flags = std_link_flags + profile_flags
else:
    std_cc_flags = std_cc_flags + optimization_flags
    std_link_flags = std_link_flags + optimization_flags

env = Environment(
    CCFLAGS = ' '.join(std_cc_flags),
    LINKFLAGS = ' '.join(std_link_flags),
    CPPPATH = ['.',
               'src/lock',
               'src/datastructures',
               'src/tests',
               'src/utils',
               'src/benchmark/skiplist'])

num_of_cores_str=str(multiprocessing.cpu_count())

rg_define = ('NUMBER_OF_READER_GROUPS',num_of_cores_str)

#For partitioned ticket lock
array_size_define = ('ARRAY_SIZE',num_of_cores_str)

object_multi_writers_queue = env.Object("src/datastructures/multi_writers_queue.c")

lock_infos = OrderedDict([
        ('sdw',        {'source'      : 'simple_delayed_writers_lock',
                        'defines'     : [rg_define],
                        'exe_defines' : ['LOCK_TYPE_SimpleDelayedWritesLock', 
                                         rg_define],
                        'lock_deps'   : [],
                        'other_deps'  : [object_multi_writers_queue]}),
        ('aer',        {'source'      : 'all_equal_rdx_lock',
                        'defines'     : [rg_define],
                        'exe_defines' : ['LOCK_TYPE_AllEqualRDXLock',
                                         rg_define],
                        'lock_deps'   : [],
                        'other_deps'  : [object_multi_writers_queue]}),
        ('mcs',        {'source'      : 'mcs_lock',
                        'defines'     : [],
                        'exe_defines' : ['LOCK_TYPE_MCSLock'],
                        'lock_deps'   : [],
                        'other_deps'  : []}),
        ('drmcs',      {'source'      : 'wprw_lock',
                        'defines'     : ['LOCK_TYPE_MCSLock',
                                         'LOCK_TYPE_WPRW_MCSLock',
                                         rg_define],
                        'exe_defines' : ['LOCK_TYPE_WPRWLock',
                                         'LOCK_TYPE_WPRW_MCSLock',
                                         rg_define],
                        'lock_deps'   : ['mcs'],
                        'other_deps'  : []}),
        ('ticket',     {'source'      : 'ticket_lock',
                        'defines'     : [],
                        'exe_defines' : ['LOCK_TYPE_TicketLock'],
                        'lock_deps'   : [],
                        'other_deps'  : []}),
        ('aticket',    {'source'      : 'aticket_lock',
                        'defines'     : [array_size_define],
                        'exe_defines' : ['LOCK_TYPE_ATicketLock',
                                         array_size_define],
                        'lock_deps'   : [],
                        'other_deps'  : []}),
        ('cohort',     {'source'      : 'cohort_lock',
                        'defines'     : [array_size_define] + numa_structure_defines(),
                        'exe_defines' : ['LOCK_TYPE_CohortLock', 
                                         array_size_define] + numa_structure_defines(),
                        'lock_deps'   : ['ticket','aticket'],
                        'other_deps'  : []}),
        ('wprwcohort', {'source'      : 'wprw_lock',
                        'defines'     : ['LOCK_TYPE_CohortLock', 
                                         'LOCK_TYPE_WPRW_CohortLock', 
                                         array_size_define, 
                                         rg_define] + numa_structure_defines(),
                        'exe_defines' : ['LOCK_TYPE_WPRWLock', 
                                         'LOCK_TYPE_WPRW_CohortLock', 
                                         array_size_define, 
                                         rg_define]  + numa_structure_defines(),
                        'lock_deps'   : ['cohort'],
                        'other_deps'  : []})])


lock_specific_object_defs = OrderedDict([
        ('test',             {'source'      : 'src/tests/test_rdx_lock.c',
                              'defines'     : []}),
        ('rw_bench_clone',   {'source'      : 'src/benchmark/rw_bench_clone.c',
                             'defines'     : ['RW_BENCH_CLONE']}),
        ('rw_bench_memtrans',{'source'      : 'src/benchmark/rw_bench_clone.c',
                              'defines'     : ['RW_BENCH_MEM_TRANSFER']})])


#Located in src/benchmark/
benchmarks_scripts = ['compare_benchmarks.py',
                      'benchmark_lock.py',
                      'run_benchmarks_on_intel_i7.py',
                      'run_benchmarks_on_sandy.py']

#Located in src/profile/
profile_scripts = ['profile_perf.py']

#################
#Generate objects
#################

def create_lock_specific_object(lock_id, lock_specific_object_def_id):
    definition = lock_specific_object_defs[lock_specific_object_def_id]
    return env.Object(
        target = lock_specific_object_def_id + '_' + lock_id + '.o',
        source = definition['source'],
        CPPDEFINES = lock_infos[lock_id]['exe_defines'] + definition['defines'])

for lock_id in lock_infos:
    lock_info = lock_infos[lock_id]
    other_deps = lock_info['other_deps']
    for lock_dep in lock_info['lock_deps']:
        other_deps.append(lock_infos[lock_dep]['obj'])
        other_deps.append(lock_infos[lock_dep]['other_deps'])
    lock_info['obj'] = env.Object(
        target = lock_info['source'] + lock_id + '.o',
        source = 'src/lock/' + lock_info['source'] + '.c',
        CPPDEFINES=lock_info['defines'])
    for lock_specific_object_def_id in lock_specific_object_defs:
        lock_info[lock_specific_object_def_id] = ( 
            create_lock_specific_object(lock_id,
                                        lock_specific_object_def_id))


##############
#Link programs
##############

def create_lock_specific_program(lock_id, lock_specific_object_def_id):
    lock_info = lock_infos[lock_id]
    return env.Program(
        target = lock_specific_object_def_id + '_' + lock_id,
        source = ([lock_info[lock_specific_object_def_id], 
                  lock_info['obj']] + 
                  lock_info['other_deps']))

for lock_id in lock_infos:
    for lock_specific_object_def_id in lock_specific_object_defs:
        create_lock_specific_program(lock_id,
                                     lock_specific_object_def_id)


env.Program(
    target = 'test_multi_writers_queue',
    source = ['src/tests/test_multi_writers_queue.c',
              object_multi_writers_queue])

#############
#Copy scripts
#############

for benchmarks_script in benchmarks_scripts:
    Command(benchmarks_script, 
            'src/benchmark/' + benchmarks_script, 
            Copy("$TARGET", "$SOURCE"))


if(mode=='profile'):
    for profile_script in profile_scripts:
        Command(profile_script, 
                'src/profile/' + profile_script, 
                Copy("$TARGET", "$SOURCE"))