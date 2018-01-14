# -*- coding: utf-8 -*-
import json
import time
from callbackcommon import BaseCallback

class JDCallback(BaseCallback):
    def __init__(self):
        BaseCallback.__init__(self)
        self.sitename = 'zgb.m.jd.com'

    def convert_data(self, data, dmaps):
        return json.loads(data[19:-1])

    def login_url_generator(self, data, dmaps):
        #return information for data_http crawler
        dmaps = {'%PAGEINDEX%': '1', '%TIMESTAMP%': str(int(time.time()*1000))}
        return [('page 1', self.sitename, 'data_http', dmaps, 0)]

    def data_url_generator(self, data, dmaps):
        if data:
            pageidx = int(dmaps['%PAGEINDEX%'])
            pageidx += 1
            dmaps['%PAGEINDEX%'] = str(pageidx)
            dmaps['%TIMESTAMP%'] = str(int(time.time()*1000))
            return [('page ' + str(pageidx), self.sitename, 'data_http', dmaps, 0)]
        return None

    def calc_product_url(self, dmaps, productid):
        return 'http://zgb.m.jd.com/detail.html?id=' + str(productid)