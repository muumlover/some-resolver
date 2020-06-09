#!/usr/bin/env python
# encoding: utf-8

"""
@Time    : 2020/6/8 19:42
@Author  : Sam Wang
@Email   : muumlover@live.com
@Blog    : https://blog.ronpy.com
@Project : plugin.video.tencent-video
@FileName: tx_player.py
@Software: PyCharm
@license : (C) Copyright 2020 by Sam Wang. All rights reserved.
@Desc    :

"""
import re
import time
from functools import reduce
from random import *
from string import hexdigits
from urllib.parse import urlencode, parse_qs

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from pywasm_easy import WasmEasy, WasmEnv, WasmTable, WasmMemory


class Document:
    def __init__(self, url):
        self.URL = url
        self.referrer = ''


class Window:
    def __init__(self):
        self.navigator = Navigator()


class Navigator:
    def __init__(self):
        self.userAgent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'
        self.appCodeName = 'Mozilla'
        self.appName = 'Netscape'
        self.platform = 'Win32'


class Wasm(WasmEasy):
    def __init__(self, player):
        env = WasmEnv(self)
        env.update({
            'DYNAMICTOP_PTR': 7968,
            'tempDoublePtr': 7952,
            'STACKTOP': 7984,
            'STACK_MAX': 5250864,

            'memoryBase': 1024,
            'tableBase': 0,

            'memory': WasmMemory(256),
            'table': WasmTable(99),
        })
        super().__init__('ckey.wasm', env)
        self.player = player

    def stack_alloc(self, size):
        return self.wa_stackAlloc(size)

    @WasmEasy.wasm_function(paras=[int], ret=int)
    def wa_stackAlloc(self, *args):
        return self.wasm_call('stackAlloc', args)

    @WasmEasy.wasm_function(paras=[int], ret=int)
    def wa__malloc(self, *args):
        return self.wasm_call('_malloc', args)

    @WasmEasy.wasm_function(paras=[int, str, str, str, str, int], ret=str)
    def wa__getkey(self, *args):
        return self.wasm_call('_getckey', args)

    def cb_getTotalMemory(self, store, *args, **kwargs):
        assert self
        return 5250864

    def cb__get_unicode_str(self, store, *args, **kwargs):
        data = '|'.join([
            self.player.document.URL[:48],
            self.player.window.navigator.userAgent.lower()[:48],
            self.player.document.referrer[:48],
            self.player.window.navigator.appCodeName,
            self.player.window.navigator.appName,
            self.player.window.navigator.platform
        ])
        data_len = len(data) + 1
        # data_ptr self.wa__malloc(data_len)
        data_ptr = self.wa_stackAlloc(data_len)
        self.memcpy(data, data_ptr, data_len + 1)
        return data_ptr


