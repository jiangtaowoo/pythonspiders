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


class TMallCrawler(BaseCrawler):
    def _perform_slipper(self, browser):
        try:
            slipper = WebDriverWait(browser, 10).until(html_element_exists('xpath', '//div[@id="nc_1__scale_text"]//span[@class="nc-lang-cnt"]'))
            h_position = slipper.location
            action = ActionChains(browser)
            action.drag_and_drop_by_offset(slipper, h_position['x'] + 300, h_position['y']).perform()
            time.sleep(1)
        except NoSuchElementException:
            pass

    def _perform_login(self, browser, account_info):
        elem = WebDriverWait(browser, 10).until(html_element_exists('xpath', '//input[@id="TPL_username_1"]'))
        elem.clear()
        elem.send_keys(account_info[0])
        elem = WebDriverWait(browser, 10).until(html_element_exists('id', 'TPL_password_1'))
        elem.clear()
        elem.send_keys(account_info[1])

    def _login_tmall(self, sess, login_url):
        browser = webdriver.Firefox()
        browser.get(login_url)
        if 'sec.taobao.com' in login_url and 'tmallrateweb-rate-anti_Spider-checklogin' in login_url:
            # tmallrateweb-rate-anti_Spider-checkcode
            #perform automatic login
            if self.accounts:
                if 'tmall.com' in self.accounts:
                    acc_list = self.accounts['tmall.com']
                    acc_info = random.choice(acc_list)
                    self._perform_login(browser, acc_info)
        raw_input('press any key to continue after login succeed!')
        self._save_browser_cookie(sess, browser)
        browser.quit()

    def _parse_item_seller_from_url(self, sess, sitename, url):
        itemid = re.findall(r'&id=\d+',url)
        if len(itemid)>0:
            itemid = itemid[0][4:]
        else:
            return None, None
        sellerid = ''
        sellerid_dict = {'chaoshi.detail.tmall.com': '725677994', 'detail.liangxinyao.com': '2928278102'}
        #step1. get sellerid from pre-defined
        for k, v in sellerid_dict.iteritems():
            if k in url:
                sellerid = v
                break
        #step2. get sellerid from url
        if not sellerid:
            sellerid = re.findall(r'&user_id=\d+',url)
            if len(sellerid)>0:
                sellerid = sellerid[0][9:]
            else:
                #step3. get url from html page
                run_obj = RunInfo(sitename, 'anything', url)
                rsp = sess.get(url=url, headers=run_obj.headers)
                if rsp.status_code==200:
                    useridinfo = re.findall(r'userid=\d+',rsp.text)
                    if len(useridinfo):
                        sellerid = useridinfo[0][7:]
        if itemid and sellerid:
            return itemid, sellerid
        return None, None            

    def _get_page_number(self, sess, itemid, sellerid): #itemId 是商品的id, sellerId是卖家的id
        run_obj = RunInfo('tmall.com', 'tmall.com', 'tmall.com', itemid=itemid, sellerid=sellerid, page=1)
        try_cnt = 0
        while True and try_cnt<5:
            rsp = sess.get(url=run_obj.url, headers=run_obj.headers)
            try:
                page_data = rsp.text
            except Exception, e:
                print '***TMALL*** Get page ERROR:', run_obj.vardict['page'], e
                try_cnt += 1
                continue
            #step2. parse data
            try:
                myjson = "{" + page_data + "}"
                page_dict = json.loads(myjson)
            except Exception, e:
                print '***TMALL*** Parse page ERROR:', run_obj.vardict['page'], e
                page_dict = json.loads(page_data)
                if 'url' in page_dict:
                    login_url = page_dict['url']
                    self._login_tmall(sess, login_url)
                try_cnt += 1
                continue
            try:
                pagecnt = int(page_dict['rateDetail']['paginator']['lastPage'])+1
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
            print '***TMALL*** Get page ERROR:', run_obj.vardict['page'], e
            return None
        #step2. parse data
        try:
            myjson = "{" + page_data + "}"
            page_dict = json.loads(myjson)
        except Exception, e:
            print '***TMALL*** Parse page ERROR:', run_obj.vardict['page'], e
            page_dict = json.loads(page_data)
            if 'url' in page_dict:
                login_url = page_dict['url']
                self._login_tmall(sess, login_url)
            return None
        if len(page_dict) == 0:
            return None
        #step3. return dataset
        dataset = []
        page_dict = page_dict['rateDetail']['rateList']
        keys = ['id', 'displayUserNick', 'goldUser', 'rateDate', 'auctionSku', 'rateContent']
        innerkeys = ['commentid', 'username', 'golduser', 'ratedate', 'sku', 'content']
        for comment_row in page_dict:
            datarow = dict()
            datarow['sitename'] = run_obj.sitename
            datarow['prodname'] = run_obj.prodname
            datarow['produrl'] = run_obj.produrl
            datarow['itemid'] = run_obj.vardict['itemid']
            datarow['sellerid'] = run_obj.vardict['sellerid']
            for idx, k in enumerate(keys):
                dataitem = comment_row[k] if k in comment_row else ''
                datarow[innerkeys[idx]] = self._stringify_data(dataitem)
            dataset.append(datarow)
        return dataset

    def crawl_product_comment(self, sitename, prodname, produrl):
        itemid, sellerid = self._parse_item_seller_from_url(self.sess, sitename, produrl)
        crawler_q = deque([])
        if itemid and sellerid:
            #get page number
            pagecnt = self._get_page_number(self.sess, itemid, sellerid)
            for pageidx in xrange(1, pagecnt):
                run_obj = RunInfo(sitename, prodname, produrl, itemid=itemid, sellerid=sellerid, page=pageidx)
                crawler_q.append(run_obj)
            #getting data
            while crawler_q:
                run_obj = crawler_q.popleft()
                print '>>>TMALL>>> getting data %s, - page %d ...' % (run_obj.prodname, run_obj.vardict['page'])
                dataset = self._get_one_page_comment(self.sess, run_obj)
                if not dataset:
                    if run_obj.try_cnt<5:
                        run_obj.try_cnt += 1
                        if run_obj.sleepinterval==0:
                            run_obj.sleepinterval = 2
                        elif run_obj.sleepinterval<5:
                            run_obj.sleepinterval += 1
                        crawler_q.append(run_obj)
                else:
                    for datarow in dataset:
                        self.businessmodel.notify_model_info_received(av_data_module=['TMallModel'], **datarow)
                #slow down
                if run_obj.sleepinterval>0:
                    time.sleep(run_obj.sleepinterval)
            print 'Finish getting data!'
        else:
            print 'Url unrecognized: %s' % (produrl)
