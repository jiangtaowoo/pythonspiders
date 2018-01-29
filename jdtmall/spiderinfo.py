# _*_ coding:utf-8 _*_
import os
import re
import random
import yaml


class RunInfo(object):
    cfg_path = os.path.sep.join([os.path.dirname(os.path.abspath(__file__)),'config'])
    user_agent_list = yaml.load( open(os.path.sep.join([cfg_path, 'useragent.yaml'])) )
    interval_info = yaml.load( open(os.path.sep.join([cfg_path, 'sleepinterval.yaml'])) )

    def __init__(self, sitename='', prodname='', produrl='', **kwargs):
        av_domain = {'tmall': ['tmall.com', 'tmall.hk', 'liangxinyao.com'], 'jd': ['jd.com']}
        #url
        self.headers = ''
        self.url = ''
        #sleep interval
        self.sleepinterval = 0
        if 'tmall.com' in self.interval_info and 'sleep' in self.interval_info['tmall.com']:
            if 'tmall.com' in produrl or 'tmall.hk' in produrl or 'liangxinyao.com' in produrl:
                self.sleepinterval = int(self.interval_info['tmall.com']['sleep'])
        elif 'jd.com' in self.interval_info and  'sleep' in self.interval_info['jd.com']:
            if 'jd.com' in produrl:
                self.sleepinterval = int(self.interval_info['jd.com']['sleep'])
        #try count
        self.try_cnt = 0
        #sitename, product name, product url, pagenum
        self.sitename = sitename
        self.prodname = prodname
        self.produrl = produrl
        #the following var is just for tmall
        self.vardict = dict()
        for k, v in kwargs.iteritems():
            self.vardict[k] = v
        #generate url
        for site, domainlist in av_domain.iteritems():
            for durl in domainlist:
                if durl in produrl:
                    if not kwargs:
                        if site=='tmall':
                            self._gen_tmall_headers()
                        elif site=='jd':
                            self._gen_jd_headers()
                    else:
                        if site=='tmall':
                            self._gen_tmall_headers()
                            self._gen_tmall_comment_url(self.produrl, self.vardict['itemid'], self.vardict['sellerid'], self.vardict['page'])
                        elif site=='jd':
                            self._gen_jd_headers(self.produrl)
                            self._gen_jd_comment_url(self.produrl, self.vardict['verinfo'], self.vardict['prodid'], self.vardict['page'])
                        else:
                            self.url = ''
                    break

    def _gen_tmall_comment_url(self, produrl, itemid, sellerid, pageidx):
        base_url = 'https://rate.tmall.com/list_detail_rate.htm?itemId=%s&sellerId=%s&currentPage=%d'
        self.url = base_url % (str(itemid), str(sellerid), pageidx)

    def _gen_jd_comment_url(self, produrl, verinfo, prodid, pageidx):
        base_url = 'http://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv%s&productId=%s&score=0&sortType=5&page=%d&pageSize=10&isShadowSku=0&rid=0&fold=1'
        self.url = base_url % (str(verinfo), str(prodid), pageidx)

    def _gen_tmall_headers(self):
        self.headers = {'User-Agent': random.choice(self.user_agent_list)}

    def _gen_jd_headers(self, produrl=''):
        if not produrl:
            self.headers = {'Host': 'item.jd.com', 'User-Agent': random.choice(self.user_agent_list)}
        else:
            self.headers = {'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'User-Agent': random.choice(self.user_agent_list), 'Host': 'sclub.jd.com', 'Referer': produrl}