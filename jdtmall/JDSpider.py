# _*_ coding:utf-8 _*_
import random
from collections import deque
import json
import time
import re
#from requests.models import Response as ReqResponse
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from spiderinfo import RunInfo
from BaseSpider import html_element_exists, BaseCrawler
import gevent
from gevent import monkey
monkey.patch_all()


class JDCrawler(BaseCrawler):
    def _parse_verinfo_prodid_from_url(self, sess, sitename, url):
        prodid = re.findall(r'\d+',url)
        if len(prodid)>0:
            prodid = prodid[0]
        else:
            return None, None
        #jd.hk only need prodid
        if 'jd.hk' in url:
            return None, prodid
        #jd.com yiyaojd.com
        verinfo = ''
        #get verinfo from html page
        run_obj = RunInfo(sitename, 'anything', url)
        rsp = sess.get(url=url, headers=run_obj.headers)
        if rsp.status_code==200:
            comment_verinfo = re.findall(r"commentVersion:'\d+", rsp.text)
            if len(comment_verinfo):
                verinfo = comment_verinfo[0][16:]
        if verinfo and prodid:
            return verinfo, prodid
        return None, None            

    def _get_page_number(self, sess, produrl, verinfo, prodid):
        run_obj = RunInfo('jd.com', 'jd.com', produrl, verinfo=verinfo, prodid=prodid, page=1)
        try_cnt = 0
        while True and try_cnt<5:
            rsp = sess.get(url=run_obj.url, headers=run_obj.headers)
            try:
                page_data = rsp.text
            except Exception, e:
                print '***JD*** Get page ERROR:', run_obj.vardict['page'], e
                try_cnt += 1
                continue
            #step2. parse data
            try:
                #jd.hk
                if verinfo is None:
                    page_dict = json.loads(page_data)
                else:
                    startidx = len('fetchJSON_comment98vv') + len(str(verinfo)) + 1
                    myjson = page_data[startidx:-2]
                    page_dict = json.loads(myjson)
            except Exception, e:
                print '***JD*** Parse page ERROR:', run_obj.vardict['page'], e
                try_cnt += 1
                continue
                ########################################################################
                ########################################################################
                ########################################################################
                """
                print page_data
                raw_input('press anykey to continue')
                page_dict = json.loads(page_data)
                if 'url' in page_dict:
                    login_url = page_dict['url']
                    self._login_tmall(sess, login_url)
                """
                ########################################################################
                ########################################################################
                ########################################################################
            try:
                pagecnt = int(page_dict['maxPage'])
                return pagecnt
            except:
                try_cnt += 1
        return 0

    def _get_one_page_comment(self, sess, run_obj):
        #step1. get page data
        rsp = sess.get(url=run_obj.url, headers=run_obj.headers)
        try:
            page_data = rsp.text
        except Exception, e:
            print '***JD*** Get page ERROR:', run_obj.vardict['page'], e
            return None
        #step2. parse data
        try:
            if run_obj.vardict['verinfo'] is None:
                page_dict = json.loads(page_data)
            else:
                startidx = len('fetchJSON_comment98vv') + len(str(run_obj.vardict['verinfo'])) + 1
                myjson = page_data[startidx:-2]
                page_dict = json.loads(myjson)
        except Exception, e:
            print '***JD*** Parse page ERROR:', run_obj.vardict['page'], e
            return None
            """
            ########################################################################
            ########################################################################
            ########################################################################
            print page_data
            raw_input('press anykey to continue')
            page_dict = json.loads(page_data)
            if 'url' in page_dict:
                login_url = page_dict['url']
                self._login_tmall(sess, login_url)
            ########################################################################
            ########################################################################
            ########################################################################
            """
        if len(page_dict) == 0:
            return None
        #step3. return dataset
        dataset = []
        page_dict = page_dict['comments']
        keys = ['id', 'guid', 'nickname', 'userLevelId', 'userLevelName', 'creationTime', 'productColor', 'productSize', 'score', 'content', 'replyCount', 'isMobile', 'userClientShow', 'recommend', 'userExpValue', 'plusAvailable']
        innerkeys = ['commentid', 'jdcguid', 'nickname', 'userLevelId', 'userLevelName', 'creationTime', 'productColor', 'productSize', 'score', 'content', 'replyCount', 'isMobile', 'userClientShow', 'recommend', 'userExpValue', 'plusAvailable']
        for comment_row in page_dict:
            datarow = dict()
            datarow['sitename'] = run_obj.sitename
            datarow['prodname'] = run_obj.prodname
            datarow['produrl'] = run_obj.produrl
            datarow['prodid'] = run_obj.vardict['prodid']
            datarow['commentver'] = run_obj.vardict['verinfo']
            for idx, k in enumerate(keys):
                dataitem = comment_row[k] if k in comment_row else ''
                datarow[innerkeys[idx]] = self._stringify_data(dataitem)
            dataset.append(datarow)
        return dataset

    def crawl_worker(self, workername, workerid):
        while self.crawler_q:
            if self.crawler_except_q:
                gevent.sleep(5)
                continue
            run_obj = self.crawler_q.popleft()
            print '>>>JD>>> getting data %s, - page %d ...' % (run_obj.prodname, run_obj.vardict['page'])
            dataset = self._get_one_page_comment(self.sess, run_obj)
            if dataset is None:
                if run_obj.try_cnt<5:
                    run_obj.try_cnt += 1
                    if run_obj.sleepinterval==0:
                        run_obj.sleepinterval = 2
                    elif run_obj.sleepinterval<5:
                        run_obj.sleepinterval += 1
                    self.crawler_q.append(run_obj)
                else:
                    print '***JD JOB FAILED %s, page %d !' % (run_obj.prodname, run_obj.vardict['page'])
            else:
                for datarow in dataset:
                    self.businessmodel.notify_model_info_received(av_data_module=['JDModel'], **datarow)
            #slow down
            if run_obj.sleepinterval>0:
                gevent.sleep(run_obj.sleepinterval)

    def crawl_product_comment(self, sitename, prodname, produrl):
        verinfo, prodid = self._parse_verinfo_prodid_from_url(self.sess, sitename, produrl)
        self.crawler_q = deque([])
        if ('jd.hk' in produrl and prodid) or (verinfo and prodid):
            #get page number
            pagecnt = self._get_page_number(self.sess, produrl, verinfo, prodid)
            for pageidx in xrange(1, pagecnt):
                run_obj = RunInfo(sitename, prodname, produrl, verinfo=verinfo, prodid=prodid, page=pageidx)
                self.crawler_q.append(run_obj)
            #getting data
            #getting data
            threads = []
            for i in xrange(0,100):
                threads.append( gevent.spawn(self.crawl_worker, 'jd_crawl_worker', i+1) )
            #3.2 create one consumer greenlet
            #step4. wait for finishing
            gevent.joinall( threads )
            print 'Finish getting data!'
        else:
            print 'Url unrecognized: %s' % (produrl)
