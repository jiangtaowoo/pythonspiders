# -*- coding: utf-8 -*-
import random
from meta.metacls import Singleton
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.common.proxy import Proxy


class ProxyPool(object):
    __metaclass__ = Singleton

    def __init__(self):
        self._proxies = []

    def load_proxy(self):
        pass

    def add_proxy(self, p):
        self._proxies.append(p)

    def get_proxy(self):
        if self._proxies:
            return random.choice(self._proxies)
        return None

    def get_request_proxy(self):
        proxies = self.get_proxy()
        if proxies:
            return {'proxies': {'http': proxies, 'https': proxies}}
        return None

    def get_selenium_proxy_profile(self, drivertype='phantomjs'):
        proxy_info = self.get_proxy()
        if not proxy_info:
            return None
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
