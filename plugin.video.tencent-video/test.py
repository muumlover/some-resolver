#!/usr/bin/env python
# encoding: utf-8

"""
@Time    : 2020/6/8 22:12
@Author  : Sam Wang
@Email   : muumlover@live.com
@Blog    : https://blog.ronpy.com
@Project : xbmc-addons
@FileName: test.py
@Software: PyCharm 
@license : (C) Copyright 2020 by Sam Wang. All rights reserved.
@Desc    : 
    
"""

# !/usr/bin/env python
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

from pywasm_easy import pywasm_path
from tx_player import TxPlayer

pywasm_path()

if __name__ == '__main__':
    tx_player = TxPlayer('https://v.qq.com/x/cover/bzfkv5se8qaqel2/n0020yrnly7.html')
    print(tx_player._c_key_8_1)
    # print(tx_player._c_key_9_1)
    key = tx_player.wasm.wa__getkey(
        tx_player.platform, tx_player.appVer, tx_player.vid, '', '1fcb9528b79f2065c9a281a7d554edd1', 1556590422)
    print(key)
    key2 = '88dkKwGYKDF79ZEItZs_lpJX5WB4a2CdS8k5hHANVaqtHEZQ1c_W6myJ8hQDnmDDHYlsFcmCbTs52vPBr-xE-uhvZyEMY131vUh1H4pgCXe2OpAF-Wzte7F4kwln76xq_nwqEERWEZPLluNDEH6IC8EOljLQ2VfW2sTdospNPlD9535CNT9iSo3cLRH93ogtX_ObeZBTEOuKEsbtjkFpGl3F3IxmISJc_8dRIBruTik-e4rt0isxZAXexKqWDJGxu2rhTvrXyHJH87s1dUoA6Stf9X0c1RYGSdj_UQOME-ds0E7OepYmW0kNjO5DljtDJlQGBgYGBgZEwDLM'
    print(key == key2)
    tx_player.get_info()
