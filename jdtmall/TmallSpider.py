# _*_ coding:utf-8 _*_
import random
from collections import deque
import requests
import json
import time
import random
import os
import re
#from requests.models import Response as ReqResponse
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import yaml
from productmodel import ModelBase
from baseadaptor import AdaptorSqlite


class html_element_exists(object):
  def __init__(self, bywhat, id_or_name_or_xpath):
    self.bywhat = bywhat
    self.id_name_xpath = id_or_name_or_xpath

  def __call__(self, driver):
    try:
        if self.bywhat == 'id':
            element = driver.find_element_by_id(self.id_name_xpath)   # Finding the referenced element
        elif self.bywhat == 'name':
            element = driver.find_element_by_name(self.id_name_xpath)   # Finding the referenced element
        elif self.bywhat == 'xpath':
            element = driver.find_element_by_xpath(self.id_name_xpath)   # Finding the referenced element
        else:
            return False
    except NoSuchElementException:
        return False
    return element


class RunInfo(object):
    cfg_path = os.path.sep.join([os.path.dirname(os.path.abspath(__file__)),'config'])
    user_agent_list = yaml.load( open(os.path.sep.join([cfg_path, 'useragent.yaml'])) )
    interval_info = yaml.load( open(os.path.sep.join([cfg_path, 'sleepinterval.yaml'])) )

    def __init__(self, sitename='', prodname='', produrl='', itemid=0, sellerid=0, pageidx=0):
        self.headers = {'User-Agent': random.choice(self.user_agent_list)}
        self.url = ''
        self.sleepinterval = int(self.interval_info['tmall.com']['sleep'])  if 'tmall.com' in self.interval_info else 0
        self.try_cnt = 0
        self.base_url = 'https://rate.tmall.com/list_detail_rate.htm?itemId=%s&sellerId=%s&currentPage=%d'
        self.sitename = sitename
        self.prodname = prodname
        self.produrl = produrl
        self.page = pageidx
        self.itemid = itemid
        self.sellerid = sellerid
        self._gen_url(itemid, sellerid, pageidx)

    def _gen_url(self, itemid, sellerid, pageidx):
        self.url = self.base_url % (str(itemid), str(sellerid), pageidx)


class TMallCrawler(object):
    def __init__(self):
        self.sess = requests.session()
        app_base_dir = os.path.dirname(os.path.abspath(__file__))
        basepath = os.path.sep.join([app_base_dir,'config'])
        self.businessmodel = ModelBase()
        self.sqliteadaptor = AdaptorSqlite(spidername='tmall', dbname='comments.db')
        self.businessmodel.load_model_config(basepath + os.path.sep + 'models.yaml')
        self.sqliteadaptor.load_db_config(basepath + os.path.sep + 'dbs.yaml')
        self.businessmodel.regist_persist_adaptor(self.sqliteadaptor)
        self.accounts = yaml.load(open(basepath + os.path.sep + 'tenants.yaml'))
        if 'ACCOUNT' in self.accounts:
            self.accounts = self.accounts['ACCOUNT']
        else:
            self.accounts = None

    def _stringify_data(self, data):
        if isinstance(data, str) or isinstance(data, unicode):
            return data
        return str(data)

    def _save_browser_cookie(self, sess, browser):
        all_cookies = browser.get_cookies()
        cookies_dict = dict()
        for s_cookie in all_cookies:
            cookies_dict[s_cookie["name"]] = s_cookie["value"]
        sess.cookies = requests.utils.cookiejar_from_dict(cookies_dict)

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
                run_obj = RunInfo()
                rsp = sess.get(url=url, headers=run_obj.headers)
                if rsp.status_code==200:
                    useridinfo = re.findall(r'userid=\d+',rsp.text)
                    if len(useridinfo):
                        sellerid = useridinfo[0][7:]
        if itemid and sellerid:
            return itemid, sellerid
        return None, None            

    def _get_page_number(self, sess, itemid, sellerid): #itemId 是商品的id, sellerId是卖家的id
        run_obj = RunInfo('nothing', 'nothing', 'nothing', itemid, sellerid, 1)
        try_cnt = 0
        while True and try_cnt<5:
            rsp = sess.get(url=run_obj.url, headers=run_obj.headers)
            try:
                page_data = rsp.text
            except Exception, e:
                print '*** Get page ERROR:', run_obj.page, e
                try_cnt += 1
                continue
            #step2. parse data
            try:
                myjson = "{" + page_data + "}"
                page_dict = json.loads(myjson)
            except Exception, e:
                print '*** Parse page ERROR:', run_obj.page, e
                page_dict = json.loads(page_data)
                if 'url' in page_dict:
                    login_url = page_dict['url']
                    self._login_tmall(sess, login_url)
                try_cnt += 1
                continue
            try:
                pagenum = int(page_dict['rateDetail']['paginator']['lastPage'])+1
                return pagenum
            except:
                try_cnt += 1
        return 0

    def _get_one_page_comment(self, sess, run_obj):
        #step1. get page data
        rsp = sess.get(url=run_obj.url, headers=run_obj.headers)
        try:
            page_data = rsp.text
        except Exception, e:
            print '*** Get page ERROR:', run_obj.page, e
            return None
        #step2. parse data
        try:
            myjson = "{" + page_data + "}"
            page_dict = json.loads(myjson)
        except Exception, e:
            print '*** Parse page ERROR:', run_obj.page, e
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
            datarow['itemid'] = run_obj.itemid
            datarow['sellerid'] = run_obj.sellerid
            for idx, k in enumerate(keys):
                dataitem = comment_row[k] if k in comment_row else ''
                datarow[innerkeys[idx]] = self._stringify_data(dataitem)
            dataset.append(datarow)
        return dataset

    def crawl_tmall_comment(self, sitename, prodname, produrl):
        itemid, sellerid = self._parse_item_seller_from_url(self.sess, sitename, produrl)
        crawler_q = deque([])
        if itemid and sellerid:
            #get page number
            pagenum = self._get_page_number(self.sess, itemid, sellerid)
            for page_num in xrange(1, pagenum):
                run_obj = RunInfo(sitename, prodname, produrl, itemid, sellerid, page_num)
                crawler_q.append(run_obj)
            #getting data
            while crawler_q:
                run_obj = crawler_q.popleft()
                print '>>> getting data %s, - page %d ...' % (run_obj.prodname, run_obj.page)
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
