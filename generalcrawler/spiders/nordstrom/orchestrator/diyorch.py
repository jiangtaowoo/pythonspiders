# -*- coding: utf-8 -*-
import time
#import os,sys
#currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
#parentdir = os.path.sep.join(currentdir.split(os.path.sep)[:-3])
#if parentdir not in sys.path:
#    sys.path.insert(0,parentdir) 
#print parentdir

from orchestrator.generalorch import BaseOrchestrator

class DiyOrchestrator(BaseOrchestrator):
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