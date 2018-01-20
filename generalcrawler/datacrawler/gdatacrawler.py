# -*- coding: utf-8 -*-
import os
import copy
import pickle
import time
import datetime
import yaml
import requests
from requests.models import Response as ReqResponse
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.common.proxy import Proxy


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


class GeneralCrawler(object):
    def __init__(self, spidername=''):
        self._session = requests.session()
        self._website_cfgs = None   # everthing in http.yaml
        self._callback_mods = None  # self._callback_mods[sitename][sitehttp] = [(cbobj,cbfunc),(genobj, genfunc)]
        self.session_used = True
        self.dtomgr = None
        self.spidername = spidername
        self._cookie_updated = False
        self.browser = None

    def _is_cookie_file_available(self, cookies_file_path):
        if os.path.exists(cookies_file_path):
            d_m = datetime.datetime.fromtimestamp(os.path.getmtime(cookies_file_path))
            date0 = datetime.datetime.today()
            if (date0 - d_m).days<6:
                return True
        return False

    def _replace_keymapping(self, data, datamaps):
        # data={"Referer": "http://www.xxxx.com?offset=%PAGEINDEX%"}  datamaps={"%PAGEINDEX%": "5"}
        # data={"Referer": "http://www.xxxx.com?offset=5"}
        if not isinstance(datamaps,dict):
            return data
        if isinstance(data,dict):
            for k, v in datamaps.iteritems():
                for kk, vv in data.iteritems():
                    if k in vv:
                        data[kk] = vv.replace(k, v)
        elif isinstance(data,str) or isinstance(data,unicode):
            for k, v in datamaps.iteritems():
                if k in data:
                    data = data.replace(k, v)
        return data

    def _get_siteinfo_from_sitename(self, sitename, sitehttp):
        #it will replace tenant info in payload by default
        if sitename in self._website_cfgs:
            siteinfo = self._website_cfgs[sitename]
            if sitehttp in siteinfo and 'http' in sitehttp:
                return copy.deepcopy(siteinfo[sitehttp])
        return None

    def _calc_proxy_profile(self, proxy_info, drivertype='phantomjs'):
        if drivertype=='chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--proxy-server=http://%s' % (proxy_info))
            return chrome_options
        elif drivertype=='firefox':
            profile = webdriver.FirefoxProfile()
            proxyobj = Proxy({
            'proxyType': ProxyType.MANUAL,
            'httpProxy': proxy_info,
            'ftpProxy': proxy_info,
            'sslProxy': proxy_info,
            'noProxy': '' # set this value as desired
            })
            profile.set_proxy(proxyobj)
            profile.update_preferences()
            return profile
        serv_args = ['--proxy=%s' % (proxy_info), '--proxy-type=http',]
        #'--proxy-auth=username:password'
        return serv_args

    def _selenium_data(self, siteinfo, now_data_maps):
        if siteinfo['method'] != 'selenium':
            return None, None
        proxies = None
        if 'proxy' in siteinfo:
            proxies = siteinfo['proxy']
        if self.browser is None:
            #dr = None
            if proxies:
                self.browser = webdriver.Firefox(firefox_profile=self._calc_proxy_profile(proxies, 'firefox'))
            else:
                self.browser = webdriver.Firefox()
        else:
            if len(self.browser.window_handles)>0:
                self.browser.switch_to.window(self.browser.window_handles[0])
        url = siteinfo['url'] if 'url' in siteinfo else ''
        payload = siteinfo['data'] if 'data' in siteinfo else ''
        locateinfo = siteinfo['locate'] if 'locate' in siteinfo else ''
        url = self._replace_keymapping(url, now_data_maps)
        self._replace_keymapping(payload, now_data_maps)
        #dr.get(url)
        self.browser.get(url)
        # locate element
        if locateinfo:
            dr = self.browser
            elems = dict()
            for ename, einfo in locateinfo.iteritems():
                try:
                    e_obj = WebDriverWait(dr, 60).until(html_element_exists(einfo['loctype'], einfo['keyword']))
                    elems[ename] = {'send_keys': (e_obj.send_keys,1), 'clear': (e_obj.clear,0), 'click': (e_obj.click,0)}
                except NoSuchElementException:
                    print 'Selenium failed to find element %s!!!' % (einfo['keyword'])
                    raw_input('Please operate manually, AFTER OPERATION SUCCESSFUL, press any key to continue!')
            # all element found, perform actions except click
            if len(elems)==len(locateinfo):
                only_one_click = None
                for enmae, einfo in locateinfo.iteritems():
                    if 'click' in einfo['action']:
                        only_one_click = elems[enmae]['click'][0]
                        continue
                    for act in einfo['action']:
                        func_tuple = elems[enmae][act]
                        if enmae in payload:
                            if func_tuple[1]:
                                func_tuple[0](payload[enmae])
                            else:
                                func_tuple[0]()
                        else:
                            func_tuple[0]()
                if only_one_click:
                    only_one_click()
                #raw_input('press any key IF LOGIN SUCCESSFUL, else please login manually first, then press any key!')
        #save cookies
        if not self._cookie_updated:
            dr = self.browser
            all_cookies = dr.get_cookies()
            cookies_dict = dict()
            for s_cookie in all_cookies:
                cookies_dict[s_cookie["name"]] = s_cookie["value"]
            self._session.cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            self._cookie_updated = True
        #return page source
        #pagedata = dr.page_source
        pagedata = copy.deepcopy(self.browser.page_source)
        #dr.quit()
        return pagedata

    def _post_data(self, siteinfo, now_data_maps):
        if siteinfo['method'] != 'post':
            return None
        request_dict = dict()
        url = siteinfo['url'] if 'url' in siteinfo else ''
        headers = siteinfo['headers'] if 'headers' in siteinfo else ''
        url = self._replace_keymapping(url, now_data_maps)
        self._replace_keymapping(headers, now_data_maps)
        if not url or not headers:
            return None
        else:
            request_dict['url'] = url
            request_dict['headers'] = headers
        av_post_kind = ['data', 'json']
        for post_dkind in av_post_kind:
            if post_dkind in siteinfo:
                payload = siteinfo[post_dkind]
                self._replace_keymapping(payload, now_data_maps)
                if payload:
                    request_dict[post_dkind] = payload
                #only one kind of data post is support(data=payload, or json=payload)
                break
        if 'proxy' in siteinfo:
            proxies = {'http': 'http://%s' % (siteinfo['proxy']), 'https': 'http://%s' % (siteinfo['proxy'])}
            request_dict['proxies'] = proxies
        # make request
        if self.session_used:
            rsp = self._session.post(**request_dict)
        else:
            rsp = requests.post(**request_dict)
        return rsp

    def _get_data(self, siteinfo, now_data_maps):
        if siteinfo['method'] != 'get':
            return None
        request_dict = dict()
        url = siteinfo['url'] if 'url' in siteinfo else ''
        headers = siteinfo['headers'] if 'headers' in siteinfo else ''
        url = self._replace_keymapping(url, now_data_maps)
        self._replace_keymapping(headers, now_data_maps)
        if not url or not headers:
            return None
        else:
            request_dict['url'] = url
            request_dict['headers'] = headers
        payload = siteinfo['data'] if 'data' in siteinfo else ''
        self._replace_keymapping(payload, now_data_maps)
        if payload:
            request_dict['params'] = payload
        if 'proxy' in siteinfo:
            proxies = {'http': 'http://%s' % (siteinfo['proxy']), 'https': 'http://%s' % (siteinfo['proxy'])}
            request_dict['proxies'] = proxies
        # make request
        if self.session_used:
            rsp = self._session.get(**request_dict)
        else:
            rsp = requests.get(**request_dict)
        return rsp

    def _login_website(self, sitename, sitehttp, now_data_maps):
        #cookies
        app_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tenant_name = now_data_maps['UXIXD'] if 'UXIXD' in now_data_maps else ''
        cookies_file_path = os.path.sep.join([app_base_dir, 'spiders', self.spidername, 'cookies', tenant_name + '_' + sitename + '.coo'])
        if self._is_cookie_file_available(cookies_file_path):
            with open(cookies_file_path) as cookief:
                cookies_data = requests.utils.cookiejar_from_dict(pickle.load(cookief))
                self._session = requests.session()
                self._session.cookies = cookies_data
            return True
        else:
            siteinfo = self._get_siteinfo_from_sitename(sitename, sitehttp)
            if siteinfo:
                self._session = requests.session()
                funcmap = {'post': self._post_data, 'get': self._get_data, 'selenium': self._selenium_data}
                login_rsp = funcmap[siteinfo['method']](siteinfo, now_data_maps)
                #generate cookies
                self.end_request()
                cookies_dict = requests.utils.dict_from_cookiejar(self._session.cookies)
                #save cookies
                with open(cookies_file_path, 'w') as cookief:
                    pickle.dump(cookies_dict, cookief)
                return login_rsp
        return None

    def load_http_config(self, http_cfg_file_name):
        if os.path.exists(http_cfg_file_name):
            self._website_cfgs = yaml.load(open(http_cfg_file_name,'r'))
            return True
        return False

    def attach_dto(self, dtomgr=None):
        self.dtomgr = dtomgr

    def exec_callback(self, data, run_info):
        siteinfo = self._get_siteinfo_from_sitename(run_info[1], run_info[2])
        if isinstance(data, ReqResponse):
            if 'datatype' in siteinfo:
                if siteinfo['datatype']=='content':
                    data = data.content
                else:
                    data = data.text
            else:
                data = data.text
        return self.dtomgr.exec_callback(data, run_info)

    def process_request(self, sitename, sitehttp, now_data_maps, sleepinterval=0):
        if sitehttp=='login_http':
            return self._login_website(sitename, sitehttp, now_data_maps)
        siteinfo = self._get_siteinfo_from_sitename(sitename, sitehttp)
        if sleepinterval:
            time.sleep(sleepinterval)
        funcmap = {'post': self._post_data, 'get': self._get_data, 'selenium': self._selenium_data}
        return funcmap[siteinfo['method']](siteinfo, now_data_maps)

    def end_request(self):
        if self.browser is not None:
            self.browser.quit()
            self.browser = None