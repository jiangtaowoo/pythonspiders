# -*- coding: utf-8 -*-
import os
import copy
import pickle
import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from meta.setting import ConfigManager
from meta.proxy import ProxyPool


class html_exists(object):
    def __init__(self, bywhat, byexpr):
        self.bywhat = bywhat
        self.byexpr = byexpr

    def __call__(self, driver):
        element = None
        if self.bywhat == 'id':
            element = driver.find_element_by_id(self.byexpr)
        elif self.bywhat == 'name':
            element = driver.find_element_by_name(self.byexpr)
        elif self.bywhat == 'xpath':
            element = driver.find_element_by_xpath(self.byexpr)
        return element


class WebCrawler(object):
    """
    1. 管理cookie文件
    2. 发送request并获取响应
    """
    def __init__(self, use_session=True, use_cookie=False):
        self._sess = requests.session()
        self._use_session = use_session
        self._use_cookie = use_cookie
        self._cookie_loaded = False

    @property
    def sessioned(self):
        return self._use_session

    @sessioned.setter
    def sessioned(self, value):
        self._use_session = value

    @property
    def cookied(self):
        return self._use_cookie

    @cookied.setter
    def cookied(self, value):
        self._use_cookie = value

    @staticmethod
    def _get_cookie_file(runner):
        confm = ConfigManager()
        cfgdir = confm.get_config_path(confm.spidername)
        loginid = runner.get_loginid()
        cookie_file = os.sep.join([cfgdir, '{0}_{1}.cookie'.format(loginid,
                                                runner.id.replace('>','_'))])
        return cookie_file

    def _load_cookie(self, runner):
        cookie_file = WebCrawler._get_cookie_file(runner)
        if os.path.exists(cookie_file):
            dm = datetime.datetime.fromtimestamp(os.path.getmtime(cookie_file))
            d0 = datetime.datetime.today()
            if (d0 - dm).days<4:
              with open(cookie_file) as cookief:
                  cookies = requests.utils.cookiejar_from_dict(pickle.load(cookief))
                  self._sess.cookies = cookies
              return True
        return False

    def _save_cookie(self, runner, browser):
        if self._use_cookie:
            if browser:
                cookies ={cook['name']:cook['value'] for cook in browser.get_cookies()}
            else:
                cookies = requests.utils.dict_from_cookiejar(self._sess.cookies)
            #save cookies
            cookie_file = WebCrawler._get_cookie_file(runner)
            with open(cookie_file, 'w') as cookief:
                pickle.dump(cookies, cookief)
            self._cookie_loaded = True
            return True
        return False

    def _selenium_request(self, runner):
        proxies = ProxyPool().get_selenium_proxy_profile('firefox')
        if proxies:
            browser = webdriver.Firefox(firefox_profile=proxies)
        else:
            browser = webdriver.Firefox()
        browser.get(runner.get_url())
        locateinfo = runner.get_selenium_locate()
        # locate element
        if locateinfo:
            try:
                for locateitem in locateinfo:
                    for ename, einfo in locateitem.iteritems():
                        data = runner.get_data_viakey(ename)
                        e_obj = WebDriverWait(browser, 60).until(
                            html_exists(einfo['type'], einfo['key']))
                        for action in einfo['action']:
                            func = getattr(e_obj, action)
                            if runner.is_selenium_noparam_proc(action):
                                func()
                            else:
                                func(data)
            except NoSuchElementException:
                print('Selenium failed to find element {0}!!!'.format(einfo['key']))
                raw_input('Please operate manually, AFTER OPERATION SUCCESSFUL,\
                           press any key to continue!')
        #save cookie if neccesary
        if self._use_cookie and not self._cookie_loaded:
            self._save_cookie(runner, browser)
        #return page source
        page = copy.deepcopy(browser.page_source)
        browser.quit()
        return page

    def process_request(self, runner):
        #load cookie when login
        if self._use_cookie and not self._cookie_loaded:
            self._cookie_loaded = self.load_cookie(runner)
        #request page
        method = runner.get_request_method()
        if method=='selenium':
            rsp = self._selenium_request(runner)
        else:
            request_dict = runner.get_reqeust_kwargs()
            proxies = ProxyPool().get_request_proxy()
            if proxies:
                request_dict.update(proxies)
            if self._use_session:
                req_proc = getattr(self._sess, method)
            else:
                req_proc = getattr(requests, method)
            rsp = req_proc(**request_dict)
        #save cookie if neccesary
        if self._use_cookie and not self._cookie_loaded:
            self._save_cookie(runner, None)
        yield rsp
        #sleep
        interval = runner.get_sleep()
        if interval:
            time.sleep(interval)
