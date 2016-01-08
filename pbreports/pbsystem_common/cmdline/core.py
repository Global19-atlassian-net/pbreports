"""Utils for commandline api"""
import time
import sys
import logging
import traceback

import pbreports.pbsystem_common.utils

log = logging.getLogger(__name__)


def args_executer(args):
    """


    :rtype int
    """
    try:
        return_code = args.func(args)
    except Exception as e:
        log.error(e, exc_info=True)
        traceback.print_exc(sys.stderr)
        if isinstance(e, IOError):
            return_code = 1
        else:
            return_code = 2

    return return_code


def main_runner(argv, parser, exe_runner_func, setup_log_func, alog):
    """
    Fundamental interface to commandline applications
    """
    started_at = time.time()
    args = parser.parse_args(argv)
    log.debug(args)

    # setup log
    if hasattr(args, 'debug'):
        if args.debug:
            setup_log_func(alog, level=logging.DEBUG)
        else:
            alog.addHandler(logging.NullHandler())
    else:
        alog.addHandler(logging.NullHandler())

    rcode = exe_runner_func(args)

    run_time = time.time() - started_at
    _d = dict(r=rcode, s=run_time)
    alog.info("exiting with return code {r} in {s:.2f} sec.".format(**_d))
    return rcode


def main_runner_default(argv, parser, alog):
    # this has a loose assumption that debug has been defined in the parser
    setup_log_func = pbreports.pbsystem_common.utils.setup_log
    return main_runner(argv, parser, args_executer, setup_log_func, alog)
