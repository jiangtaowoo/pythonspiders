# -*- coding: utf-8 -*-
import os
from collections import deque
from requests.models import Response as ReqResponse
from datacrawler.gdatacrawler import GeneralCrawler
from dto.dtomanager import DTOManager
from persistadaptor.baseadaptor import AdaptorSqlite
from models.productmodel import ModelBase


class BaseOrchestrator(object):
    def __init__(self, spidername=''):
        self.crawler = None
        self.businessmodel = None
        self.sqliteadaptor = None
        self.addinfo_cb = None
        self.tips_cb = None
        self.spidername = spidername
        self.craw_info_q = deque([])
        self._init_crawler()

    def _init_crawler(self):
        app_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        basepath = os.path.sep.join([app_base_dir,'spiders',self.spidername,'config'])
        self.crawler = GeneralCrawler(self.spidername)
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

    def run_pipeline(self, isdebug=False):
        while self.craw_info_q:
            run_info = self.craw_info_q.popleft()
            if isinstance(run_info, tuple) and len(run_info)==5:
                rsp_data = self.crawler.process_request(*run_info[1:])
                if isinstance(rsp_data, ReqResponse):
                    rsp_data = rsp_data.text
                next_rinfos, data_set, av_data_module = self.crawler.exec_callback(rsp_data, run_info)
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
                        self.businessmodel.notify_model_info_received(av_data_module=av_data_module, **datarow)
                if self.tips_cb:
                    self.tips_cb(run_info[0])