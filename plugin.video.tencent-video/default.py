#!/usr/bin/env python
# encoding: utf-8

"""
@Time    : 2020/6/2 20:36
@Author  : Sam Wang
@Email   : muumlover@live.com
@Blog    : https://blog.ronpy.com
@Project : plugin.video.tencent-video
@FileName: default.py
@Software: PyCharm
@license : (C) Copyright 2020 by Sam Wang. All rights reserved.
@Desc    :

"""

from pywasm_easy import WasmEnv, WasmEasy, WasmMemory, WasmTable, pywasm_path
from tx_player import TxPlayer

pywasm_path()


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
        return 5250864

    def cb__get_unicode_str(self, store, *args, **kwargs):
        def p(a):
            b = 0
            for d in a:
                d = ord(d)
                if 55296 <= d <= 57343:
                    d = 65536 + ((1023 & d) << 10) | 1023 & a.charCodeAt(++c)  # TODO
                if d <= 127:
                    b += 1
                elif d <= 2047:
                    b += 2
                elif d <= 65535:
                    b += 3
                elif d <= 2097151:
                    b += 4
                elif d <= 67108863:
                    b += 5
                else:
                    b += 6
            return b

        def a(a):
            return a[:48] if a else ''

        def b():
            b = self.player.window.url
            c = self.player.window.userAgent.upper()
            d = self.player.window.referrer
            f = self.player.window.appCodeName
            g = self.player.window.appName
            h = self.player.window.platform
            b = a(b)
            d = a(d)
            c = a(c)
            return b + "|" + c + "|" + d + "|" + f + "|" + g + "|" + h

        c = b()
        c = 'http://localhost:63342/xbmc-addons/plugin.video.|mozilla/5.0 (windows nt 10.0; win64; x64; rv:77.||Mozilla|Netscape|Win32'
        d = len(c) + 1  # p(c) + 1
        # e = self.wa__malloc(d)
        e = self.wa_stackAlloc(d)
        self.memcpy(c, e, d + 1)
        return e


if __name__ == '__main__':
    tx_player = TxPlayer('https://v.qq.com/x/cover/bzfkv5se8qaqel2/n0020yrnly7.html')
    print(tx_player._c_key_8_1)
    tx_player.get_info()

    wasm = Wasm(tx_player)
    a = wasm.wa__getkey(tx_player.platform, tx_player.appVer, tx_player.vid, '', tx_player.guid, tx_player.tm)
    # pywasm.on_debug()
    getckey = wasm.wa__getkey
    # f ? (a.encryptVer = '9.1', b = f(a.platform, a.appVer, a.vids || a.vid, '', a.guid, a.tm))  : (a.encryptVer = '8.1', b = i(a.vids || a.vid, a.tm, a.appVer, a.guid, a.platform)),
    ret1 = 'N0NK-cUcBud79ZEItZs_lpJX5WB4a2CdS8k5i8cHVaqtHEZQ1c_W6myJ8hQHnmDDHcIqDJeMPTs52vPBr7VR-qt2KjERJVHppF07A9o7TT28d58ctmb-Kq1z2Fd28rxhoT1qVh0ARIWXluNDEH6IC8EOljLQ2VfW2sTdospNPlD9535CNT9iSo3cLRH93ogtX_ObeZBTEOuKEsbtjkFpGl3F3IxmISJc_8dRIBruTik-e4rt0isxZAXexKqWDJGxu2rhTvrXyHJH87s1dUoA6Stf9X0c1RYGSdj_UQOME-ds0KBPfJDz8_mcsKExELVLirIGBgYGBgY__Byl'
    ret2 = getckey(10201, '3.5.57', 'j002024w2wg', '', '1fcb9528b79f2065c9a281a7d554edd1', 1556617308)

    print(runtime.store.memory_list[0].data[r:r + 155])  # 55
    b = 0
