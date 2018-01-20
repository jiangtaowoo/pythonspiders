# -*- coding: utf-8 -*-
from orchestrator.generalorch import BaseOrchestrator

class DiyOrchestrator(BaseOrchestrator):
    def __init__(self, spidername=''):
        BaseOrchestrator.__init__(self, spidername)
        self.pipline_mode = 'gevent'
        
    def setup_entry_info(self, tenant_item):
        # input: [website, varmaps(opt)]
        # add tuple to craw_info_q: (tips, website, login_http, varmaps, sleepinterval)
        # self.craw_info_q.append( tuple() )
        website = tenant_item[0]
        tips = 'site: %s , request start' % (website)
        sitehttp = 'init_http'
        dmaps = None
        sleepinterval = 0
        run_info = (tips, website, sitehttp, dmaps, sleepinterval)
        self.craw_info_q.append(run_info)
        return True