# -*- coding: utf-8 -*-
import time
from sys import argv
from orchestration.scheduler import Scheduler
from spiders.autohome.autohome import AutohomeParser

def timed_procedure(proc):
    def wrapper(*args, **kw):
        ts = time.time()
        result = proc(*args, **kw)
        te = time.time()
        print('procedure %s took %2.4f sec' % (proc.__name__, te-ts))
        return result
    return wrapper

def print_tips(tips):
    if tips:
        print(u'>>> {0} ...'.format(tips))


@timed_procedure
def main(spidername):
    scheduler = Scheduler(spidername, 1)
    scheduler.register_parser_saver(AutohomeParser)
    scheduler.register_prompt_procedure(print_tips)
    scheduler.run_pipeline()
    print('Finish!')

if __name__=="__main__":
    script, spidername = argv
    main(spidername)
