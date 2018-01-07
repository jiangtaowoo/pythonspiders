# -*- coding: utf-8 -*-
import time
from generalorch import BaseOrchestrator

class ZSOrchestrator(BaseOrchestrator):
    def setup_entry_info(self, tenant_item):
        # input: [website, varmaps(opt)]
        # add tuple to craw_info_q: (tips, website, login_http, varmaps, sleepinterval)
        # self.craw_info_q.append( tuple() )
        website = tenant_item[0]
        tips = 'site: %s , request login page' % (website)
        sitehttp = 'login_http'
        dmaps = {'%PAGEOFFSET%': '0', '%PAGEINDEX%': '1', '%TIMESTAMP%': str(int(time.time()*1000))}
        login_dmaps = None
        sleepinterval = 0
        if len(tenant_item)>0:
            login_dmaps = tenant_item[1]
            if not isinstance(login_dmaps, dict):
                login_dmaps = None
        if login_dmaps:
            for k, v in login_dmaps.iteritems():
                dmaps[k] = v
        run_info = (tips, website, sitehttp, dmaps, sleepinterval)
        self.craw_info_q.append(run_info)
        return True