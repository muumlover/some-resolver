#!/usr/bin/env python
# encoding: utf-8

"""
@Time    : 2020/6/13 21:28
@Author  : Sam Wang
@Email   : muumlover@live.com
@Blog    : https://blog.ronpy.com
@Project : xbmc-addons
@FileName: test.py
@Software: PyCharm 
@license : (C) Copyright 2020 by Sam Wang. All rights reserved.
@Desc    : 
    
"""

import wadze

with open('ckey.wasm', 'rb') as file:
    data = file.read()

module = wadze.parse_module(data)

# If you also want function code decoded into instructions, do this
module['code'] = [wadze.parse_code(c) for c in module['code']]
for exp in module['export']:
    print(exp)
