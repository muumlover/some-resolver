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
import json

from tx_player import TxPlayer

if __name__ == '__main__':
    tx_player = TxPlayer('https://v.qq.com/x/cover/zu9dcrznlprx505/d0973687czo.html')
    ret_data = tx_player.get_video_info()
    data_json = ret_data.json()
    vinfo = json.loads(data_json['vinfo'])
    m3u8_list = vinfo['vl']['vi'][0]['ul']['ui']
    video_urls = []
    for m3u8_item in m3u8_list:
        video_urls.append(m3u8_item['url'].replace('.ts.m3u8', '.1.ts'))
        print(m3u8_item['url'])
    for video_url in video_urls:
        print(video_url)
    pass
