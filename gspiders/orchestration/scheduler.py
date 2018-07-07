# -*- coding: utf-8 -*-
import time
from collections import deque
from requests.exceptions import ConnectionError
from orchestration.crawler import WebCrawler
from orchestration.datamodel import DataModel
#from orchestration.saveload import SaveLoader as SaveLoadAdaptor
from orchestration.adaorm import AdaptorORM as SaveLoadAdaptor
#from orchestration.adasqlite import AdaptorSqlite as SaveLoadAdaptor
from meta.metacls import Singleton
from meta.setting import ConfigManager
from meta.proxy import ProxyPool
import gevent
#from gevent.lock import BoundedSemaphore
#from gevent.queue import Queue
from gevent import monkey
monkey.patch_all()

def timeit_by_dict(store_dict, seg1, seg2):
    def timeit(method_to_be_timed):
        def timed(*args, **kw):
            ts = time.time()
            result = method_to_be_timed(*args, **kw)
            te = time.time()
            if seg1 not in store_dict:
                store_dict[seg1] = dict()
            if seg2[0] in store_dict[seg1]:
                store_dict[seg1][seg2[0]] = store_dict[seg1][seg2[0]]+te-ts
            else:
                store_dict[seg1][seg2[0]] = te-ts
            return result
        return timed
    return timeit


class TimedWorker(object):
    def __init__(self, worker, id):
        self._worker = worker
        self._id = id
        self._latest_active_time = time.time()

    @property
    def active_time(self):
        return self._latest_active_time

    @property
    def id(self):
        return self._id

    @property
    def worker(self):
        self._latest_active_time = time.time()
        return self._worker


