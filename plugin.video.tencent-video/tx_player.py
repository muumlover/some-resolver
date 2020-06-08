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

import time
from functools import reduce
from random import *
from string import hexdigits
from urllib.parse import urlencode, quote

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class Window:
    def __init__(self, url):
        self.platform = 'None'
        self.appName = 'None'
        self.appCodeName = 'None'
        self.referrer = ''
        self.url = url
        self.userAgent = 'None'

    pass


class TxPlayer:
    proxy_url = r'https://vd.l.qq.com/proxyhttp '
    appVer = '3.5.57'

    def __init__(self, url):
        self.window = Window(url)
        url_split = self.window.url.split('/')
        self._host = url_split[2]
        self._cid = url_split[-2]
        self._vid = url_split[-1].split('.')[0]
        self._guid = self.create_guid()
        self._player_id = self.create_guid()

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
    def device_id(self):
        """
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
        return 2

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
        ub = self.window.url[0: 48]  # https://v.qq.com/x/cover/79npj83isb0ylvq/l0029fi58lh.html
        vb = self.window.userAgent.lower()[0: 48]
        yb = self.window.appCodeName
        zb = self.window.appName
        qb = self.window.platform
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
        return ''

    @property
    def _v_info_param_raw(self):
        """
        vinfoparam
        :return:
        """
        return {
            'appVer': self.appVer,
            'cKey': 'zWwn3j8za8R7xJEItZs_lpJX5WB4a2CdS8k7lH2nVaqtHEZQ1c_W6myJ8hQDnmDDHYlsFcmCbTvK2vPBr-xE-uhvZyEMY131vUh1H4pgCXe2OpAF-Wzte7F4kwln76xq_nwqEERWEZPLluNDEH6IC8EOljLQ2VfW2sTdospNPlD9535CNT9iSo3cLRH93ogtX_ObeZBTEOuLEsb5t1pjAAuGkoYGNScB_8lMahr0SD1lJfkplb5LtU1mpdrzcMbY1XniNzyOKljQ8AICTCwy2R1qtnUZ1UpVTYn8AlDeRPU8hdlveILQyBf7H2d1On-HRfi3QCaTtKylFETKdNYef_9yKwUFBQUFaxGsyQ',
            'charge': 0,
            'defaultfmt': 'auto',
            'defn': '',
            'defnpayver': '1',
            'defsrc': '1',
            'dtype': 3,
            'ehost': quote(self.window.url, safe=''),
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
            'logintoken': '%7B%22main_login%22%3A%22%22%2C%22openid%22%3A%22%22%2C%22appid%22%3A%22%22%2C%22access_token%22%3A%22%22%2C%22vuserid%22%3A%22%22%2C%22vusession%22%3A%22%22%7D',
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
            'ad_type': 'LD%7CKB%7CPVL',
            'pf_ex': 'pc',
            'url': quote(self.window.url, safe=''),
            'refer': quote(self.window.url, safe=''),
            'ty': 'web',
            'plugin': '1.0.0',
            'v': '3.5.57',
            'coverid': self.cid,
            'vid': self.vid,
            'pt': '',
            'flowid': self.flow_id,
            'vptag': '',
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
            'tpid': '106'
        }

    def get_info(self):
        res = requests.post(
            self.proxy_url,
            {
                'buid': 'vinfoad',
                'vinfoparam': self.v_info_param,
                'adparam': self.ad_param
            }
        )
        pass
