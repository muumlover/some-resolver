#!/usr/bin/env python
# encoding: utf-8

"""
@Time    : 2020/6/8 20:28
@Author  : Sam Wang
@Email   : muumlover@live.com
@Blog    : https://blog.ronpy.com
@Project : xbmc-addons
@FileName: pywasm_easy.py
@Software: PyCharm 
@license : (C) Copyright 2020 by Sam Wang. All rights reserved.
@Desc    : 
    
"""
from functools import partial

import pywasm


def match_limits(new: pywasm.binary.Limits, old: pywasm.binary.Limits) -> bool:
    if old.n >= new.n:
        if new.m == 0:
            return True
        if old.m != 0 and new.m != 0:
            if old.m <= new.m:
                return True
    return False


class MemoryInstance:
    def __init__(self, type: pywasm.binary.MemoryType):
        self.type = type
        self.data = bytearray()
        self.size = 0
        # self.grow(type.limits.n)

    def grow(self, n: int):
        if self.type.limits.m and self.size + n > self.type.limits.m:
            raise Exception('pywasm: out of memory limit')
        # If len is larger than 2**16, then fail
        if self.size + n > pywasm.convention.memory_page:
            raise Exception('pywasm: out of memory limit')
        self.data.extend([0x00 for _ in range(n * pywasm.convention.memory_page_size)])
        self.size += n


def pywasm_path():
    pywasm.execution.match_limits = match_limits
    pywasm.execution.MemoryInstance = MemoryInstance
    pywasm.Memory = pywasm.execution.MemoryInstance


if pywasm.execution.match_limits != match_limits:
    pywasm_path()


class WasmMemory:
    def __new__(cls, n, m=None):
        limits = pywasm.Limits()
        limits.n = n
        limits.m = m or n
        memory_type = pywasm.binary.MemoryType()
        memory_type.limits = limits
        memory = pywasm.Memory(memory_type)
        return memory


class WasmTable:
    def __new__(cls, n, m=None, element_type=None):
        limits = pywasm.Limits()
        limits.n = n
        limits.m = m or n
        table = pywasm.Table(element_type or pywasm.convention.empty, limits)
        return table


class WasmEnv(dict):
    def __init__(self, wasm):
        super().__init__()
        self.wasm = wasm

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        if super().__contains__(item):
            return super().__getitem__(item)
        else:
            if 'cb_' + item in self.wasm.__dir__():
                func = self.wasm.__getattribute__('cb_' + item).__func__
                partial_func = partial(func, self.wasm, _cb_name=item)
            else:
                partial_func = partial(self.wasm.callback, self.wasm, _cb_name=item)
            partial_func.__name__ = item
            return partial_func


class WasmEasy:
    def __init__(self, name, env):
        self.runtime = pywasm.load(name, {
            'env': env,
            'global': {
                'NaN': None,
                'Infinity': None,
            }
        })
        # pywasm.on_debug()

    def wasm_call(self, name, args):
        return self.runtime.exec(name, args)

    def memcpy(self, data, addr, size):
        self.runtime.store.mems[0].data[addr:addr + size] = bytes(data.encode() + b'\0')

    def stack_alloc(self, size):
        pass

    def callback(self, *args, **kwargs):
        assert self
        return 0

    @classmethod
    def wasm_function(cls, paras, ret):
        def wrapper(func):
            def deco(self, *args, **kwargs):
                assert len(paras) == len(args)
                new_args = []
                for i, arg in enumerate(args):
                    if paras[i] == str:
                        arg_ptr = self.stack_alloc(len(arg) + 1)
                        self.memcpy(arg, arg_ptr, len(arg) + 1)
                        new_args.append(arg_ptr)
                    else:
                        new_args.append(arg)
                ret_data = func(self, *new_args, **kwargs)
                if ret == str:
                    r_end = ret_data
                    while self.runtime.store.mems[0].data[r_end] != 0:
                        r_end += 1
                    return self.runtime.store.mems[0].data[ret_data:r_end].decode()
                else:
                    return ret_data

            return deco

        return wrapper