class Scheduler(object):
    __metaclass__ = Singleton

    def __init__(self, spidername, runmode=0):
        self._spidername = spidername
        self._run_mode = runmode
        self._glo_cfgs = ConfigManager(spidername)
        self._proxy = ProxyPool()
        #任务队列
        self.job_queue = deque([])
        self.rsp_queue = deque([])
        self.dataset_queue = deque([])
        self.datasave_queue = deque([])
        self._jobs = [self.job_queue, self.rsp_queue,
                      self.dataset_queue, self.datasave_queue]
        #回调函数队列
        self.crawler_procs = []          #request, selenium 进程
        self.parser_procs = []           #数据清洗, 错误处理, 数据提取
        self.modeler_procs = []         #数据模型转换
        self.saver_procs = []           #入库处理函数, 包括计时处理, 写日志等
        self._callbacks = [self.crawler_procs, self.parser_procs,
                           self.modeler_procs, self.saver_procs]
        #处理类型
        self._prompt_func = None
        self._crawler = WebCrawler
        self._parser = None
        self._moduler = DataModel
        self._saver = SaveLoadAdaptor         #默认入库到sqlite

    def _init_spider(self, spidername):
        if not self._parser:
            return False
        """
        配置处理流程(设置回调函数队列)
        1. crawler 队列
        2. parser 队列
        3. saver 队列
        每个工人自带以下信息:
        a. 自己的类型
        b. 自己上一次工作的时间(last_active_time)
        """
        CRAWLER_SIZE = 30 if self._run_mode else 1
        PARSER_SIZE = 1
        MODELER_SIZE = 1
        SAVER_SIZE = 1
        sizes = [CRAWLER_SIZE, PARSER_SIZE, MODELER_SIZE, SAVER_SIZE]
        self._proctypes = [self._crawler, self._parser,
                           self._moduler, self._saver]
        for i in range(len(sizes)):
            #create worker
            proc_instances = [TimedWorker(self._proctypes[i](), j)
                              for j in range(sizes[i])]
            #put worker in queue
            self._callbacks[i].extend(proc_instances)
        return True

    # children class should overwrite this method to setup crawler entry info
    @staticmethod
    def _worker_idle(worker_list, wait_duration=30):
        ts = time.time()
        for worker in worker_list:
            if ts-worker.active_time < wait_duration:
                return False
        return True

    def _crawler_worker(self, worker):
        while self.job_queue or not Scheduler._worker_idle(self.crawler_procs):
            if self.job_queue:
                runner = self.job_queue.popleft()
                try:
                    for rsp in worker.worker.process_request(runner):
                        self.rsp_queue.append((runner, rsp))
                except ConnectionError:
                    if runner.has_retry_opportunity():
                        self.job_queue.append(runner)
            else:
                gevent.sleep(0)
        print('Crawler - {0} is quiting'.format(worker.id))

    def _parser_worker(self, worker):
        while self.rsp_queue or not Scheduler._worker_idle(self.parser_procs, 60):
            if self.rsp_queue:
                runner, rsp =  self.rsp_queue.popleft()
                success, result = worker.worker.dispatch_response(runner, rsp)
                if success:
                    runners, models, dataset = result
                    self.add_jobs(runners)
                    self.dataset_queue.append((runner, models, dataset))
                else:
                    print(result)
            else:
                gevent.sleep(0)
        print('Parser - {0} is quiting'.format(worker.id))

    def _modeler_worker(self, worker):
        while self.dataset_queue or not Scheduler._worker_idle(self.modeler_procs, 60):
            if self.dataset_queue:
                runner, models, dataset = self.dataset_queue.popleft()
                datadict = worker.worker.gen_model_data(models, dataset)
                if datadict:
                    self.datasave_queue.append((runner, datadict))
            else:
                gevent.sleep(0)
        print('Modeler - {0} is quiting'.format(worker.id))

    def _saver_worker(self, worker):
        while self.datasave_queue or not Scheduler._worker_idle(self.saver_procs, 60):
            if self.datasave_queue:
                runner, datadict = self.datasave_queue.popleft()
                worker.worker.persist_data(datadict)
                if self._prompt_func:
                    self._prompt_func(runner.get_prompt_msg())
            else:
                gevent.sleep(0)
        print('Saver - {0} is quiting'.format(worker.id))

    def _run_mode_multiple(self):
        threads = []
        threads.extend([gevent.spawn(self._crawler_worker, w)
                        for w in self.crawler_procs])
        threads.extend([gevent.spawn(self._parser_worker, w)
                        for w in self.parser_procs])
        threads.extend([gevent.spawn(self._modeler_worker, w)
                        for w in self.modeler_procs])
        threads.extend([gevent.spawn(self._saver_worker, w)
                        for w in self.saver_procs])
        def _peek_queue():
            while not all([Scheduler._worker_idle(p) for p in self._callbacks]):
                print('jobs: {0}, responses: {1}, models: {2}, savers: {3}'.format(
                    *map(len, self._jobs)))
                gevent.sleep(10)
        threads.append(gevent.spawn(_peek_queue))
        gevent.joinall( threads )

    def _run_mode_single(self):
        crawler = self.crawler_procs[0].worker
        parser = self.parser_procs[0].worker
        modeler = self.modeler_procs[0].worker
        saver = self.saver_procs[0].worker
        while self.job_queue:
            runner = self.job_queue.popleft()
            #1. download page
            for rsp in crawler.process_request(runner):
                #2. parse page
                success, result = parser.dispatch_response(runner, rsp)
            #3. generate data
            datadict = None
            if success:
                runners, models, dataset = result
                self.add_jobs(runners)
                datadict = modeler.gen_model_data(models, dataset)
            else:
                print(result)
            #4. save data to db
            if datadict:
                saver.persist_data(datadict)
                if self._prompt_func:
                    self._prompt_func(runner.get_prompt_msg())

    """
    interface for user
    """
    def register_parser_saver(self, parser, saver=None):
        if parser is not None: #isinstance(parser(), Parser):
            self._parser = parser
            if saver is not None: # and isinstance(saver(), SaveLoader):
                self._saver = saver
            #创建procedure queue
            self._init_spider(self._spidername)
            #初始化parser要抓取的内容
            runners = self.parser_procs[0].worker.init_runners()
            self.add_jobs(runners)
            return True
        return False

    def register_prompt_procedure(self, func):
        self._prompt_func = func

    def add_jobs(self, runners):
        if runners:
            for r in runners:
                self.job_queue.append(r)

    def run_pipeline(self):
        #self.run_pipeline_sthread(isdebug)
        if self._run_mode:
            self._run_mode_multiple()
        else:
            self._run_mode_single()
