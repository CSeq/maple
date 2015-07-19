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
"""

##==============================================================
import time
import random
import string
import shutil
##==============================================================
import os
import sys
import subprocess
import optparse
from maple.core import config
from maple.core import logging
from maple.core import pintool
from maple.core import static_info
from maple.core import testing
from maple.pct import history as pct_history
from maple.race import pintool as race_pintool
from maple.idiom import iroot
from maple.idiom import memo
from maple.idiom import history as idiom_history
from maple.idiom import pintool as idiom_pintool
from maple.idiom import offline_tool as idiom_offline_tool
from maple.idiom import testing as idiom_testing

# global variables
_separator = '---'

def get_prefix(pin, tool=None):
    c = []
    c.append(pin.pin())
    c.extend(pin.options())
    if tool != None:
        c.extend(tool.options())
    c.append('--')
    return c

def separate_opt_prog(argv):
    if not _separator in argv:
        return argv, []
    else:
        opt_argv = argv[0:argv.index(_separator)]
        prog_argv = argv[argv.index(_separator)+1:]
        return opt_argv, prog_argv

def __display_image_table(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    sinfo.display_image_table(output)

def __display_inst_table(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    sinfo.display_inst_table(output)

def __display_iroot_db(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    iroot_db.display(output)

def __display_memo_exposed_set(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_db.display_exposed_set(output)

def __display_memo_summary(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_db.display_summary(output)

def __display_test_history(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    test_history = idiom_history.TestHistory(sinfo, iroot_db)
    test_history.load(options.test_history)
    test_history.display(output)

def __display_test_history_summary(output, options):
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    history = idiom_history.TestHistory(sinfo, iroot_db)
    history.load(options.test_history)
    history.display_summary(output)

def __display_pct_history(output, options):
    history = pct_history.History()
    history.load(options.pct_history)
    history.display(output)

def __display_pct_history_summary(output, options):
    history = pct_history.History()
    history.load(options.pct_history)
    history.display_summary(output)

def valid_display_set():
    result = set()
    for name in dir(sys.modules[__name__]):
        idx = name.find('__display_')
        if idx != -1:
            result.add(name[idx+10:])
    return result

def valid_display(display):
    return display in valid_display_set()

def display_usage():
    usage = 'usage: <script> display [options] <object>\n\n'
    usage += 'valid objects are:\n'
    for display in valid_display_set():
        usage += '  %s\n' % display
    return usage

def register_display_options(parser):
    parser.add_option(
            '-i', '--input',
            action='store',
            type='string',
            dest='input',
            default='stdin',
            metavar='PATH',
            help='the input file name')
    parser.add_option(
            '-o', '--output',
            action='store',
            type='string',
            dest='output',
            default='stdout',
            metavar='PATH',
            help='the output file name')
    parser.add_option(
            '--sinfo_in',
            action='store',
            type='string',
            dest='sinfo_in',
            default='sinfo.db',
            metavar='PATH',
            help='the input static info database path')
    parser.add_option(
            '--sinfo_out',
            action='store',
            type='string',
            dest='sinfo_out',
            default='sinfo.db',
            metavar='PATH',
            help='the output static info database path')
    parser.add_option(
            '--iroot_in',
            action='store',
            type='string',
            dest='iroot_in',
            default='iroot.db',
            metavar='PATH',
            help='the input iroot database path')
    parser.add_option(
            '--iroot_out',
            action='store',
            type='string',
            dest='iroot_out',
            default='iroot.db',
            metavar='PATH',
            help='the output iroot database path')
    parser.add_option(
            '--memo_in',
            action='store',
            type='string',
            dest='memo_in',
            default='memo.db',
            metavar='PATH',
            help='the input memoization database path')
    parser.add_option(
            '--memo_out',
            action='store',
            type='string',
            dest='memo_out',
            default='memo.db',
            metavar='PATH',
            help='the output memoization database path')
    parser.add_option(
            '--test_history',
            action='store',
            type='string',
            dest='test_history',
            default='test.histo',
            metavar='PATH',
            help='the test history path')
    parser.add_option(
            '--pct_history',
            action='store',
            type='string',
            dest='pct_history',
            default='pct.histo',
            metavar='PATH',
            help='the PCT history path')

def __command_display(argv):
    parser = optparse.OptionParser(display_usage())
    register_display_options(parser)
    (options, args) = parser.parse_args(argv)
    if len(args) != 1 or not valid_display(args[0]):
        parser.print_help()
        sys.exit(0)
    # open output
    if options.output == 'stdout':
        output = sys.stdout
    elif options.output == 'stderr':
        output = sys.stderr
    else:
        output = open(options.output, 'w')
    # write output
    eval('__display_%s(output, options)' % args[0])
    # close output
    if options.output == 'stdout':
        pass
    elif options.output == 'stderr':
        pass
    else:
        output.close()

def __modify_memo_input_change(options):
    if not os.path.exists(options.memo_in):
        return
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_db.clear_predicted_set()
    memo_db.clear_candidate_map()
    memo_db.save(options.memo_out)
    logging.msg('memo input change done!\n')

def __modify_memo_mark_unexposed_failed(options):
    if not os.path.exists(options.memo_in):
        return
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_db.mark_unexposed_failed()
    memo_db.save(options.memo_out)
    logging.msg('memo mark unexposed failed done!\n')

def __modify_memo_refine_candidate(options):
    if not os.path.exists(options.memo_in):
        return
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_db.refine_candidate()
    memo_db.save(options.memo_out)
    logging.msg('memo refine candidate done!\n')

def __modify_memo_merge(options):
    if not os.path.exists(options.memo_in):
        return
    if not os.path.exists(options.memo_merge_in):
        return
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_merge_db = memo.Memo(sinfo, iroot_db)
    memo_merge_db.load(options.memo_merge_in)
    memo_db.merge(memo_merge_db)
    memo_db.save(options.memo_out)
    logging.msg('memo merge done!\n')

def __modify_memo_apply(options):
    if not os.path.exists(options.memo_in):
        return
    if not os.path.exists(options.memo_merge_in):
        return
    sinfo = static_info.StaticInfo()
    sinfo.load(options.sinfo_in)
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load(options.iroot_in)
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load(options.memo_in)
    memo_merge_db = memo.Memo(sinfo, iroot_db)
    memo_merge_db.load(options.memo_merge_in)
    memo_db.merge(memo_merge_db)
    memo_db.refine_candidate()
    memo_db.save(options.memo_out)
    logging.msg('memo apply done!\n')

def valid_modify_set():
    result = set()
    for name in dir(sys.modules[__name__]):
        idx = name.find('__modify_')
        if idx != -1:
            result.add(name[idx+9:])
    return result

def valid_modify(modify):
    return modify in valid_modify_set()

def modify_usage():
    usage = 'usage: <script> modify [options] <object>\n\n'
    usage += 'valid objects are:\n'
    for modify in valid_modify_set():
        usage += '  %s\n' % modify
    return usage

def register_modify_options(parser):
    parser.add_option(
            '--sinfo_in',
            action='store',
            type='string',
            dest='sinfo_in',
            default='sinfo.db',
            metavar='PATH',
            help='the input static info database path')
    parser.add_option(
            '--sinfo_out',
            action='store',
            type='string',
            dest='sinfo_out',
            default='sinfo.db',
            metavar='PATH',
            help='the output static info database path')
    parser.add_option(
            '--iroot_in',
            action='store',
            type='string',
            dest='iroot_in',
            default='iroot.db',
            metavar='PATH',
            help='the input iroot database path')
    parser.add_option(
            '--iroot_out',
            action='store',
            type='string',
            dest='iroot_out',
            default='iroot.db',
            metavar='PATH',
            help='the output iroot database path')
    parser.add_option(
            '--memo_in',
            action='store',
            type='string',
            dest='memo_in',
            default='memo.db',
            metavar='PATH',
            help='the input memoization database path')
    parser.add_option(
            '--memo_out',
            action='store',
            type='string',
            dest='memo_out',
            default='memo.db',
            metavar='PATH',
            help='the output memoization database path')
    parser.add_option(
            '--memo_merge_in',
            action='store',
            type='string',
            dest='memo_merge_in',
            default='memo_merge.db',
            metavar='PATH',
            help='the to-merge memoization database path')
    parser.add_option(
            '--no_memo_failed',
            action='store_false',
            dest='memo_failed',
            default=True,
            help='whether memorize fail-to-expose iroots')

def __command_modify(argv):
    parser = optparse.OptionParser(modify_usage())
    register_modify_options(parser)
    (options, args) = parser.parse_args(argv)
    if len(args) != 1 or not valid_modify(args[0]):
        parser.print_help()
        sys.exit(0)
    eval('__modify_%s(options)' % args[0])

def register_profile_cmdline_options(parser, prefix=''):
    parser.add_option(
            '--%smode' % prefix,
            action='store',
            type='string',
            dest='%smode' % prefix,
            default='runout',
            metavar='MODE',
            help='the profile mode: runout, timeout, stable')
    parser.add_option(
            '--%sthreshold' % prefix,
            action='store',
            type='int',
            dest='%sthreshold' % prefix,
            default=1,
            metavar='N',
            help='the threshold (depends on mode)')

def __command_profile(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_defaults['enable_observer_new'] = True
    profiler.knob_defaults['enable_predictor_new'] = True
    # parse cmdline options
    usage = 'usage: <script> profile [options] --- program'
    parser = optparse.OptionParser(usage)
    register_profile_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.ProfileTestCase(test,
                                             options.mode,
                                             options.threshold,
                                             profiler)
    testcase.run()

def register_active_cmdline_options(parser, prefix=''):
    parser.add_option(
            '--%smode' % prefix,
            action='store',
            type='string',
            dest='%smode' % prefix,
            default='runout',
            metavar='MODE',
            help='the active mode: runout, timeout, finish')
    parser.add_option(
            '--%sthreshold' % prefix,
            action='store',
            type='int',
            dest='%sthreshold' % prefix,
            default=1,
            metavar='N',
            help='the threshold (depends on mode)')

def __command_active(argv):
    pin = pintool.Pin(config.pin_home())
    scheduler = idiom_pintool.Scheduler()
    # parse cmdline options
    usage = 'usage: <script> active [options] --- program'
    parser = optparse.OptionParser(usage)
    register_active_cmdline_options(parser)
    scheduler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    scheduler.set_cmdline_options(options, args)
    # run active test
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, scheduler))
    testcase = idiom_testing.ActiveTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            scheduler)
    testcase.run()

def register_random_cmdline_options(parser, prefix=''):
    parser.add_option(
            '--%smode' % prefix,
            action='store',
            type='string',
            dest='%smode' % prefix,
            default='runout',
            metavar='MODE',
            help='the active mode: runout, timeout')
    parser.add_option(
            '--%sthreshold' % prefix,
            action='store',
            type='int',
            dest='%sthreshold' % prefix,
            default=1,
            metavar='N',
            help='the threshold (depends on mode)')

def __command_native(argv):
    # parse cmdline options
    usage = 'usage: <script> native [options] --- program'
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    # run profile
    test = testing.InteractiveTest(prog_argv)
    testcase = idiom_testing.NativeTestCase(test,
                                            options.mode,
                                            options.threshold)
    testcase.run()

def __command_pinbase(argv):
    pin = pintool.Pin(config.pin_home())
    # parse cmdline options
    usage = 'usage: <script> pinbase [options] --- program'
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    # run profile
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin))
    testcase = idiom_testing.NativeTestCase(test,
                                            options.mode,
                                            options.threshold)
    testcase.run()

def __command_pct(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_defaults['strict'] = True
    # parse cmdline options
    usage = 'usage: <script> pct [options] --- program'
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.RandomTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            profiler)
    testcase.run()

def __command_pct_large(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    # parse cmdline options
    usage = 'usage: <script> pct_large [options] --- program'
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.RandomTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            profiler)
    testcase.run()

def __command_rand_delay(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.RandSchedProfiler()
    profiler.knob_defaults['delay'] = True
    # parse cmdline options
    usage = 'usage: <script> rand_delay [options] --- program'
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.RandomTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            profiler)
    testcase.run()

def register_chess_cmdline_options(parser, prefix=''):
    parser.add_option(
            '--%smode' % prefix,
            action='store',
            type='string',
            dest='%smode' % prefix,
            default='finish',
            metavar='MODE',
            help='the active mode: finish, runout, timeout')
    parser.add_option(
            '--%sthreshold' % prefix,
            action='store',
            type='int',
            dest='%sthreshold' % prefix,
            default=1,
            metavar='N',
            help='the threshold (depends on mode)')

def __command_chess(argv):
    pin = pintool.Pin(config.pin_home())
    controller = idiom_pintool.ChessProfiler()
    controller.knob_defaults['enable_chess_scheduler'] = True
    controller.knob_defaults['enable_observer_new'] = True
    # parse cmdline options
    usage = 'usage: <script> chess [options] --- program'
    parser = optparse.OptionParser(usage)
    register_chess_cmdline_options(parser)
    controller.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    controller.set_cmdline_options(options, args)
    # run chess
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, controller))
    testcase = idiom_testing.ChessTestCase(test,
                                           options.mode,
                                           options.threshold,
                                           controller)
    testcase.run()

def register_race_cmdline_options(parser, prefix=''):
    parser.add_option(
            '--%smode' % prefix,
            action='store',
            type='string',
            dest='%smode' % prefix,
            default='runout',
            metavar='MODE',
            help='the race detector mode: runout, timeout, stable')
    parser.add_option(
            '--%sthreshold' % prefix,
            action='store',
            type='int',
            dest='%sthreshold' % prefix,
            default=1,
            metavar='N',
            help='the threshold (depends on mode)')

def __command_chess_race(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = race_pintool.PctProfiler()
    profiler.knob_prefix = 'race_'
    profiler.knob_defaults['enable_djit'] = True
    profiler.knob_defaults['ignore_lib'] = True
    profiler.knob_defaults['track_racy_inst'] = True
    controller = idiom_pintool.ChessProfiler()
    controller.knob_prefix = 'chess_'
    controller.knob_defaults['enable_chess_scheduler'] = True
    controller.knob_defaults['enable_observer_new'] = True
    controller.knob_defaults['sched_race'] = True
    # parse cmdline options
    usage = 'usage: <script> chess_race [options] --- program'
    parser = optparse.OptionParser(usage)
    register_race_cmdline_options(parser, 'race_')
    profiler.register_cmdline_options(parser)
    register_chess_cmdline_options(parser, 'chess_')
    controller.register_cmdline_options(parser)
    parser.set_defaults(race_mode='stable')
    parser.set_defaults(race_threshold=3)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    controller.set_cmdline_options(options, args)
    # create race testcase
    race_test = testing.InteractiveTest(prog_argv)
    race_test.set_prefix(get_prefix(pin, profiler))
    race_testcase = idiom_testing.RaceTestCase(race_test,
                                               options.race_mode,
                                               options.race_threshold,
                                               profiler)
    # create chess testcase
    chess_test = testing.InteractiveTest(prog_argv)
    chess_test.set_prefix(get_prefix(pin, controller))
    chess_testcase = idiom_testing.ChessTestCase(chess_test,
                                                 options.chess_mode,
                                                 options.chess_threshold,
                                                 controller)
    # run
    testcase = idiom_testing.ChessRaceTestCase(race_testcase,
                                               chess_testcase)
    testcase.run()

def __command_default(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_prefix = 'profile_'
    profiler.knob_defaults['enable_observer_new'] = True
    profiler.knob_defaults['enable_predictor_new'] = True
    scheduler = idiom_pintool.Scheduler()
    scheduler.knob_prefix = 'active_'
    # parse cmdline options
    usage = 'usage: <script> default [options] --- program'
    parser = optparse.OptionParser(usage)
    register_profile_cmdline_options(parser, 'profile_')
    profiler.register_cmdline_options(parser)
    register_active_cmdline_options(parser, 'active_')
    scheduler.register_cmdline_options(parser)
    parser.set_defaults(profile_mode='stable')
    parser.set_defaults(profile_threshold=3)
    parser.set_defaults(active_mode='finish')
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    scheduler.set_cmdline_options(options, args)
    # create profile testcase
    profile_test = testing.InteractiveTest(prog_argv)
    profile_test.set_prefix(get_prefix(pin, profiler))
    profile_testcase = idiom_testing.ProfileTestCase(profile_test,
                                                     options.profile_mode,
                                                     options.profile_threshold,
                                                     profiler)
    # create active testcase
    active_test = testing.InteractiveTest(prog_argv)
    active_test.set_prefix(get_prefix(pin, scheduler))
    active_testcase = idiom_testing.ActiveTestCase(active_test,
                                                   options.active_mode,
                                                   options.active_threshold,
                                                   scheduler)
    # run idiom testcase
    idiom_testcase = idiom_testing.IdiomTestCase(profile_testcase,
                                                 active_testcase)
    idiom_testcase.run()

def valid_benchmark_set():
    result = set()
    path = config.pkg_home() + '/script/maple/benchmark'
    for f in os.listdir(path):
        if f.endswith('.py'):
            if f != '__init__.py':
                result.add(f[:-3])
    return result

def valid_benchmark(bench):
    return bench in valid_benchmark_set()

def benchmark_usage():
    usage = 'valid benchmarks are:\n'
    for bench in valid_benchmark_set():
        usage += '  %s\n' % bench
    return usage

def __command_profile_script(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_defaults['enable_observer_new'] = True
    profiler.knob_defaults['enable_predictor_new'] = True
    # parse cmdline options
    usage = 'usage: <script> profile_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_profile_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.ProfileTestCase(test,
                                             options.mode,
                                             options.threshold,
                                             profiler) 
    testcase.run()

def __command_active_script(argv):
    pin = pintool.Pin(config.pin_home())
    scheduler = idiom_pintool.Scheduler()
    # parse cmdline options
    usage = 'usage: <script> active_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_active_cmdline_options(parser)
    scheduler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    scheduler.set_cmdline_options(options, args)
    # run active test
    __import__('maple.benchmark.%s' % bench_name)
    bench_mod = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench_mod.get_test(input_idx)
    test.set_prefix(get_prefix(pin, scheduler))
    testcase = idiom_testing.ActiveTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            scheduler)
    testcase.run()

def __command_native_script(argv):
    # parse cmdline options
    usage = 'usage: <script> native_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    # run profile
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    testcase = idiom_testing.NativeTestCase(test,
                                            options.mode,
                                            options.threshold) 
    testcase.run()

def __command_pinbase_script(argv):
    pin = pintool.Pin(config.pin_home())
    # parse cmdline options
    usage = 'usage: <script> pinbase_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    # run profile
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    test.set_prefix(get_prefix(pin))
    testcase = idiom_testing.NativeTestCase(test,
                                            options.mode,
                                            options.threshold) 
    testcase.run()

def __command_pct_script(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_defaults['strict'] = True
    # parse cmdline options
    usage = 'usage: <script> pct_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.RandomTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            profiler) 
    testcase.run()

def __command_pct_large_script(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    # parse cmdline options
    usage = 'usage: <script> pct_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.RandomTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            profiler) 
    testcase.run()

def __command_rand_delay_script(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.RandSchedProfiler()
    profiler.knob_defaults['delay'] = True
    # parse cmdline options
    usage = 'usage: <script> rand_delay_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_random_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    # run profile
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.RandomTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            profiler) 
    testcase.run()

def __command_chess_script(argv):
    pin = pintool.Pin(config.pin_home())
    controller = idiom_pintool.ChessProfiler()
    controller.knob_defaults['enable_chess_scheduler'] = True
    controller.knob_defaults['enable_observer_new'] = True
    # parse cmdline options
    usage = 'usage: <script> chess_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_chess_cmdline_options(parser)
    controller.register_cmdline_options(parser)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    controller.set_cmdline_options(options, args)
    # run chess
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    test = bench.get_test(input_idx)
    test.set_prefix(get_prefix(pin, controller))
    testcase = idiom_testing.ChessTestCase(test,
                                           options.mode,
                                           options.threshold,
                                           controller) 
    testcase.run()

def __command_chess_race_script(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = race_pintool.PctProfiler()
    profiler.knob_prefix = 'race_'
    profiler.knob_defaults['enable_djit'] = True
    profiler.knob_defaults['ignore_lib'] = True
    profiler.knob_defaults['track_racy_inst'] = True
    controller = idiom_pintool.ChessProfiler()
    controller.knob_prefix = 'chess_'
    controller.knob_defaults['enable_chess_scheduler'] = True
    controller.knob_defaults['enable_observer_new'] = True
    controller.knob_defaults['sched_race'] = True
    # parse cmdline options
    usage = 'usage: <script> chess_race_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_race_cmdline_options(parser, 'race_')
    profiler.register_cmdline_options(parser)
    register_chess_cmdline_options(parser, 'chess_')
    controller.register_cmdline_options(parser)
    parser.set_defaults(race_mode='stable')
    parser.set_defaults(race_threshold=3)
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    controller.set_cmdline_options(options, args)
    # create race testcase
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    race_test = bench.get_test(input_idx)
    race_test.set_prefix(get_prefix(pin, profiler))
    race_testcase = idiom_testing.RaceTestCase(race_test,
                                               options.race_mode,
                                               options.race_threshold,
                                               profiler)
    # create chess testcase
    chess_test = bench.get_test(input_idx)
    chess_test.set_prefix(get_prefix(pin, controller))
    chess_testcase = idiom_testing.ChessTestCase(chess_test,
                                                 options.chess_mode,
                                                 options.chess_threshold,
                                                 controller)
    # run
    testcase = idiom_testing.ChessRaceTestCase(race_testcase,
                                               chess_testcase)
    testcase.run()

def __command_default_script(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_prefix = 'profile_'
    profiler.knob_defaults['enable_observer_new'] = True
    profiler.knob_defaults['enable_predictor_new'] = True
    scheduler = idiom_pintool.Scheduler()
    scheduler.knob_prefix = 'active_'
    # parse cmdline options
    usage = 'usage: <script> default_script [options] --- <bench name> <input index>\n\n'
    usage += benchmark_usage()
    parser = optparse.OptionParser(usage)
    register_profile_cmdline_options(parser, 'profile_')
    profiler.register_cmdline_options(parser)
    register_active_cmdline_options(parser, 'active_')
    scheduler.register_cmdline_options(parser)
    parser.set_defaults(profile_mode='stable')
    parser.set_defaults(profile_threshold=3)
    parser.set_defaults(active_mode='finish')
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 1:
        bench_name = prog_argv[0]
        input_idx = 'default'
    elif len(prog_argv) == 2:
        bench_name = prog_argv[0]
        input_idx = prog_argv[1]
    else:
        parser.print_help()
        sys.exit(0)
    if not valid_benchmark(bench_name):
        logging.err('invalid benchmark name\n')
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    scheduler.set_cmdline_options(options, args)
    # create profile testcase
    __import__('maple.benchmark.%s' % bench_name)
    bench = sys.modules['maple.benchmark.%s' % bench_name]
    profile_test = bench.get_test(input_idx)
    profile_test.set_prefix(get_prefix(pin, profiler))
    profile_testcase = idiom_testing.ProfileTestCase(profile_test,
                                                     options.profile_mode,
                                                     options.profile_threshold,
                                                     profiler)
    # create active testcase
    active_test = bench.get_test(input_idx)
    active_test.set_prefix(get_prefix(pin, scheduler))
    active_testcase = idiom_testing.ActiveTestCase(active_test,
                                                   options.active_mode,
                                                   options.active_threshold,
                                                   scheduler)
    # run idiom testcase
    idiom_testcase = idiom_testing.IdiomTestCase(profile_testcase,
                                                 active_testcase)
    idiom_testcase.run()

def __command_memo_tool(argv):
    usage = 'usage: <script> memo_tool --operation=OP [options]'
    parser = optparse.OptionParser(usage)
    memo_tool = idiom_offline_tool.MemoTool()
    memo_tool.register_cmdline_options(parser)
    (options, args) = parser.parse_args(argv)
    memo_tool.set_cmdline_options(options, args)
    memo_tool.call()

def valid_command_set():
    result = set()
    for name in dir(sys.modules[__name__]):
        idx = name.find('__command_')
        if idx != -1:
            result.add(name[idx+10:])
    return result

def valid_command(command):
    return command in valid_command_set()

def command_usage():
    usage =  'usage: <script> <command> [options] [args]\n\n'
    usage += 'valid commands are:\n'
    for command in valid_command_set():
        usage += '  %s\n' % command
    return usage
    
    
##==============================================================
## Start
##==============================================================

WRONG_TIME = 0
NUM_ACTIVE = 0
MAX_ACTIVE = 0
MIN_ACTIVE = 99
IS_FATAL = False

_MIN_NUM = 99
_CHOSEN_SET = set()


_wrong_edge = 89
_num_of_candidate_testcase = 4
_rand_upper = 100
_rand_lower = -99
_is_remove = True
_is_update_memo = True
_is_fatal = False


def __command_my_profile(argv):
    pin = pintool.Pin(config.pin_home())
    profiler = idiom_pintool.PctProfiler()
    profiler.knob_defaults['enable_observer_new'] = True
    profiler.knob_defaults['enable_predictor_new'] = True
    ### parse cmdline options
    usage = 'usage: <script> profile [options] --- program'
    parser = optparse.OptionParser(usage)
    register_profile_cmdline_options(parser)
    profiler.register_cmdline_options(parser)
    
    parser.set_defaults(mode='stable')
    parser.set_defaults(threshold=2)
    parser.set_defaults(ignore_lib=True)
    #parser.set_defaults(complex_idioms=True)

    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    profiler.set_cmdline_options(options, args)
    ### run profile
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, profiler))
    testcase = idiom_testing.ProfileTestCase(test,
                                             options.mode,
                                             options.threshold,
                                             profiler)
    testcase.run()
    
def __command_my_active(argv):
    pin = pintool.Pin(config.pin_home())
    scheduler = idiom_pintool.Scheduler()
    ### parse cmdline options
    usage = 'usage: <script> active [options] --- program'
    parser = optparse.OptionParser(usage)
    register_active_cmdline_options(parser)
    scheduler.register_cmdline_options(parser)
    
    parser.set_defaults(mode='finish')
    #parser.set_defaults(complex_idioms=True)
    
    (opt_argv, prog_argv) = separate_opt_prog(argv)
    if len(prog_argv) == 0:
        parser.print_help()
        sys.exit(0)
    (options, args) = parser.parse_args(opt_argv)
    scheduler.set_cmdline_options(options, args)
    ### run active test
    test = testing.InteractiveTest(prog_argv)
    test.set_prefix(get_prefix(pin, scheduler))
    testcase = idiom_testing.ActiveTestCase(test,
                                            options.mode,
                                            options.threshold,
                                            scheduler)
    testcase.run()
    
    if testcase.is_fatal():
        global IS_FATAL
        IS_FATAL = True


def __command_my_test(argv):
    start_time = time.time()
    if not os.path.isfile("testcase2.txt"):
        logging.err("testcase file not exists!!\n")
        
    all_candidate_set = set()            # memo.myCandidate; testcase with its candidate iroots
    all_exposed_set = set()              # memo.myIRoot; all exposed iroots  (from memo.myMemo.exposed_set)
    all_failed_set = set()               # memo.myIRoot; all failed iroots  (from memo.myMemo.failed_set)
    all_predicted_set = set()            # memo.myIRoot; all predicted iroots  (from memo.myMemo.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRoot; all shadow_exposed iroots  (from memo.myMemo.shadow_exposed_set)

    f = open("testcase2.txt")
    
    ### profile
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        directory = "MyTest_%s" % "_".join(test_case)
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        os.mkdir(directory)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        ### update all_candidate_set, and all memo set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        my_candidate = memo.myCandidate(memo_db, test_case)
        #print "this_candidate_map length = %d" % len(my_candidate.candidate_map)
        all_candidate_set.add(my_candidate)
        os.chdir("..")
    f.close()
    
    ### active
    while len(all_candidate_set) != 0:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### choose a testcase
        (best_testcase, max_count, id_set) = get_best_testcase(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set)
        print "best testcase is %s : count = %d" % (best_testcase, max_count)
        if max_count == 0:
            for aset in all_candidate_set:
                directory = "MyTest_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        directory = "MyTest_%s" % "_".join(best_testcase)
        os.chdir(directory)
        ### remove exposed_iroots from candidate_map{}
        if _is_update_memo:
            update_memo(all_exposed_set, all_failed_set, all_shadow_exposed_set)
        eval('__command_my_active(argv + best_testcase)')
        update_memo_mark_unexposed_failed()
        ### update all_exposed_set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        ### remove the tested testcase from all_candidate_set
        for aset in all_candidate_set:
            if aset.test_case == best_testcase:
                all_candidate_set.remove(aset)
                break
        id_set.clear()
        os.chdir("..")
        if _is_remove:
            os.system('rm -rf %s' % directory)
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                for aset in all_candidate_set:
                    directory = "MyTest_%s" % "_".join(aset.test_case)
                    if _is_remove:
                        os.system('rm -rf %s' % directory)
                all_candidate_set.clear()
                break
        
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    #for iroot_info in all_exposed_set:
    #    print str(iroot_info)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    
def __command_my_test_gen(argv):
    start_time = time.time()
    
    all_candidate_set = set()            # memo.myCandidate; testcase with its candidate iroots
    all_exposed_set = set()              # memo.myIRoot; all exposed iroots  (from memo.myMemo.exposed_set)
    all_failed_set = set()               # memo.myIRoot; all failed iroots  (from memo.myMemo.failed_set)
    all_predicted_set = set()            # memo.myIRoot; all predicted iroots  (from memo.myMemo.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRoot; all shadow_exposed iroots  (from memo.myMemo.shadow_exposed_set)
    
    testcase_list = list()               # readline.split(); all testcase
    chosen_list = list()                 # readline.split(); chosen testcase
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if test_case != None:
            testcase_list.append(test_case)
    
    f = open("testcase.txt")
    
    ### profile
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        directory = "MyTestGen_%s" % "_".join(test_case)
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        os.mkdir(directory)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        ### update all_candidate_set, testcase_list, and all memo set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        my_candidate = memo.myCandidate(memo_db, test_case)
        all_candidate_set.add(my_candidate)
        os.chdir("..")
    f.close()
    
    count = 0
    pre_predicted_num = 0
    
    ### active
    while len(all_candidate_set) != 0:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### choose a testcase
        (best_testcase, max_count, id_set) = get_best_testcase(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set)
        print "best testcase is %s : count = %d" % (best_testcase, max_count)
        if max_count == 0:
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        chosen_list.append(best_testcase)
        directory = "MyTestGen_%s" % "_".join(best_testcase)
        os.chdir(directory)
        ### remove exposed_iroots from candidate_map{}
        if _is_update_memo:
            update_memo(all_exposed_set, all_failed_set, all_shadow_exposed_set)
        eval('__command_my_active(argv + best_testcase)')
        update_memo_mark_unexposed_failed()
        ### update all_exposed_set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        ### remove the tested testcase from all_candidate_set
        for aset in all_candidate_set:
            if aset.test_case == best_testcase:
                all_candidate_set.remove(aset)
                break
        id_set.clear()
        os.chdir("..")
        if _is_remove:
            os.system('rm -rf %s' % directory)
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                for aset in all_candidate_set:
                    directory = "MyTestGen_%s" % "_".join(aset.test_case)
                    if _is_remove:
                        os.system('rm -rf %s' % directory)
                all_candidate_set.clear()
                break
        
        if len(all_predicted_set) == pre_predicted_num:
            count += 1
        else:
            pre_predicted_num = len(all_predicted_set)
            count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change in 4 tests, then stop testing
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        
        ### generate a new testcase and do profile
        new_testcase = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if new_testcase != None:
            directory = "MyTestGen_%s" % "_".join(new_testcase)
            if os.path.exists(directory):
                logging.err("%s already existed!!!\n" % directory)
                return
            os.mkdir(directory)
            os.chdir(directory)
            eval('__command_my_profile(argv + new_testcase)')
            ### update all_candidate_set, testcase_list, and all memo set
            sinfo = static_info.StaticInfo()
            sinfo.load("sinfo.db")
            iroot_db = iroot.iRootDB(sinfo)
            iroot_db.load("iroot.db")
            memo_db = memo.Memo(sinfo, iroot_db)
            memo_db.load("memo.db")
            my_memo = memo.myMemo(memo_db)
            for my_iroot in my_memo.exposed_set:
                if not is_in_set(my_iroot, all_exposed_set):
                    all_exposed_set.add(my_iroot)
            for my_iroot in my_memo.failed_set:
                if not is_in_set(my_iroot, all_failed_set):
                    all_failed_set.add(my_iroot)
            for my_iroot in my_memo.predicted_set:
                if not is_in_set(my_iroot, all_predicted_set):
                    all_predicted_set.add(my_iroot)
            for my_iroot in my_memo.shadow_exposed_set:
                if not is_in_set(my_iroot, all_shadow_exposed_set):
                    all_shadow_exposed_set.add(my_iroot)
            print "exposed_set length        = %d" % len(all_exposed_set)
            print "failed_set length         = %d" % len(all_failed_set)
            print "predicted_set length      = %d" % len(all_predicted_set)
            if len(all_shadow_exposed_set) != 0:
                print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
            my_candidate = memo.myCandidate(memo_db, new_testcase)
            all_candidate_set.add(my_candidate)
            testcase_list.append(new_testcase)
            os.chdir("..")
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    global WRONG_TIME
    global NUM_ACTIVE
    NUM_ACTIVE += len(chosen_list)
    global MAX_ACTIVE
    global MIN_ACTIVE
    if len(chosen_list)>MAX_ACTIVE:
        MAX_ACTIVE = len(chosen_list)
    if len(chosen_list)<MIN_ACTIVE:
        MIN_ACTIVE = len(chosen_list)
        
    if _is_fatal:
        if IS_FATAL==False:
            WRONG_TIME += 1
    else:
        if len(all_predicted_set) < _wrong_edge:
            WRONG_TIME += 1



def update_memo(all_exposed_set, all_failed_set, all_shadow_exposed_set):
    sinfo = static_info.StaticInfo()
    sinfo.load("sinfo.db")
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load("iroot.db")
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load("memo.db")
    memo_db.my_update("memo.db", all_exposed_set, all_failed_set, all_shadow_exposed_set)

def update_memo_mark_unexposed_failed():
    sinfo = static_info.StaticInfo()
    sinfo.load("sinfo.db")
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load("iroot.db")
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load("memo.db")
    memo_db.mark_unexposed_failed()
    memo_db.save("memo.db")
    #logging.msg('memo mark unexposed failed done!\n')


def get_best_testcase(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set):
    max_count = 0
    best_testcase = None
    id_set = set()
    current_set = set()
    for aset in all_candidate_set:
        count = 0
        current_set.clear()
        for candidate_id in aset.candidate_map.keys():
            if not is_in_set(aset.candidate_map[candidate_id], all_exposed_set):
                if not is_in_set(aset.candidate_map[candidate_id], all_failed_set):
                        if not is_in_set(aset.candidate_map[candidate_id], all_shadow_exposed_set):
                            count += 1
                            current_set.add(candidate_id)
        print "%s : count = %d" % (aset.test_case, count) 
        if count > max_count:
            max_count = count
            best_testcase = aset.test_case
            id_set.clear()
            id_set |= current_set
    print "id_set = %s" % str(id_set)
    return (best_testcase, max_count, id_set)

#====
def get_fit_testcase(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set):
    max_count = 0
    best_testcase = None
    id_set = set()
    current_set = set()
    whole_set = all_exposed_set | all_failed_set | all_shadow_exposed_set
    for aset in all_candidate_set:
        count = 0
        current_set.clear()
        for candidate_id in aset.candidate_map.keys():
            if not is_in_set(aset.candidate_map[candidate_id], whole_set):
                count += 1
                current_set.add(candidate_id)
        print "%s : count = %d" % (aset.test_case, count) 
        if count > max_count:
            max_count = count
            best_testcase = aset.test_case
            id_set.clear()
            id_set |= current_set
    print "id_set = %s" % str(id_set)
    return (best_testcase, max_count, id_set)
#====


def event_equal(e1, e2):
    if e1.type != e2.type:
        return False
    if e1.inst_offset != e2.inst_offset:
        return False
    return True

def is_in_set(myMemo_info, myIRoot_set):
    if len(myIRoot_set) == 0:
        return False
    for myI in myIRoot_set:
        if myMemo_info.idiom == myI.idiom:
            length = len(myMemo_info.event_list)
            count = 0
            for idx in range(length):
                if event_equal(myI.event_list[idx], myMemo_info.event_list[idx]):
                    count += 1
                else:
                    break
            if count == length:
                return True
    return False

def is_in_testcase(t, t_list):
    length = len(t_list)
    if length == 0:
        return False
    s = " ".join(t)
    for idx in range(length):
        if cmp(s, " ".join(t_list[idx])) == 0:
            return True
    return False

def gen_int(a, b):
    return random.randint(a, b)

def gen_string(length=8,chars=string.ascii_letters+string.digits):
    return ''.join([random.choice(chars) for i in range(length)])

def gen_testcase(a, b, testcase_list):
    i = 0
    while 1:
        int1 = gen_int(a, b)
        int2 = gen_int(a, b)
        line = str(int1) + " " + str(int2)
        testcase = line.split()
        if is_in_testcase(testcase, testcase_list):        # if cann't create new testcase for 3 times, then stop and return None
            if i < 3:
                i += 1
                continue
            return None
        else:
            f = open("testcase.txt", "a")
            f.write(line)
            f.write("\n")
            f.close()
            return testcase

def gen_testcase_splash(a, b):
    i = 0
    int1 = gen_int(a, b)
    int2 = gen_int(a, b)
    int3 = gen_int(a, b)
    int4 = gen_int(a, b)
    
    l1_num = (int1 + 99) * 1000 + 50000
    l1 = "-n" + str(l1_num)
    
    if int2>0:
        l2 = "-t"
    else:
        l2 = ""
    
    if int3>0:
        l3 = "-p2"
    else:
        l3 = "-p4"
        
    if int4>50:
        l4 = "-r1024"
    elif int4>0:
        l4 = "-r512"
    elif int4>-50:
        l4 = "-r256"
    else:
        l4 = "-r2048"
    
    line = l1 + " " + l2 + " " + l3 + " " +l4
    testcase = line.split()
    f = open("testcase.txt", "a")
    f.write(line)
    f.write("\n")
    f.close()
    return testcase













def __command_my_old(argv):
    start_time = time.time()
    if not os.path.isfile("testcase.txt"):
        logging.err("testcase file not exists!!\n")
    all_exposed_set = set()    # memo.myMemo.exposed_set
    f = open("testcase2.txt")
    directory = "MyOld"
    if os.path.exists(directory):
        logging.err("%s already existed!!!\n" % directory)
        return
    os.mkdir(directory)
    os.chdir(directory)
    
    while 1:
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        eval('__command_my_profile(argv + test_case)')
        eval('__command_my_active(argv + test_case)')
        
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        
        my_memo = memo.myMemo(memo_db)
        for exp in my_memo.exposed_set:
            if not is_in_set(exp, all_exposed_set):
                all_exposed_set.add(exp)
        print "exposed_set length = %d" % len(all_exposed_set)
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                break
        
    os.chdir("..")
    f.close()
    if _is_remove:
        os.system('rm -rf %s' % directory)
    
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    

def __command_my_rand(argv):
    start_time = time.time()
    if not os.path.isfile("testcase2.txt"):
        logging.err("testcase file not exists!!\n")
        
    all_candidate_set = set()            # memo.myCandidate; testcase with its candidate iroots
    all_exposed_set = set()              # memo.myIRoot; all exposed iroots  (from memo.myMemo.exposed_set)
    all_failed_set = set()               # memo.myIRoot; all failed iroots  (from memo.myMemo.failed_set)
    all_predicted_set = set()            # memo.myIRoot; all predicted iroots  (from memo.myMemo.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRoot; all shadow_exposed iroots  (from memo.myMemo.shadow_exposed_set)
    
    f = open("testcase2.txt")
    
    while 1:
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        directory = "MyRand_%s" % "_".join(test_case)
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        os.mkdir(directory)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        if _is_update_memo:
            update_memo(all_exposed_set, all_failed_set, all_shadow_exposed_set)
        eval('__command_my_active(argv + test_case)')
        update_memo_mark_unexposed_failed()
        
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        
        os.chdir("..")
        if _is_remove:
            os.system('rm -rf %s' % directory)
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                break
    f.close()

    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"

def __command_my_rand_gen(argv):
    start_time = time.time()
    
    all_exposed_set = set()              # memo.myIRoot; all exposed iroots  (from memo.myMemo.exposed_set)
    all_failed_set = set()               # memo.myIRoot; all failed iroots  (from memo.myMemo.failed_set)
    all_predicted_set = set()            # memo.myIRoot; all predicted iroots  (from memo.myMemo.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRoot; all shadow_exposed iroots  (from memo.myMemo.shadow_exposed_set)
    
    testcase_list = list()     # readline.split(); all testcase
    chosen_list = list()         # readline.split(); chosen testcase
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if test_case != None:
            testcase_list.append(test_case)
    
    index = 0
    count = 0
    pre_predicted_num = 0
    
    ### profile and active
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        test_case = testcase_list[index]
        directory = "MyRandGen_%s" % "_".join(test_case)
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        chosen_list.append(test_case)
        os.mkdir(directory)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        if _is_update_memo:
            update_memo(all_exposed_set, all_failed_set, all_shadow_exposed_set)
        eval('__command_my_active(argv + test_case)')
        update_memo_mark_unexposed_failed()
        ### update all_exposed_set and testcase_list
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        os.chdir("..")
        if _is_remove:
            os.system('rm -rf %s' % directory)
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                break
        if len(all_predicted_set) == pre_predicted_num:
            count += 1
        else:
            pre_predicted_num = len(all_predicted_set)
            #count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change for 4 times totally, then stop testing
            break
        ### generate new testcase
        new_testcase = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if new_testcase != None:
            testcase_list.append(new_testcase)
        index += 1
        if index == len(testcase_list):  # if there's no testcases, then stop testing
            break
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    global WRONG_TIME
    global NUM_ACTIVE
    NUM_ACTIVE += len(chosen_list)
    global MAX_ACTIVE
    global MIN_ACTIVE
    if len(chosen_list)>MAX_ACTIVE:
        MAX_ACTIVE = len(chosen_list)
    if len(chosen_list)<MIN_ACTIVE:
        MIN_ACTIVE = len(chosen_list)
    
    if _is_fatal:
        if IS_FATAL==False:
            WRONG_TIME += 1
    else:
        if len(all_predicted_set) < _wrong_edge:
            WRONG_TIME += 1





def __command_my_test_gen_10(argv):
    start_time = time.time()
    global _CHOSEN_SET
    global _MIN_NUM
    for i in range(1000):
        if _is_fatal:
            global IS_FATAL
            IS_FATAL = False
        _CHOSEN_SET.clear()
        _MIN_NUM = 99
        print "##### No.%d test ####### start" % (i+1)
        eval('__command_my_test_gen(argv)')
        print "##### No.%d test ####### end" % (i+1)
    global WRONG_TIME
    global NUM_ACTIVE
    global MAX_ACTIVE
    global MIN_ACTIVE
    print "actvs : %d" % NUM_ACTIVE
    print "max_act:%d" % MAX_ACTIVE
    print "min_act:%d" % MIN_ACTIVE
    print "wrong : %d" % WRONG_TIME
    end_time = time.time()
    print "total time : %f" % (end_time - start_time)

def __command_my_test_genp_10(argv):
    start_time = time.time()
    global _CHOSEN_SET
    global _MIN_NUM
    for i in range(1000):
        if _is_fatal:
            global IS_FATAL
            IS_FATAL = False
        _CHOSEN_SET.clear()
        _MIN_NUM = 99
        print "##### No.%d test ####### start" % (i+1)
        eval('__command_my_test_genp(argv)')
        print "##### No.%d test ####### end" % (i+1)
    global WRONG_TIME
    global NUM_ACTIVE
    global MAX_ACTIVE
    global MIN_ACTIVE
    print "actvs : %d" % NUM_ACTIVE
    print "max_act:%d" % MAX_ACTIVE
    print "min_act:%d" % MIN_ACTIVE
    print "wrong : %d" % WRONG_TIME
    end_time = time.time()
    print "total time : %f" % (end_time - start_time)

def __command_my_rand_gen_10(argv):
    start_time = time.time()
    for i in range(1000):
        if _is_fatal:
            global IS_FATAL
            IS_FATAL = False
        print "##### No.%d test ####### start" % (i+1)
        eval('__command_my_rand_gen(argv)')
        print "##### No.%d test ####### end" % (i+1)
    global WRONG_TIME
    global NUM_ACTIVE
    global MAX_ACTIVE
    global MIN_ACTIVE
    print "actvs : %d" % NUM_ACTIVE
    print "max_act:%d" % MAX_ACTIVE
    print "min_act:%d" % MIN_ACTIVE
    print "wrong : %d" % WRONG_TIME
    end_time = time.time()
    print "total time : %f" % (end_time - start_time)















def __command_my_test_genp(argv):
    start_time = time.time()
    
    all_candidate_set = set()            # memo.myCandidatep; testcase with its candidate iroots
    all_exposed_set = set()              # memo.myIRootp; all exposed iroots  (from memo.myMemop.exposed_set)
    all_failed_set = set()               # memo.myIRootp; all failed iroots  (from memo.myMemop.failed_set)
    all_predicted_set = set()            # memo.myIRootp; all predicted iroots  (from memo.myMemop.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRootp; all shadow_exposed iroots  (from memo.myMemop.shadow_exposed_set)
    
    testcase_list = list()               # readline.split(); all testcase
    chosen_list = list()                 # readline.split(); chosen testcase
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if test_case != None:
            testcase_list.append(test_case)
    
    f = open("testcase.txt")
    last_dir = ""
    
    ### profile
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        directory = "MyTestGen_%s" % "_".join(test_case)
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        os.mkdir(directory)
        if os.path.exists(last_dir):
            dirS1 = last_dir + "/sinfo.db"
            dirS2 = directory + "/sinfo.db"
            shutil.copyfile(dirS1, dirS2)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        ### update all_candidate_set, testcase_list, and all memo set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemop(memo_db)
        all_exposed_set |= my_memo.exposed_set
        all_failed_set |= my_memo.failed_set
        all_predicted_set |= my_memo.predicted_set
        all_shadow_exposed_set |= my_memo.shadow_exposed_set
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        my_candidate = memo.myCandidatep(memo_db, test_case)
        all_candidate_set.add(my_candidate)
        os.chdir("..")
        last_dir = directory
    f.close()
    
    count = 0
    pre_predicted_num = 0
    
    ### active
    global _CHOSEN_SET
    global _MIN_NUM
    while len(all_candidate_set) != 0:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### choose a testcase
        (best_testcase, max_count) = get_best_testcasep(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set)
        print "best testcase is %s : count = %d" % (best_testcase, max_count)
        if max_count == 0:
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        chosen_list.append(best_testcase)
        directory = "MyTestGen_%s" % "_".join(best_testcase)
        os.chdir(directory)
        ### remove exposed_iroots from candidate_map{}
        if _is_update_memo:
            update_memop(all_exposed_set, all_failed_set, all_shadow_exposed_set)
        eval('__command_my_active(argv + best_testcase)')
        update_memo_mark_unexposed_failed()
        ### update all_exposed_set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemop(memo_db)
        all_exposed_set |= my_memo.exposed_set
        all_failed_set |= my_memo.failed_set
        all_predicted_set |= my_memo.predicted_set
        all_shadow_exposed_set |= my_memo.shadow_exposed_set
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        ### remove the tested testcase from all_candidate_set
        for aset in all_candidate_set:
            if aset.test_case == best_testcase:
                all_candidate_set.remove(aset)
                #
                _CHOSEN_SET.remove(aset)
                _MIN_NUM -= 1
                #
                break
        os.chdir("..")
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                os.system('rm -rf %s' % directory)
                for aset in all_candidate_set:
                    directory = "MyTestGen_%s" % "_".join(aset.test_case)
                    if _is_remove:
                        os.system('rm -rf %s' % directory)
                all_candidate_set.clear()
                break
        active_dir = directory
        
        if len(all_predicted_set) == pre_predicted_num:
            count += 1
        else:
            pre_predicted_num = len(all_predicted_set)
            count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change in 4 tests, then stop testing
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        
        ### generate a new testcase and do profile
        new_testcase = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if new_testcase != None:
            directory = "MyTestGen_%s" % "_".join(new_testcase)
            if os.path.exists(directory):
                logging.err("%s already existed!!!\n" % directory)
                return
            os.mkdir(directory)
            dirS1 = last_dir + "/sinfo.db"
            dirS2 = directory + "/sinfo.db"
            shutil.copyfile(dirS1, dirS2)
            if _is_remove:
                os.system('rm -rf %s' % active_dir)
            os.chdir(directory)
            eval('__command_my_profile(argv + new_testcase)')
            ### update all_candidate_set, testcase_list, and all memo set
            sinfo = static_info.StaticInfo()
            sinfo.load("sinfo.db")
            iroot_db = iroot.iRootDB(sinfo)
            iroot_db.load("iroot.db")
            memo_db = memo.Memo(sinfo, iroot_db)
            memo_db.load("memo.db")
            my_memo = memo.myMemop(memo_db)
            all_exposed_set |= my_memo.exposed_set
            all_failed_set |= my_memo.failed_set
            all_predicted_set |= my_memo.predicted_set
            all_shadow_exposed_set |= my_memo.shadow_exposed_set
            print "exposed_set length        = %d" % len(all_exposed_set)
            print "failed_set length         = %d" % len(all_failed_set)
            print "predicted_set length      = %d" % len(all_predicted_set)
            if len(all_shadow_exposed_set) != 0:
                print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
            my_candidate = memo.myCandidatep(memo_db, new_testcase)
            all_candidate_set.add(my_candidate)
            #
            _CHOSEN_SET.add(my_candidate)
            _MIN_NUM += 1
            #
            testcase_list.append(new_testcase)
            os.chdir("..")
            last_dir = directory
        else:
            if _is_remove:
                os.system('rm -rf %s' % active_dir)
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    print "predicted_set = %s" % str(all_predicted_set)
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    global WRONG_TIME
    global NUM_ACTIVE
    NUM_ACTIVE += len(chosen_list)
    global MAX_ACTIVE
    global MIN_ACTIVE
    if len(chosen_list)>MAX_ACTIVE:
        MAX_ACTIVE = len(chosen_list)
    if len(chosen_list)<MIN_ACTIVE:
        MIN_ACTIVE = len(chosen_list)
    
    if _is_fatal:
        if IS_FATAL==False:
            WRONG_TIME += 1
    else:
        if len(all_predicted_set) < _wrong_edge:
            WRONG_TIME += 1






def __command_my_rand_genp(argv):
    start_time = time.time()
    
    all_exposed_set = set()              # memo.myIRootp; all exposed iroots  (from memo.myMemop.exposed_set)
    all_failed_set = set()               # memo.myIRootp; all failed iroots  (from memo.myMemop.failed_set)
    all_predicted_set = set()            # memo.myIRootp; all predicted iroots  (from memo.myMemop.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRootp; all shadow_exposed iroots  (from memo.myMemop.shadow_exposed_set)
    
    testcase_list = list()               # readline.split(); all testcase
    chosen_list = list()                 # readline.split(); chosen testcase
    
    last_dir = ""
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if test_case != None:
            testcase_list.append(test_case)
    
    index = 0
    count = 0
    pre_predicted_num = 0
    
    ### profile and active
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        test_case = testcase_list[index]
        directory = "MyRandGen_%s" % "_".join(test_case)
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        chosen_list.append(test_case)
        os.mkdir(directory)
        if os.path.exists(last_dir):
            dirS1 = last_dir + "/sinfo.db"
            dirS2 = directory + "/sinfo.db"
            shutil.copyfile(dirS1, dirS2)
            if _is_remove:
                os.system('rm -rf %s' % last_dir)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        if _is_update_memo:
            update_memop(all_exposed_set, all_failed_set, all_shadow_exposed_set)
        eval('__command_my_active(argv + test_case)')
        update_memo_mark_unexposed_failed()
        ### update all_exposed_set and testcase_list
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemop(memo_db)
        all_exposed_set |= my_memo.exposed_set
        all_failed_set |= my_memo.failed_set
        all_predicted_set |= my_memo.predicted_set
        all_shadow_exposed_set |= my_memo.shadow_exposed_set
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        os.chdir("..")
        if len(all_predicted_set) == pre_predicted_num:
            count += 1
        else:
            pre_predicted_num = len(all_predicted_set)
            #count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change for 4 times totally, then stop testing
            if _is_remove:
                os.system('rm -rf %s' % directory)
            break
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                if _is_remove:
                    os.system('rm -rf %s' % directory)
                break
        ### generate new testcase
        new_testcase = gen_testcase(_rand_lower, _rand_upper, testcase_list)
        if new_testcase != None:
            testcase_list.append(new_testcase)
        index += 1
        if index == len(testcase_list):  # if there's no testcases, then stop testing
            if _is_remove:
                os.system('rm -rf %s' % directory)
            break
        last_dir = directory
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    global WRONG_TIME
    global NUM_ACTIVE
    NUM_ACTIVE += len(chosen_list)
    global MAX_ACTIVE
    global MIN_ACTIVE
    if len(chosen_list)>MAX_ACTIVE:
        MAX_ACTIVE = len(chosen_list)
    if len(chosen_list)<MIN_ACTIVE:
        MIN_ACTIVE = len(chosen_list)
    
    if _is_fatal:
        if IS_FATAL==False:
            WRONG_TIME += 1
    else:
        if len(all_predicted_set) < _wrong_edge:
            WRONG_TIME += 1



#_MIN_NUM = 99
#_CHOSEN_SET = set()

def get_best_testcasep(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set):
    best_testcase = None
    current_set = set()
    chosen_set = set()
    new_set = set()
    whole_set = all_exposed_set | all_failed_set | all_shadow_exposed_set
    for aset in all_candidate_set:
        current_set.clear()
        current_set = aset.candidate_set - whole_set
        new_set |= current_set
    ggeett(all_candidate_set, chosen_set, new_set, 0)
    
    max_count = 0
    global _MIN_NUM
    global _CHOSEN_SET
    for aset in _CHOSEN_SET:
        count = len(aset.candidate_set - whole_set)
        print "%s : count = %d" % (aset.test_case, count) 
        if count > max_count:
            max_count = count
            best_testcase = aset.test_case
    print "_MIN_NUM = %d" % _MIN_NUM
    print "_CHOSEN_LEN = %d" % len(_CHOSEN_SET)
    return (best_testcase, max_count)

def ggeett(candidate_set, chosen_set, new_set, min_count):
    #print "len cand_set = %d" % len(candidate_set)
    #print "len chos_set = %d" % len(chosen_set)
    #print "len new_set = %d" % len(new_set)
    #print "min_count = %d" % min_count
    global _MIN_NUM
    global _CHOSEN_SET
    #print "_MIN_NUM = %d" % _MIN_NUM
    #print "==========="
    if len(new_set)==0:
        if min_count<_MIN_NUM:
            _MIN_NUM = min_count
            _CHOSEN_SET.clear()
            _CHOSEN_SET |= chosen_set
    elif min_count < _MIN_NUM:
        for aset in candidate_set:
            curr_new = new_set - aset.candidate_set
            if len(curr_new) < len(new_set):
                curr_candidate = set(candidate_set)
                curr_candidate.remove(aset)
                curr_chosen = set(chosen_set)
                curr_chosen.add(aset)
                ggeett(curr_candidate, curr_chosen, curr_new, min_count+1)
    

def get_best_testcasep_backup(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set):
    max_count = 0
    best_testcase = None
    current_set = set()
    max_set = set()
    whole_set = all_exposed_set | all_failed_set | all_shadow_exposed_set
    for aset in all_candidate_set:
        current_set.clear()
        current_set = aset.candidate_set - whole_set
        count = len(current_set)
        print "%s : count = %d" % (aset.test_case, count) 
        if count > max_count:
            max_count = count
            best_testcase = aset.test_case
            max_set.clear()
            max_set |= current_set
    #print("max_set = %s" % str(max_set))
    return (best_testcase, max_count)
'''
def is_in_setp(myMemo_info_int, myIRoot_set):
    if myMemo_info_int in myIRoot_set:
        return True
    return False
'''
def update_memop(all_exposed_set, all_failed_set, all_shadow_exposed_set):
    sinfo = static_info.StaticInfo()
    sinfo.load("sinfo.db")
    iroot_db = iroot.iRootDB(sinfo)
    iroot_db.load("iroot.db")
    memo_db = memo.Memo(sinfo, iroot_db)
    memo_db.load("memo.db")
    memo_db.my_updatep("memo.db", all_exposed_set, all_failed_set, all_shadow_exposed_set)












NUM_IROOT = 0



def __command_my_rand_pro(argv):
    start_time = time.time()
    
    all_pro_set = set()
    
    testcase_list = list()     # readline.split(); all testcase
    chosen_list = list()         # readline.split(); chosen testcase
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase_splash(_rand_lower, _rand_upper)
        if test_case != None:
            testcase_list.append(test_case)
    
    index = 0
    count = 0
    pre_pro_num = 0
    
    ### profile and active
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        test_case = testcase_list[index]
        directory = "MyRandGen_SP"
        if os.path.exists(directory):
            logging.err("%s already existed!!!\n" % directory)
            return
        chosen_list.append(test_case)
        os.mkdir(directory)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')

        ### update all_exposed_set and testcase_list
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_pro_set):
                all_pro_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_pro_set):
                all_pro_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_pro_set):
                all_pro_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_pro_set):
                all_pro_set.add(my_iroot)
        print "profile_set length        = %d" % len(all_pro_set)

        os.chdir("..")
        if _is_remove:
            os.system('rm -rf %s' % directory)
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                break
        if len(all_pro_set) == pre_pro_num:
            count += 1
        else:
            pre_pro_num = len(all_pro_set)
            #count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change for 4 times totally, then stop testing
            break
        ### generate new testcase
        new_testcase = gen_testcase_splash(_rand_lower, _rand_upper)
        if new_testcase != None:
            testcase_list.append(new_testcase)
        index += 1
        if index == len(testcase_list):  # if there's no testcases, then stop testing
            break
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    global NUM_ACTIVE
    global NUM_IROOT
    NUM_ACTIVE += len(chosen_list)
    NUM_IROOT += len(all_pro_set)





def __command_my_test_pro(argv):
    start_time = time.time()
    
    all_candidate_set = set()            # memo.myCandidate; testcase with its candidate iroots
    all_exposed_set = set()              # memo.myIRoot; all exposed iroots  (from memo.myMemo.exposed_set)
    all_failed_set = set()               # memo.myIRoot; all failed iroots  (from memo.myMemo.failed_set)
    all_predicted_set = set()            # memo.myIRoot; all predicted iroots  (from memo.myMemo.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRoot; all shadow_exposed iroots  (from memo.myMemo.shadow_exposed_set)
    
    testcase_list = list()               # readline.split(); all testcase
    chosen_list = list()                 # readline.split(); chosen testcase
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase_splash(_rand_lower, _rand_upper)
        if test_case != None:
            testcase_list.append(test_case)
    
    f = open("testcase.txt")
    
    ### profile
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        directory = "MyTestGen_%s" % "_".join(test_case)
        if not os.path.exists(directory):
            os.mkdir(directory)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        ### update all_candidate_set, testcase_list, and all memo set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_failed_set):
                all_failed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_predicted_set):
                all_predicted_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_shadow_exposed_set):
                all_shadow_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        my_candidate = memo.myCandidate(memo_db, test_case)
        all_candidate_set.add(my_candidate)
        os.chdir("..")
    f.close()
    
    count = 0
    pre_predicted_num = 0
    
    ### active
    while len(all_candidate_set) != 0:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### choose a testcase
        (best_testcase, max_count, id_set) = get_best_testcase(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set)
        print "best testcase is %s : count = %d" % (best_testcase, max_count)
        if max_count == 0:
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        chosen_list.append(best_testcase)
        directory = "MyTestGen_%s" % "_".join(best_testcase)
        os.chdir(directory)

        ### update all_exposed_set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemo(memo_db)
        for my_iroot in my_memo.exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.failed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.predicted_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        for my_iroot in my_memo.shadow_exposed_set:
            if not is_in_set(my_iroot, all_exposed_set):
                all_exposed_set.add(my_iroot)
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        ### remove the tested testcase from all_candidate_set
        for aset in all_candidate_set:
            if aset.test_case == best_testcase:
                all_candidate_set.remove(aset)
                break
        id_set.clear()
        os.chdir("..")
        if _is_remove:
            os.system('rm -rf %s' % directory)
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                for aset in all_candidate_set:
                    directory = "MyTestGen_%s" % "_".join(aset.test_case)
                    if _is_remove:
                        os.system('rm -rf %s' % directory)
                all_candidate_set.clear()
                break
        
        if len(all_predicted_set) == pre_predicted_num:
            count += 1
        else:
            pre_predicted_num = len(all_predicted_set)
            count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change in 4 tests, then stop testing
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        
        ### generate a new testcase and do profile
        new_testcase = gen_testcase_splash(_rand_lower, _rand_upper)
        if new_testcase != None:
            directory = "MyTestGen_%s" % "_".join(new_testcase)
            if not os.path.exists(directory):
                os.mkdir(directory)
            os.chdir(directory)
            eval('__command_my_profile(argv + new_testcase)')
            ### update all_candidate_set, testcase_list, and all memo set
            sinfo = static_info.StaticInfo()
            sinfo.load("sinfo.db")
            iroot_db = iroot.iRootDB(sinfo)
            iroot_db.load("iroot.db")
            memo_db = memo.Memo(sinfo, iroot_db)
            memo_db.load("memo.db")
            my_memo = memo.myMemo(memo_db)
            for my_iroot in my_memo.exposed_set:
                if not is_in_set(my_iroot, all_exposed_set):
                    all_exposed_set.add(my_iroot)
            for my_iroot in my_memo.failed_set:
                if not is_in_set(my_iroot, all_failed_set):
                    all_failed_set.add(my_iroot)
            for my_iroot in my_memo.predicted_set:
                if not is_in_set(my_iroot, all_predicted_set):
                    all_predicted_set.add(my_iroot)
            for my_iroot in my_memo.shadow_exposed_set:
                if not is_in_set(my_iroot, all_shadow_exposed_set):
                    all_shadow_exposed_set.add(my_iroot)
            print "exposed_set length        = %d" % len(all_exposed_set)
            print "failed_set length         = %d" % len(all_failed_set)
            print "predicted_set length      = %d" % len(all_predicted_set)
            if len(all_shadow_exposed_set) != 0:
                print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
            my_candidate = memo.myCandidate(memo_db, new_testcase)
            all_candidate_set.add(my_candidate)
            testcase_list.append(new_testcase)
            os.chdir("..")
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    global NUM_ACTIVE
    global NUM_IROOT
    NUM_ACTIVE += len(chosen_list)
    NUM_IROOT += len(all_exposed_set)






def __command_my_test_prop(argv):
    start_time = time.time()
    
    all_candidate_set = set()            # memo.myCandidatep; testcase with its candidate iroots
    all_exposed_set = set()              # memo.myIRootp; all exposed iroots  (from memo.myMemop.exposed_set)
    all_failed_set = set()               # memo.myIRootp; all failed iroots  (from memo.myMemop.failed_set)
    all_predicted_set = set()            # memo.myIRootp; all predicted iroots  (from memo.myMemop.predicted_set)
    all_shadow_exposed_set = set()       # memo.myIRootp; all shadow_exposed iroots  (from memo.myMemop.shadow_exposed_set)
    
    testcase_list = list()               # readline.split(); all testcase
    chosen_list = list()                 # readline.split(); chosen testcase
    
    ### generate several testcases
    while len(testcase_list) < _num_of_candidate_testcase:
        test_case = gen_testcase_splash(_rand_lower, _rand_upper)
        if test_case != None:
            testcase_list.append(test_case)
    
    f = open("testcase.txt")
    last_dir = ""
    
    ### profile
    while 1:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### get a testcase and do profile
        line = f.readline()
        if not line:
            break
        if line == "\n":
            continue
        test_case = line.split()
        directory = "MyTestGen_%s" % "_".join(test_case)
        if not os.path.exists(directory):
            os.mkdir(directory)
        if os.path.exists(last_dir) and cmp(directory,last_dir)!=0:
            dirS1 = last_dir + "/sinfo.db"
            dirS2 = directory + "/sinfo.db"
            shutil.copyfile(dirS1, dirS2)
        os.chdir(directory)
        eval('__command_my_profile(argv + test_case)')
        ### update all_candidate_set, testcase_list, and all memo set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemop(memo_db)
        all_exposed_set |= my_memo.exposed_set
        all_failed_set |= my_memo.failed_set
        all_predicted_set |= my_memo.predicted_set
        all_shadow_exposed_set |= my_memo.shadow_exposed_set
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        my_candidate = memo.myCandidatep(memo_db, test_case)
        all_candidate_set.add(my_candidate)
        os.chdir("..")
        last_dir = directory
    f.close()
    
    count = 0
    pre_predicted_num = 0
    
    ### active
    global _CHOSEN_SET
    global _MIN_NUM
    while len(all_candidate_set) != 0:
        print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        ### choose a testcase
        (best_testcase, max_count) = get_best_testcasep(all_candidate_set, all_exposed_set, all_failed_set, all_shadow_exposed_set)
        print "best testcase is %s : count = %d" % (best_testcase, max_count)
        if max_count == 0:
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        chosen_list.append(best_testcase)
        directory = "MyTestGen_%s" % "_".join(best_testcase)
        os.chdir(directory)
        
        ### update all_exposed_set
        sinfo = static_info.StaticInfo()
        sinfo.load("sinfo.db")
        iroot_db = iroot.iRootDB(sinfo)
        iroot_db.load("iroot.db")
        memo_db = memo.Memo(sinfo, iroot_db)
        memo_db.load("memo.db")
        my_memo = memo.myMemop(memo_db)
        all_exposed_set |= my_memo.exposed_set
        all_exposed_set |= my_memo.failed_set
        all_exposed_set |= my_memo.predicted_set
        all_exposed_set |= my_memo.shadow_exposed_set
        print "exposed_set length        = %d" % len(all_exposed_set)
        print "failed_set length         = %d" % len(all_failed_set)
        print "predicted_set length      = %d" % len(all_predicted_set)
        if len(all_shadow_exposed_set) != 0:
            print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
        ### remove the tested testcase from all_candidate_set
        for aset in all_candidate_set:
            if aset.test_case == best_testcase:
                all_candidate_set.remove(aset)
                #
                _CHOSEN_SET.discard(aset)
                _MIN_NUM -= 1
                #
                break
        os.chdir("..")
        if _is_fatal:
            global IS_FATAL
            if IS_FATAL:
                os.system('rm -rf %s' % directory)
                for aset in all_candidate_set:
                    directory = "MyTestGen_%s" % "_".join(aset.test_case)
                    if _is_remove:
                        os.system('rm -rf %s' % directory)
                all_candidate_set.clear()
                break
        active_dir = directory
        
        if len(all_predicted_set) == pre_predicted_num:
            count += 1
        else:
            pre_predicted_num = len(all_predicted_set)
            count = 0
        if count == _num_of_candidate_testcase:     # if exposed iroots don't change in 4 tests, then stop testing
            for aset in all_candidate_set:
                directory = "MyTestGen_%s" % "_".join(aset.test_case)
                if _is_remove:
                    os.system('rm -rf %s' % directory)
            all_candidate_set.clear()
            break
        
        ### generate a new testcase and do profile
        new_testcase = gen_testcase_splash(_rand_lower, _rand_upper)
        directory = "MyTestGen_%s" % "_".join(new_testcase)
        while(cmp(directory,last_dir)==0 or cmp(directory,active_dir)==0):
            new_testcase = gen_testcase_splash(_rand_lower, _rand_upper)
            directory = "MyTestGen_%s" % "_".join(new_testcase)
        if new_testcase != None:
            #directory = "MyTestGen_%s" % "_".join(new_testcase)
            if not os.path.exists(directory):
                os.mkdir(directory)
            dirS1 = last_dir + "/sinfo.db"
            dirS2 = directory + "/sinfo.db"
            shutil.copyfile(dirS1, dirS2)
            if _is_remove:
                os.system('rm -rf %s' % active_dir)
            if os.path.exists(directory):
                os.chdir(directory)
                eval('__command_my_profile(argv + new_testcase)')
                ### update all_candidate_set, testcase_list, and all memo set
                sinfo = static_info.StaticInfo()
                sinfo.load("sinfo.db")
                iroot_db = iroot.iRootDB(sinfo)
                iroot_db.load("iroot.db")
                memo_db = memo.Memo(sinfo, iroot_db)
                memo_db.load("memo.db")
                my_memo = memo.myMemop(memo_db)
                all_exposed_set |= my_memo.exposed_set
                all_failed_set |= my_memo.failed_set
                all_predicted_set |= my_memo.predicted_set
                all_shadow_exposed_set |= my_memo.shadow_exposed_set
                print "exposed_set length        = %d" % len(all_exposed_set)
                print "failed_set length         = %d" % len(all_failed_set)
                print "predicted_set length      = %d" % len(all_predicted_set)
                if len(all_shadow_exposed_set) != 0:
                    print "shadow_exposed_set length = %d" % len(all_shadow_exposed_set)
                my_candidate = memo.myCandidatep(memo_db, new_testcase)
                all_candidate_set.add(my_candidate)
                #
                _CHOSEN_SET.add(my_candidate)
                _MIN_NUM += 1
                #
                testcase_list.append(new_testcase)
                os.chdir("..")
                last_dir = directory
        else:
            if _is_remove:
                os.system('rm -rf %s' % active_dir)
    
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    print "predicted_set = %s" % str(all_predicted_set)
    os.system('rm testcase.txt')
    print "chosen testcases:"
    for idx in range(len(chosen_list)):
        print '\t' + str(chosen_list[idx])
    ### print cost time
    end_time = time.time()
    print "cost time : %f" % (end_time - start_time)
    print "++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
    
    global NUM_ACTIVE
    global NUM_IROOT
    NUM_ACTIVE += len(chosen_list)
    NUM_IROOT += len(all_exposed_set)




def __command_my_test_pro_10(argv):
    start_time = time.time()
    global _CHOSEN_SET
    global _MIN_NUM
    for i in range(50):
        if _is_fatal:
            global IS_FATAL
            IS_FATAL = False
        _CHOSEN_SET.clear()
        _MIN_NUM = 99
        print "##### No.%d test ####### start" % (i+1)
        eval('__command_my_test_prop(argv)')
        print "##### No.%d test ####### end" % (i+1)
    global NUM_ACTIVE
    global NUM_IROOT
    print "actvs : %d" % NUM_ACTIVE
    print "iRoot :% d" % NUM_IROOT
    end_time = time.time()
    print "total time : %f" % (end_time - start_time)


##==============================================================
## End
##==============================================================

def main(argv):
    if len(argv) < 1:
        logging.err(command_usage())
    command = argv[0]
    logging.msg('performing command: %s ...\n' % command, 2) 
    if valid_command(command):
        eval('__command_%s(argv[1:])' % command)
    else:
        logging.err(command_usage())

if __name__ == '__main__':
    main(sys.argv[1:])

