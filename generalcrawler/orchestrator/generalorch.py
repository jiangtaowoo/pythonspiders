# -*- coding: utf-8 -*-
import os
import json
import time
import copy
from collections import deque
from requests.exceptions import ConnectionError
from requests.models import Response as ReqResponse
from datacrawler.gdatacrawler import GeneralCrawler
from dto.dtomanager import DTOManager
from persistadaptor.baseadaptor import AdaptorSqlite
from models.productmodel import ModelBase
#import gevent
#from gevent.lock import BoundedSemaphore
#from gevent.queue import Queue
#from gevent import monkey
#monkey.patch_all()

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

class BaseOrchestrator(object):
    def __init__(self, spidername=''):
        self.crawler = None
        self.businessmodel = None
        self.sqliteadaptor = None
        self.addinfo_cb = None
        self.tips_cb = None
        self.spidername = spidername
        self.craw_info_q = deque([])
        self.rsp_data_q = deque([])
        self._init_crawler()
        self.current_ts = time.time()
        self.timed_var_dict = dict()
        self.timed_var_site = ['']
        self.parser_cnt = 0
        self.crawler_cnt = 0
        self.crawler_latest_work_time = []
        self.parser_latest_work_time = []
        self.run_info_retry = dict()

    def _init_crawler(self):
        app_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        basepath = os.path.sep.join([app_base_dir,'spiders',self.spidername,'config'])
        self.crawler = GeneralCrawler(self.spidername)
        self.crawler.session_used = False
        self.businessmodel = ModelBase()
        self.sqliteadaptor = AdaptorSqlite(spidername=self.spidername)
        self.crawler.load_http_config(basepath + os.path.sep + 'http.yaml')
        self.businessmodel.load_model_config(basepath + os.path.sep + 'models.yaml')
        self.sqliteadaptor.load_db_config(basepath + os.path.sep + 'dbs.yaml')
        dtomgr = DTOManager(self.spidername)
        dtomgr.load_dto_config((basepath + os.path.sep + 'dtomap.yaml'))
        self.crawler.attach_dto(dtomgr=dtomgr)
        self.businessmodel.regist_persist_adaptor(self.sqliteadaptor)

    # to add additional info for each data row
    def regist_addinfo_callback(self, func):
        self.addinfo_cb = func

    def regist_tips_callback(self, func):
        self.tips_cb = func

    # children class should overwrite this method to setup crawler entry info
    def setup_entry_info(self, tenant_item):
        # input: [website, varmaps(opt)]
        # add tuple to craw_info_q: (tips, website, login_http, varmaps, sleepinterval)
        # self.craw_info_q.append( tuple() )
        return False

    def crawler_wait_toolong(self):
        ts = time.time()
        for i in xrange(0, self.crawler_cnt):
            if ts-self.crawler_latest_work_time[i] < 5:
                return False
        return True

    def parser_wait_toolong(self):
        ts = time.time()
        for i in xrange(0, self.parser_cnt):
            if ts-self.parser_latest_work_time[i] < 5:
                return False
        return True

    def url_request_worker(self, workername, workerid, timed_funcs, isdebug):
        timed_process_request, timed_process_callback, timed_process_database, timed_process_tips = timed_funcs
        while self.craw_info_q or not self.parser_wait_toolong():
            #print '%s - %d is working' % (workername, workerid)
            if self.craw_info_q:
                self.crawler_latest_work_time[workerid-1] = time.time()
                run_info = self.craw_info_q.popleft()
                if isinstance(run_info, tuple) and len(run_info)==5:
                    #rsp_data = self.crawler.process_request(*run_info[1:])
                    self.timed_var_site[0] = run_info[1]
                    try:
                        rsp_data = timed_process_request(run_info)
                        if isinstance(rsp_data, ReqResponse):
                            rsp_data = rsp_data.text
                        self.rsp_data_q.append((run_info, rsp_data))
                    except ConnectionError:
                        hash_runinfo = (run_info[0],run_info[1],run_info[2],json.dumps(run_info[3]),run_info[4])
                        if hash_runinfo not in self.run_info_retry:
                            try_cnt = 0
                            self.run_info_retry[hash_runinfo] = 0
                        else:
                            try_cnt = self.run_info_retry[hash_runinfo]
                            self.run_info_retry[hash_runinfo] = try_cnt + 1
                        if try_cnt<5:
                            self.craw_info_q.append(run_info)
            else:
                gevent.sleep(0)
        print '%s - %d is quiting' % (workername, workerid)
        #with open('threads_info.log', 'a+') as outf:
        #    outf.write( 'worker %s %d quitting\n' % (workername, workerid) )

    def data_callback_worker(self, workername, workerid, timed_funcs, isdebug):
        timed_process_request, timed_process_callback, timed_process_database, timed_process_tips = timed_funcs
        while self.rsp_data_q or not self.crawler_wait_toolong():
            #print '%s - %d is working' % (workername, workerid)
            if self.rsp_data_q:
                #print 'http_q: %d, data_q: %d' % (len(self.craw_info_q), len(self.rsp_data_q))
                self.parser_latest_work_time[workerid-1] = time.time()
                run_info, rsp_data = self.rsp_data_q.popleft()
                next_rinfos, data_set, av_data_module = timed_process_callback(rsp_data, run_info)
                # add next running info to queue (tips,website,http,varmaps,sleepinterval)
                if next_rinfos:
                    for next_rinfo in next_rinfos:
                        self.craw_info_q.append(next_rinfo)
                if not data_set:
                    continue
                    #break
                for datarow in data_set:
                    if self.addinfo_cb:
                        self.addinfo_cb(datarow)
                    if isdebug:
                        self.businessmodel.notify_model_info_debug(av_data_module=av_data_module, **datarow)
                    else:
                        #self.businessmodel.notify_model_info_received(av_data_module=av_data_module, **datarow)
                        timed_process_database(av_data_module, datarow)
                if self.tips_cb:
                    #self.tips_cb(run_info[0])
                    timed_process_tips(run_info)
                if isdebug:
                    ts = time.time()
                    if ts-self.current_ts>60:
                        self.current_ts = ts
                        self.record_time_elapsed()
            else:
                gevent.sleep(0)
        print '%s - %d is quiting' % (workername, workerid)
        #with open('threads_info.log', 'a+') as outf:
        #    outf.write( 'worker %s-<%d> quitting\n' % (workername, workerid) )

    def record_time_elapsed(self):
        with open('%s_time_elapsed.log' % (self.spidername), 'a+') as outf:
            out_dict = copy.deepcopy(self.timed_var_dict)
            for kt, vt in self.timed_var_dict.iteritems():
                for sitehttp, t in vt.iteritems():
                    out_dict[kt][sitehttp] = int(t)
            outf.write(json.dumps(out_dict))
            outf.write('\n')

    def dump_failed_task(self):
        if isinstance(self.run_info_retry,dict):
            with open('%s_failed_task.log' % (self.spidername), 'a+') as outf:
                for hash_runinfo, try_cnt in self.run_info_retry.iteritems():
                    outf.write(try_cnt)
                    outf.write('\t'.join(map(unicode,list(hash_runinfo))))
                    outf.write('\n')
                #outf.write(json.dumps(self.run_info_retry))

    def run_pipeline(self, isdebug=False):
        self.run_pipeline_sthread(isdebug)
        #if isdebug:
        #    self.run_pipeline_sthread(isdebug)
        #else:
        #    self.run_pipeline_gevent()

    def run_pipeline_gevent(self, isdebug=False):
        timed_var_dict = self.timed_var_dict
        timed_var_site = self.timed_var_site
        @timeit_by_dict(timed_var_dict, 'WEB_REQUEST', timed_var_site)
        def timed_process_request(run_info):
            return self.crawler.process_request(*run_info[1:])

        @timeit_by_dict(timed_var_dict, 'DTO_CALLBACK', timed_var_site)
        def timed_process_callback(rsp_data, run_info):
            return self.crawler.exec_callback(rsp_data, run_info)

        @timeit_by_dict(timed_var_dict, 'DB_OPERATE', timed_var_site)
        def timed_process_database(av_data_module, datarow):
            self.businessmodel.notify_model_info_received(av_data_module=av_data_module, **datarow)

        @timeit_by_dict(timed_var_dict, 'TIP_OUTPUT', timed_var_site)
        def timed_process_tips(run_info):
            self.tips_cb(run_info[0])

        timed_funcs = (timed_process_request, timed_process_callback, timed_process_database, timed_process_tips)
        #step3. create worker greenlet
        threads = []
        c_worker_size = 20
        c_consumer_size = 1
        #c_sem_size = 1
        self.crawler_cnt = c_worker_size
        self.parser_cnt = c_consumer_size
        self.crawler_latest_work_time = [time.time()]*c_worker_size
        self.parser_latest_work_time = [time.time()] * c_consumer_size
        #3.1 create worker greenlets
        for i in xrange(0,c_worker_size):
            threads.append( gevent.spawn(self.url_request_worker, 'url_crawler_worker', i+1, timed_funcs, isdebug) )
        #3.2 create one consumer greenlet
        threads.append( gevent.spawn(self.data_callback_worker, 'data_callback_worker', 1, timed_funcs, isdebug) )

        #step4. wait for finishing
        gevent.joinall( threads )
        self.businessmodel.notify_model_info_end()
        self.dump_failed_task()

    def run_pipeline_sthread(self, isdebug=False):
        timed_var_dict = self.timed_var_dict
        timed_var_site = self.timed_var_site
        @timeit_by_dict(timed_var_dict, 'WEB_REQUEST', timed_var_site)
        def timed_process_request(run_info):
            return self.crawler.process_request(*run_info[1:])

        @timeit_by_dict(timed_var_dict, 'DTO_CALLBACK', timed_var_site)
        def timed_process_callback(rsp_data, run_info):
            return self.crawler.exec_callback(rsp_data, run_info)

        @timeit_by_dict(timed_var_dict, 'DB_OPERATE', timed_var_site)
        def timed_process_database(av_data_module, datarow):
            self.businessmodel.notify_model_info_received(av_data_module=av_data_module, **datarow)

        @timeit_by_dict(timed_var_dict, 'TIP_OUTPUT', timed_var_site)
        def timed_process_tips(run_info):
            self.tips_cb(run_info[0])

        current_ts = time.time()
        while self.craw_info_q:
            run_info = self.craw_info_q.popleft()
            if isinstance(run_info, tuple) and len(run_info)==5:
                #rsp_data = self.crawler.process_request(*run_info[1:])
                timed_var_site[0] = run_info[1]
                rsp_data = timed_process_request(run_info)
                if isinstance(rsp_data, ReqResponse):
                    rsp_data = rsp_data.text
                #next_rinfos, data_set, av_data_module = self.crawler.exec_callback(rsp_data, run_info)
                next_rinfos, data_set, av_data_module = timed_process_callback(rsp_data, run_info)
                # add next running info to queue (tips,website,http,varmaps,sleepinterval)
                if next_rinfos:
                    for next_rinfo in next_rinfos:
                        self.craw_info_q.append(next_rinfo)
                if not data_set:
                    continue
                    #break
                for datarow in data_set:
                    if self.addinfo_cb:
                        self.addinfo_cb(datarow)
                    if isdebug:
                        self.businessmodel.notify_model_info_debug(av_data_module=av_data_module, **datarow)
                    else:
                        #self.businessmodel.notify_model_info_received(av_data_module=av_data_module, **datarow)
                        timed_process_database(av_data_module, datarow)
                if self.tips_cb:
                    #self.tips_cb(run_info[0])
                    timed_process_tips(run_info)

                ts = time.time()
                if ts-current_ts>60:
                    current_ts = ts
                    with open('timed_info_%s.txt' % (self.spidername), 'a+') as outf:
                        out_dict = copy.deepcopy(timed_var_dict)
                        for kt, vt in timed_var_dict.iteritems():
                            for sitehttp, t in vt.iteritems():
                                out_dict[kt][sitehttp] = int(t)
                        outf.write(json.dumps(out_dict))
                        outf.write('\n')
        self.businessmodel.notify_model_info_end()