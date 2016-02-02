#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import time

class snowball_monitor:
    # variables

    request_tag = 0

    proxy_tag = 0

    adjustment_tag = 0

    pa_history = []

    basic_url = 'http://xueqiu.com/cubes/rebalancing/history.json'

    b2_url = 'http://xueqiu.com/v4/stock/quotec.json?code=VNM%2CYINN%2CYANG%2CFXP&_='

    group_list = [
        {'id': 0, 'url': 'ZH771938', 'name': '冷刃不血3英吉沙'}
    ]

    cookies = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
    }

    headers1 = {
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': '*/*',
        'Referer': 'http://xueqiu.com/',
        'Accept-Language': 'zh-CN',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Host': 'xueqiu.com',
        'DNT': '1',
        'Connection': 'Keep-Alive'
    }

    headers2 = {
        'Accept': '*/*',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'http://xueqiu.com/',
        'Accept-Language': 'zh-CN',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Host': 'xueqiu.com',
        'DNT': '1',
        'Connection': 'Keep-Alive',
        'Pragma': 'no-cache'
    }

    Proxy_list = [
        'http://114.215.141.103:3128',
        'http://115.28.73.197:3128'
    ]

    p = {'areacode' : '86',
         'username' : 'jizy10@163.com',
         'password' : 'AD0C1F9A32F1B60F2154C76733F14CD0',
         'remember_me' : 'on'
        }

    # functions

    def __init__(self):
        self.initialize_cookies()
        self.login()
        self.initialize_position_adjustment_history()

    def initialize_cookies(self):
        self.s = requests.Session()
        r = self.s.get('http://www.xueqiu.com', headers = self.headers)
        self.cookies = r.cookies

    def initialize_position_adjustment_history(self):
        self.get_position_adjustment_history()


    def get_position_adjustment_history(self):
        for group in self.group_list:
            group_history = self.get_group_adjustment_history(group)
            self.pop_group_history(group['id'], group_history)

    def get_group_adjustment_history(self, group, need_check = None):
        params = self.load_params(group['url'])
        success = False
        while success is not True:
            try:
                r = self.s.get(self.basic_url, params = params, headers = self.headers, timeout = 6)
            except:
                print('sb')
            else:
                success = True
        content = r.json()
        group_history = self.mine_group_history(group['id'], content, need_check = need_check)
        return group_history

    def mine_group_history(self, group_id, content, need_check):
        ga_id = content['list'][0]['id']
        if need_check:
            if ga_id == self.pa_history[group_id]['id']:
                return None
        local_time = time.asctime(time.localtime(int(content['list'][0]['created_at'])/1000))
        group_history_raw = content['list'][0]['rebalancing_histories']
        group_history = {
            'id':ga_id,
            'group_id':group_id,
            'group_name':self.group_list[group_id]['name'],
            'time':local_time,
            'history': {}
        }
        for stock in group_history_raw:
            group_history['history'][stock['stock_symbol']] = {'name'         : stock['stock_name'],
                                                               'price'        : stock['price'],
                                                               'prev_weight'  : stock['prev_weight'],
                                                               'target_weight': stock['target_weight']
            }
        if need_check:
            self.pa_history[group_id] = group_history
        return group_history

    def pop_group_history(self, group_id, group_history):
        if len(self.pa_history) == group_id:
            self.pa_history.append(group_history)
        else:
            self.pa_history[group_id] = group_history

    def load_params(self, group_url):
        params = {'cube_symbol': group_url,
                  'count'      : '20',
                  'page'       : '1'
        }
        return params

    def load_proxies(self):
        if self.proxy_tag == len(self.Proxy_list):
            self.proxy_tag = 0
            return None
        self.proxy_tag += 1
        return {'http': self.Proxy_list[self.proxy_tag-1]}

    def login(self):
        self.s.get('http://xueqiu.com/service/csrf?api=http%3A%2F%2Fxueqiu.com%2Fuser%2Flogin HTTP/1.1', headers = self.headers)
        self.s.post('http://xueqiu.com/user/login', data = self.p, headers = self.headers2)

    def get_new_adjustment(self):
        self.adjustment_tag += 1
        if self.adjustment_tag == len(self.group_list):
            self.adjustment_tag = 0
        group_history = self.get_group_adjustment_history(self.group_list[self.adjustment_tag], True)
        return group_history

if __name__ == '__main__':
    print('Snowball monitor successfully loaded.')