class TxPlayer:
    proxy_url = r'https://vd.l.qq.com/proxyhttp'
    appVer = '3.5.57'

    def __init__(self, url, navigator=None):
        url_split = url.split('/')
        self._host = url_split[2]
        self._cid = url_split[-2]
        self._vid = url_split[-1].split('.')[0]
        self._guid = self.create_guid()
        self._player_id = self.create_guid()

        self.document = Document(url)
        self.window = Window()
        if navigator:
            self.window.navigator = navigator

        self.wasm = Wasm(self)

    @property
    def tm(self):
        return int(time.time())

    @property
    def cid(self):
        return self._cid

    @property
    def vid(self):
        return self._vid

    @property
    def business_id(self):
        """
        app:
            wechat 6
            mqq 17
        web
            weixin.qq.com 6
            v.qq.com film.qq.com 1
            news.qq.com 2
            qzone.qq.com 3
            t.qq.com 5
            3g.v.qq.com 8
            m.v.qq.com 10
            3g.qq.com 12
        other 7
        :return:
        """
        business_id = {
            'wechat': 6,
            'mqq': 17,

            'weixin.qq.com': 6,
            'v.qq.com': 1,
            'film.qq.com': 1,
            'news.qq.com': 2,
            'qzone.qq.com': 3,
            't.qq.com': 5,
            '3g.v.qq.com': 8,
            'm.v.qq.com': 10,
            '3g.qq.com': 12,
        }
        return business_id[self._host] if self._host in business_id else 7

    @property
    def os_name(self):
        re_maps = {
            'android_1': r'android[\s\/]([\d\.]+)',
            'android_2': r'android',
            'android_3': r'MIDP-',
            'ipod_1': r'iPod\stouch;\sCPU\siPhone\sos\s([\d_]+)',
            'ipod_100': r'iPod.*os\s?([\d_\.]+)',
            'iphone': r'iPhone;\sCPU\siPhone\sos\s([\d_]+)',
            'iphone_100': r'iPhone.*os\s?([\d_\.]+)',
            'ipad_1': r'ipad;\scpu\sos\s([\d_]+)',
            'ipad_2': r'ipad([\d]+)?',
            'windows': r'windows\snt\s([\d\.]+)',
            'mac': r'Macintosh.*mac\sos\sx\s([\d_\.]+)',
            'linux': r'Linux',
            'nintendo': r'Nintendo Switch'
        }
        for key, re_str in re_maps.items():
            if re.search(re_str, self.window.navigator.userAgent, flags=re.I):
                return key.split('_')[0]

    @property
    def device_id(self):
        """
        getDeviceId
        navigator.userAgent
        ipad 1
        windows 2
            Touch 8
            Phone 7
        android 5
            mobile 3
        iphone 4
        mac 9
        other 10
        :return:
        """
        user_agent = self.window.navigator.userAgent
        os_name = self.os_name
        if os_name == 'ipad':
            return 1
        elif os_name == 'windows':
            if re.search(r'Touch', user_agent, flags=re.I):
                return 8
            elif re.search(r'Phone', user_agent, flags=re.I):
                return 7
            else:
                return 2
        elif os_name == 'android':
            if 'mobile' in user_agent:
                return 3
            else:
                return 5
        elif os_name == 'iphone':
            return 4
        elif os_name == 'mac':
            return 9
        else:
            return 10

    @property
    def std_from(self):
        """
        caixin.com v1093
        ke.qq.com v1101
        mobile v1010
            iphone ipod v3010
                view.inews.qq.com v3110
            ipad v4010
                view.inews.qq.com v4110
        android v5010
            tablet v6010
            view.inews.qq.com v5110
        IEMobile v7010
        other v1010
        :return:
        """
        return 'v1010'

    @property
    def platform(self):
        return int(10 ** 4 * self.business_id + 100 * self.device_id + 1)

    @property
    def flow_id(self):
        return self._player_id + '_' + str(self.platform)

    @property
    def guid(self):
        return self._guid

    @property
    def player_id(self):
        return self._player_id

    @staticmethod
    def create_guid(length=32):
        """
        createGUID in txplayer.js
        :return:
        """
        return reduce(lambda x, y: x + choice(hexdigits[:16]), range(length), '')

    @property
    def v_info_param(self):
        return urlencode(self._v_info_param_raw)

    @property
    def ad_param(self):
        return urlencode(self._ad_param_raw)

    @property
    def c_key(self):
        return self._player_id

    @property
    def _c_key_8_1(self):
        """
        https://www.52pojie.cn/forum.php?mod=viewthread&tid=859308
        :return:
        """
        ub = self.document.URL[0: 48]  # https://v.qq.com/x/cover/79npj83isb0ylvq/l0029fi58lh.html
        vb = self.window.navigator.userAgent.lower()[0: 48]
        yb = self.window.navigator.appCodeName
        zb = self.window.navigator.appName
        qb = self.window.navigator.platform
        _loc1 = ub + "|" + vb + "|" + "https://v.qq.com/" + "|" + yb + "|" + zb + "|" + qb
        _loc2_ = self.guid
        _loc3_ = "|" + self.vid + "|" + str(self.tm) + "|mg3c3b04ba|3.5.57|" + _loc2_ + "|10201|" + _loc1 + "|00|"
        _loc4_ = 0
        for char in _loc3_:
            # print(ord(char))
            if 57 == ord(char):
                v = 1
            _loc4_ = (_loc4_ * 31 + ord(char))
            _loc4_ &= 0xFFFFFFFF
            # print(_loc4_ if _loc4_ < 0x80000000 else _loc4_ - 0x100000000)
        _loc5_ = "|" + str(_loc4_ if _loc4_ < 0x80000000 else _loc4_ - 0x100000000) + _loc3_
        key = b'\x4f\x6b\xda\xa3\x9e\x2f\x8c\xb0\x7f\x5e\x72\x2d\x9e\xde\xf3\x14'
        iv = b'\x01\x50\x4a\xf3\x56\xe6\x19\xcf\x2e\x42\xbb\xa6\x8c\x3f\x70\xf9'
        aes = AES.new(key, AES.MODE_CBC, iv)
        encrypted_text = aes.encrypt(pad(_loc5_.encode(), 16))
        return encrypted_text.hex()

    @property
    def _c_key_9_1(self):
        return self.wasm.wa__getkey(self.platform, self.appVer, self.vid, '', self.guid, self.tm)

    @property
    def _v_info_param_raw(self):
        """
        vinfoparam
        :return:
        """
        return {
            'appVer': self.appVer,
            'cKey': self._c_key_9_1,
            'charge': 0,
            'defaultfmt': 'auto',
            'defn': '',
            'defnpayver': '1',
            'defsrc': '1',
            'dtype': 3,
            'ehost': self.document.URL,
            'encryptVer': '9.1',
            'fhdswitch': 0,
            'flowid': self.flow_id,
            'guid': self.guid,
            'host': 'v.qq.com',
            'isHLS': 1,
            'otype': 'ojson',
            'platform': self.platform,
            'refer': 'v.qq.com',
            'sdtfrom': self.std_from,
            'show1080p': 1,
            'sphttps': 1,
            'spwm': '4',
            'tm': '1591190268',
            'vid': self.vid,
            'sphls': 2,
            'spgzip': 1,
            'dlver': 2,
            'logintoken': '{"main_login":"","openid":"","appid":"","access_token":"","vuserid":"","vusession":""}',
            'drm': '32',
            'hdcp': '0',
            'spau': '1',
            'spaudio': '15',
            'fp2p': '1',
            'spadseg': '3'
        }

    @property
    def _ad_param_raw(self):
        return {
            'pf': 'in',
            'ad_type': 'LD|KB|PVL',  # unquote('LD%7CKB%7CPVL'), #
            'pf_ex': 'pc',
            'url': self.document.URL,
            'refer': self.document.URL,
            'ty': 'web',
            'plugin': '1.0.0',
            'v': self.appVer,
            'coverid': self.cid,
            'vid': self.vid,
            'pt': '',
            'flowid': self.flow_id,
            # 'vptag': 'jimu.210588.zt',  # '',
            'pu': '0',
            'chid': '0',
            'adaptor': '2',
            'dtype': '1',
            'live': '0',
            'resp_type': 'json',
            'guid': self.guid,
            'req_type': '1',
            'from': '0',
            'appversion': '1.0.145',
            'platform': self.platform,
            'tpid': '9'
        }

    def get_info(self):

        data1 = {
            'buid': 'vinfoad',
            'adparam': self.ad_param,
            'vinfoparam': self.v_info_param
        }
        data2 = {
            "buid": "vinfoad",
            "adparam": "pf=in&ad_type=LD%7CKB%7CPVL&pf_ex=pc&url=https%3A%2F%2Fv.qq.com%2Fx%2Fcover%2Fmzc00200ps708z1%2Fq003305dzmd.html&refer=https%3A%2F%2Fv.qq.com%2Fx%2Fcover%2Fmzc00200ps708z1%2Fq003305dzmd.html&ty=web&plugin=1.0.0&v=3.5.57&coverid=mzc00200ps708z1&vid=q003305dzmd&pt=&flowid=1c048b037253d0af68318883eb20a8d1_10201&vptag=&pu=0&chid=0&adaptor=2&dtype=1&live=0&resp_type=json&guid=ecef7a974423ebdd638f94c9d5ef846f&req_type=1&from=0&appversion=1.0.145&platform=10201&tpid=9",
            "vinfoparam": "charge=0&defaultfmt=auto&otype=ojson&guid=ecef7a974423ebdd638f94c9d5ef846f&flowid=1c048b037253d0af68318883eb20a8d1_10201&platform=10201&sdtfrom=v1010&defnpayver=1&appVer=3.5.57&host=v.qq.com&ehost=https%3A%2F%2Fv.qq.com%2Fx%2Fcover%2Fmzc00200ps708z1%2Fq003305dzmd.html&refer=v.qq.com&sphttps=1&tm=1591684692&spwm=4&logintoken=%7B%22main_login%22%3A%22%22%2C%22openid%22%3A%22%22%2C%22appid%22%3A%22%22%2C%22access_token%22%3A%22%22%2C%22vuserid%22%3A%22%22%2C%22vusession%22%3A%22%22%7D&vid=q003305dzmd&defn=&fhdswitch=0&show1080p=1&isHLS=1&dtype=3&sphls=2&spgzip=1&dlver=2&drm=32&hdcp=0&spau=1&spaudio=15&defsrc=1&encryptVer=9.1&cKey=gPOfDnKs0xR79ZEItZs_lpJX5WB4a2CdS8k7nPEPVaqtHEZQ1c_W6myJ8hQcnmDCHsArH9_WPjs52vPBr-xE-uhvZyEMY131vUh1H4pgCXe2Op8F_DerfPIt2wsxrvF8_Xw1EERXEtqMluNDEH6IC8EOljLQ2VfW2sTdospNPlD9535CNT9iSo3cLRH93ogtX_ObeZBTEOuKEsbtjkFpGl3F3IxmISJc_8dRIBruTik-e4rt0isxZAXexKqWDJGxu2q1S-zTxiZM-O02fh9Xu3kOoHdFgRcDS9b_UVPeTqc_h4UjOGuwnte5LCRPWcRSxKIGBgYGBgYlsvI7&fp2p=1&spadseg=3"
        }
        qsa1 = {k: v[0] for k, v in parse_qs(data1['adparam']).items()}
        qsa2 = {k: v[0] for k, v in parse_qs(data2['adparam']).items()}
        qsv1 = {k: v[0] for k, v in parse_qs(data1['vinfoparam']).items()}
        qsv2 = {k: v[0] for k, v in parse_qs(data2['vinfoparam']).items()}
        differa = set(qsa1.items()) ^ set(qsa2.items())
        differv = set(qsv1.items()) ^ set(qsv2.items())
        res = requests.post(
            url=self.proxy_url,
            json=data2,
            headers={
                'Host': 'vd.l.qq.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'text/plain',
                'Content-Length': '1500',
                'Origin': 'https://v.qq.com',
                'Connection': 'keep-alive',
                'Referer': 'https://v.qq.com/x/cover/mzc00200ps708z1/q003305dzmd.html',
                'Cache-Control': 'max-age=0, no-cache',
                'Pragma': 'no-cache',
                'TE': 'Trailers',
            },
        )
        res = requests.post(
            url=self.proxy_url,
            json=data1,
            headers={
                'User-Agent': self.window.navigator.userAgent,
                'Content-Type': 'text/plain',
            },
        )
        return res
