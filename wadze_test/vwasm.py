#!/usr/bin/env python
# encoding: utf-8

"""
@Time    : 2020/6/14 8:47
@Author  : Sam Wang
@Email   : muumlover@live.com
@Blog    : https://blog.ronpy.com
@Project : xbmc-addons
@FileName: vwasm.py
@Software: PyCharm 
@license : (C) Copyright 2020 by Sam Wang. All rights reserved.
@Desc    : 
    
"""
from collections import deque, namedtuple

import wadze

wadze.Global.get_value = lambda self: VValue(self.globaltype.type, self.expr[0][1])
wadze.ImportGlobal.get_value = lambda self, value: VValue(self.globaltype.type, value)

MEMORY_PAGE_SIZE = 64 * 1024
MEMORY_PAGE_MAX = 2 ** 16


class VEnv:
    pass


class VMemory:
    data = None

    def __init__(self, min, max):
        self.limit_min = min
        self.limit_max = max
        self.data = bytearray()
        self.size = 0

    def grow(self, n):
        if self.limit_max and self.size + n > self.limit_max:
            raise RuntimeError('out of memory')
        if self.size + n > MEMORY_PAGE_MAX:
            raise RuntimeError('out of memory')
        self.data.extend([0x00] * n * MEMORY_PAGE_SIZE)
        self.size += n


VFunction = namedtuple('VFunction', ['code', 'type', 'name'])


class VValue:
    def __init__(self, v_type, v_data):
        self._type = v_type
        self._data = v_data

    def __repr__(self):
        return f'{self._type}({self._data})'

    @property
    def type(self):
        return self._type

    @property
    def data(self):
        return self._data

    def set(self, value):
        self._type = value.type
        self._data = value.data


class VStack(deque):
    push = deque.append


class VMemoryStack:
    def __init__(self):
        self._data = deque()

    def __len__(self):
        return len(self._data)

    def push(self, value):
        self._data.append(VValue(value.type, value.data))

    def pop(self):
        value = self._data.pop()
        return VValue(value.type, value.data)


class VCore:
    dispatch_map = None
    global_list = None
    local_list = None
    memory_stack = None

    def __init__(self):
        self.dispatch_map = {
            'unreachable': self._unreachable_,
            'nop': self._nop_,
            'block': self._block_,
            'loop': self._loop_,
            'if': self._if_,
            'else': self._else_,
            'br': self._br_,
            'br_if': self._br_if_,
            'br_table': self._br_table_,
            'return': self._return_,
            'call': self._call_,
            'call_indirect': self._call_indirect_,
            'drop': self._drop_,
            'select': self._select_,
            'local.get': self._local_get_,
            'local.set': self._local_set_,
            'local.tee': self._local_tee_,
            'global.get': self._global_get_,
            'global.set': self._global_set_,
            'i32.load': self._i32_load_,
            'i64.load': self._i64_load_,
            'f32.load': self._f32_load_,
            'f64.load': self._f64_load_,
            'i32.load8_s': self._i32_load8_s_,
            'i32.load8_u': self._i32_load8_u_,
            'i32.load16_s': self._i32_load16_s_,
            'i32.load16_u': self._i32_load16_u_,
            'i64.load8_s': self._i64_load8_s_,
            'i64.load8_u': self._i64_load8_u_,
            'i64.load16_s': self._i64_load16_s_,
            'i64.load16_u': self._i64_load16_u_,
            'i64.load32_s': self._i64_load32_s_,
            'i64.load32_u': self._i64_load32_u_,
            'i32.store': self._i32_store_,
            'i64.store': self._i64_store_,
            'f32.store': self._f32_store_,
            'f64.store': self._f64_store_,
            'i32.store8': self._i32_store8_,
            'i32.store16': self._i32_store16_,
            'i64.store8': self._i64_store8_,
            'i64.store16': self._i64_store16_,
            'i64.store32': self._i64_store32_,
            'memory.size': self._memory_size_,
            'memory.grow': self._memory_grow_,
            'i32.const': self._i32_const_,
            'i64.const': self._i64_const_,
            'f32.const': self._f32_const_,
            'f64.const': self._f64_const_,
            'i32.eqz': self._i32_eqz_,
            'i32.eq': self._i32_eq_,
            'i32.ne': self._i32_ne_,
            'i32.lt_s': self._i32_lt_s_,
            'i32.lt_u': self._i32_lt_u_,
            'i32.gt_s': self._i32_gt_s_,
            'i32.gt_u': self._i32_gt_u_,
            'i32.le_s': self._i32_le_s_,
            'i32.le_u': self._i32_le_u_,
            'i32.ge_s': self._i32_ge_s_,
            'i32.ge_u': self._i32_ge_u_,
            'i64.eqz': self._i64_eqz_,
            'i64.eq': self._i64_eq_,
            'i64.ne': self._i64_ne_,
            'i64.lt_s': self._i64_lt_s_,
            'i64.lt_u': self._i64_lt_u_,
            'i64.gt_s': self._i64_gt_s_,
            'i64.gt_u': self._i64_gt_u_,
            'i64.le_s': self._i64_le_s_,
            'i64.le_u': self._i64_le_u_,
            'i64.ge_s': self._i64_ge_s_,
            'i64.ge_u': self._i64_ge_u_,
            'f32.eq': self._f32_eq_,
            'f32.ne': self._f32_ne_,
            'f32.lt': self._f32_lt_,
            'f32.gt': self._f32_gt_,
            'f32.le': self._f32_le_,
            'f32.ge': self._f32_ge_,
            'f64.eq': self._f64_eq_,
            'f64.ne': self._f64_ne_,
            'f64.lt': self._f64_lt_,
            'f64.gt': self._f64_gt_,
            'f64.le': self._f64_le_,
            'f64.ge': self._f64_ge_,
            'i32.clz': self._i32_clz_,
            'i32.ctz': self._i32_ctz_,
            'i32.popcnt': self._i32_popcnt_,
            'i32.add': self._i32_add_,
            'i32.sub': self._i32_sub_,
            'i32.mul': self._i32_mul_,
            'i32.div_s': self._i32_div_s_,
            'i32.div_u': self._i32_div_u_,
            'i32.rem_s': self._i32_rem_s_,
            'i32.rem_u': self._i32_rem_u_,
            'i32.and': self._i32_and_,
            'i32.or': self._i32_or_,
            'i32.xor': self._i32_xor_,
            'i32.shl': self._i32_shl_,
            'i32.shr_s': self._i32_shr_s_,
            'i32.shr_u': self._i32_shr_u_,
            'i32.rotl': self._i32_rotl_,
            'i32.rotr': self._i32_rotr_,
            'i64.clz': self._i64_clz_,
            'i64.ctz': self._i64_ctz_,
            'i64.popcnt': self._i64_popcnt_,
            'i64.add': self._i64_add_,
            'i64.sub': self._i64_sub_,
            'i64.mul': self._i64_mul_,
            'i64.div_s': self._i64_div_s_,
            'i64.div_u': self._i64_div_u_,
            'i64.rem_s': self._i64_rem_s_,
            'i64.rem_u': self._i64_rem_u_,
            'i64.and': self._i64_and_,
            'i64.or': self._i64_or_,
            'i64.xor': self._i64_xor_,
            'i64.shl': self._i64_shl_,
            'i64.shr_s': self._i64_shr_s_,
            'i64.shr_u': self._i64_shr_u_,
            'i64.rotl': self._i64_rotl_,
            'i64.rotr': self._i64_rotr_,
            'f32.abs': self._f32_abs_,
            'f32.neg': self._f32_neg_,
            'f32.ceil': self._f32_ceil_,
            'f32.floor': self._f32_floor_,
            'f32.trunc': self._f32_trunc_,
            'f32.nearest': self._f32_nearest_,
            'f32.sqrt': self._f32_sqrt_,
            'f32.add': self._f32_add_,
            'f32.sub': self._f32_sub_,
            'f32.mul': self._f32_mul_,
            'f32.div': self._f32_div_,
            'f32.min': self._f32_min_,
            'f32.max': self._f32_max_,
            'f32.copysign': self._f32_copysign_,
            'f64.abs': self._f64_abs_,
            'f64.neg': self._f64_neg_,
            'f64.ceil': self._f64_ceil_,
            'f64.floor': self._f64_floor_,
            'f64.trunc': self._f64_trunc_,
            'f64.nearest': self._f64_nearest_,
            'f64.sqrt': self._f64_sqrt_,
            'f64.add': self._f64_add_,
            'f64.sub': self._f64_sub_,
            'f64.mul': self._f64_mul_,
            'f64.div': self._f64_div_,
            'f64.min': self._f64_min_,
            'f64.max': self._f64_max_,
            'f64.copysign': self._f64_copysign_,
            'i32.wrap_i64': self._i32_wrap_i64_,
            'i32.trunc_f32_s': self._i32_trunc_f32_s_,
            'i32.trunc_f32_u': self._i32_trunc_f32_u_,
            'i32.trunc_f64_s': self._i32_trunc_f64_s_,
            'i32.trunc_f64_u': self._i32_trunc_f64_u_,
            'i64.extend_i32_s': self._i64_extend_i32_s_,
            'i64.extend_i32_u': self._i64_extend_i32_u_,
            'i64.trunc_f32_s': self._i64_trunc_f32_s_,
            'i64.trunc_f32_u': self._i64_trunc_f32_u_,
            'i64.trunc_f64_s': self._i64_trunc_f64_s_,
            'i64.trunc_f64_u': self._i64_trunc_f64_u_,
            'f32.convert_i32_s': self._f32_convert_i32_s_,
            'f32.convert_i32_u': self._f32_convert_i32_u_,
            'f32.convert_i64_s': self._f32_convert_i64_s_,
            'f32.convert_i64_u': self._f32_convert_i64_u_,
            'f32.demote_f64': self._f32_demote_f64_,
            'f64.convert_i32_s': self._f64_convert_i32_s_,
            'f64.convert_i32_u': self._f64_convert_i32_u_,
            'f64.convert_i64_s': self._f64_convert_i64_s_,
            'f64.convert_i64_u': self._f64_convert_i64_u_,
            'f64.promote_f32': self._f64_promote_f32_,
            'i32.reinterpret_f32': self._i32_reinterpret_f32_,
            'i64.reinterpret_f64': self._i64_reinterpret_f64_,
            'f32.reinterpret_i32': self._f32_reinterpret_i32_,
            'f64.reinterpret_i64': self._f64_reinterpret_i64_,
        }

    def _exec_opcodes(self, opcodes):
        pass

    def call(self, param):
        pass

    def dispatch(self, op):
        if op in self.dispatch_map:
            return self.dispatch_map[op]
        else:
            raise RuntimeError("Unknown opcode: '%s'" % op)

    def _unreachable_(self, operand):
        pass

    def _nop_(self, operand):
        pass

    def _block_(self, operand):
        pass

    def _loop_(self, operand):
        pass

    def _if_(self, operand):
        x = self.memory_stack.pop()
        if x.data:
            for opcodes in operand[1][0]:
                self._exec_opcodes(opcodes)
        pass

    def _else_(self, operand):
        pass

    def _br_(self, operand):
        pass

    def _br_if_(self, operand):
        pass

    def _br_table_(self, operand):
        pass

    def _return_(self, operand):
        pass

    def _call_(self, operand):
        self.call(operand[0])
        pass

    def _call_indirect_(self, operand):
        pass

    def _drop_(self, operand):
        pass

    def _select_(self, operand):
        pass

    def _local_get_(self, operand):
        self.memory_stack.push(self.local_list[operand[0]])
        pass

    def _local_set_(self, operand):
        self.local_list[operand[0]].set(self.memory_stack.pop())
        pass

    def _local_tee_(self, operand):
        pass

    def _global_get_(self, operand):
        self.memory_stack.push(self.global_list[operand[0]])

    def _global_set_(self, operand):
        self.global_list[operand[0]].set(self.memory_stack.pop())
        pass

    def _i32_load_(self, operand):
        pass

    def _i64_load_(self, operand):
        pass

    def _f32_load_(self, operand):
        pass

    def _f64_load_(self, operand):
        pass

    def _i32_load8_s_(self, operand):
        pass

    def _i32_load8_u_(self, operand):
        pass

    def _i32_load16_s_(self, operand):
        pass

    def _i32_load16_u_(self, operand):
        pass

    def _i64_load8_s_(self, operand):
        pass

    def _i64_load8_u_(self, operand):
        pass

    def _i64_load16_s_(self, operand):
        pass

    def _i64_load16_u_(self, operand):
        pass

    def _i64_load32_s_(self, operand):
        pass

    def _i64_load32_u_(self, operand):
        pass

    def _i32_store_(self, operand):
        pass

    def _i64_store_(self, operand):
        pass

    def _f32_store_(self, operand):
        pass

    def _f64_store_(self, operand):
        pass

    def _i32_store8_(self, operand):
        pass

    def _i32_store16_(self, operand):
        pass

    def _i64_store8_(self, operand):
        pass

    def _i64_store16_(self, operand):
        pass

    def _i64_store32_(self, operand):
        pass

    def _memory_size_(self, operand):
        pass

    def _memory_grow_(self, operand):
        pass

    def _i32_const_(self, operand):
        self.memory_stack.push(VValue('i32', operand[0]))
        pass

    def _i64_const_(self, operand):
        self.memory_stack.push(VValue('i64', operand[0]))
        pass

    def _f32_const_(self, operand):
        self.memory_stack.push(VValue('f32', operand[0]))
        pass

    def _f64_const_(self, operand):
        self.memory_stack.push(VValue('f64', operand[0]))
        pass

    def _i32_eqz_(self, operand):
        pass

    def _i32_eq_(self, operand):
        pass

    def _i32_ne_(self, operand):
        pass

    def _i32_lt_s_(self, operand):
        pass

    def _i32_lt_u_(self, operand):
        pass

    def _i32_gt_s_(self, operand):
        pass

    def _i32_gt_u_(self, operand):
        pass

    def _i32_le_s_(self, operand):
        pass

    def _i32_le_u_(self, operand):
        pass

    def _i32_ge_s_(self, operand):
        x = self.memory_stack.pop()
        y = self.memory_stack.pop()
        self.memory_stack.push(VValue('i32', x.data >= y.data))
        pass

    def _i32_ge_u_(self, operand):
        pass

    def _i64_eqz_(self, operand):
        pass

    def _i64_eq_(self, operand):
        pass

    def _i64_ne_(self, operand):
        pass

    def _i64_lt_s_(self, operand):
        pass

    def _i64_lt_u_(self, operand):
        pass

    def _i64_gt_s_(self, operand):
        pass

    def _i64_gt_u_(self, operand):
        pass

    def _i64_le_s_(self, operand):
        pass

    def _i64_le_u_(self, operand):
        pass

    def _i64_ge_s_(self, operand):
        pass

    def _i64_ge_u_(self, operand):
        pass

    def _f32_eq_(self, operand):
        pass

    def _f32_ne_(self, operand):
        pass

    def _f32_lt_(self, operand):
        pass

    def _f32_gt_(self, operand):
        pass

    def _f32_le_(self, operand):
        pass

    def _f32_ge_(self, operand):
        pass

    def _f64_eq_(self, operand):
        pass

    def _f64_ne_(self, operand):
        pass

    def _f64_lt_(self, operand):
        pass

    def _f64_gt_(self, operand):
        pass

    def _f64_le_(self, operand):
        pass

    def _f64_ge_(self, operand):
        pass

    def _i32_clz_(self, operand):
        pass

    def _i32_ctz_(self, operand):
        pass

    def _i32_popcnt_(self, operand):
        pass

    def _i32_add_(self, operand):
        x = self.memory_stack.pop()
        y = self.memory_stack.pop()
        self.memory_stack.push(VValue('i32', x.data + y.data))
        pass

    def _i32_sub_(self, operand):
        pass

    def _i32_mul_(self, operand):
        pass

    def _i32_div_s_(self, operand):
        pass

    def _i32_div_u_(self, operand):
        pass

    def _i32_rem_s_(self, operand):
        pass

    def _i32_rem_u_(self, operand):
        pass

    def _i32_and_(self, operand):
        pass

    def _i32_or_(self, operand):
        pass

    def _i32_xor_(self, operand):
        pass

    def _i32_shl_(self, operand):
        pass

    def _i32_shr_s_(self, operand):
        pass

    def _i32_shr_u_(self, operand):
        pass

    def _i32_rotl_(self, operand):
        pass

    def _i32_rotr_(self, operand):
        pass

    def _i64_clz_(self, operand):
        pass

    def _i64_ctz_(self, operand):
        pass

    def _i64_popcnt_(self, operand):
        pass

    def _i64_add_(self, operand):
        pass

    def _i64_sub_(self, operand):
        pass

    def _i64_mul_(self, operand):
        pass

    def _i64_div_s_(self, operand):
        pass

    def _i64_div_u_(self, operand):
        pass

    def _i64_rem_s_(self, operand):
        pass

    def _i64_rem_u_(self, operand):
        pass

    def _i64_and_(self, operand):
        pass

    def _i64_or_(self, operand):
        pass

    def _i64_xor_(self, operand):
        pass

    def _i64_shl_(self, operand):
        pass

    def _i64_shr_s_(self, operand):
        pass

    def _i64_shr_u_(self, operand):
        pass

    def _i64_rotl_(self, operand):
        pass

    def _i64_rotr_(self, operand):
        pass

    def _f32_abs_(self, operand):
        pass

    def _f32_neg_(self, operand):
        pass

    def _f32_ceil_(self, operand):
        pass

    def _f32_floor_(self, operand):
        pass

    def _f32_trunc_(self, operand):
        pass

    def _f32_nearest_(self, operand):
        pass

    def _f32_sqrt_(self, operand):
        pass

    def _f32_add_(self, operand):
        pass

    def _f32_sub_(self, operand):
        pass

    def _f32_mul_(self, operand):
        pass

    def _f32_div_(self, operand):
        pass

    def _f32_min_(self, operand):
        pass

    def _f32_max_(self, operand):
        pass

    def _f32_copysign_(self, operand):
        pass

    def _f64_abs_(self, operand):
        pass

    def _f64_neg_(self, operand):
        pass

    def _f64_ceil_(self, operand):
        pass

    def _f64_floor_(self, operand):
        pass

    def _f64_trunc_(self, operand):
        pass

    def _f64_nearest_(self, operand):
        pass

    def _f64_sqrt_(self, operand):
        pass

    def _f64_add_(self, operand):
        pass

    def _f64_sub_(self, operand):
        pass

    def _f64_mul_(self, operand):
        pass

    def _f64_div_(self, operand):
        pass

    def _f64_min_(self, operand):
        pass

    def _f64_max_(self, operand):
        pass

    def _f64_copysign_(self, operand):
        pass

    def _i32_wrap_i64_(self, operand):
        pass

    def _i32_trunc_f32_s_(self, operand):
        pass

    def _i32_trunc_f32_u_(self, operand):
        pass

    def _i32_trunc_f64_s_(self, operand):
        pass

    def _i32_trunc_f64_u_(self, operand):
        pass

    def _i64_extend_i32_s_(self, operand):
        pass

    def _i64_extend_i32_u_(self, operand):
        pass

    def _i64_trunc_f32_s_(self, operand):
        pass

    def _i64_trunc_f32_u_(self, operand):
        pass

    def _i64_trunc_f64_s_(self, operand):
        pass

    def _i64_trunc_f64_u_(self, operand):
        pass

    def _f32_convert_i32_s_(self, operand):
        pass

    def _f32_convert_i32_u_(self, operand):
        pass

    def _f32_convert_i64_s_(self, operand):
        pass

    def _f32_convert_i64_u_(self, operand):
        pass

    def _f32_demote_f64_(self, operand):
        pass

    def _f64_convert_i32_s_(self, operand):
        pass

    def _f64_convert_i32_u_(self, operand):
        pass

    def _f64_convert_i64_s_(self, operand):
        pass

    def _f64_convert_i64_u_(self, operand):
        pass

    def _f64_promote_f32_(self, operand):
        pass

    def _i32_reinterpret_f32_(self, operand):
        pass

    def _i64_reinterpret_f64_(self, operand):
        pass

    def _f32_reinterpret_i32_(self, operand):
        pass

    def _f64_reinterpret_i64_(self, operand):
        pass


class VRuntime(VCore):
    _data = None
    module = None
    memory_list = None
    function_list = None
    frame_stack = None

    def __init__(self, imp):
        super().__init__()
        self.imp = imp
        self.memory_stack = VMemoryStack()
        self.frame_stack = VStack()

    @property
    def local_list(self):
        return self.frame_stack[-1] if self.frame_stack else None

    def load(self, module):
        self.module = module
        self.function_list = []
        self.global_list = []

        for i in self.module.import_list:
            if isinstance(i, wadze.ImportFunction):
                self.function_list.append(VFunction(
                    self.imp[i.module].get(i.name, None),
                    self.module.type_list[i.typeidx],
                    i.name
                ))
            if isinstance(i, wadze.ImportGlobal):
                self.global_list.append(VValue(i.globaltype.type, self.imp[i.module][i.name]))
        for index, c in enumerate(self.module.code_list):
            self.function_list.append(VFunction(
                c,
                self.module.type_list[self.module.func_list[index]],
                None
            ))
        for index, e in enumerate(self.module.export_list):
            func = self.function_list[e.ref]
            self.function_list[e.ref] = VFunction(
                func.code,
                func.type,
                e.name
            )
            pass
        for g in self.module.global_list:
            self._exec_opcodes(g.expr[0])
            self.global_list.append(self.memory_stack.pop())

    def _exec_opcodes(self, opcodes):
        operation = self.dispatch(opcodes[0])
        operation(opcodes[1:])

    def _run_wasm_fun(self, func):
        self.frame_stack.push([])
        assert len(self.memory_stack) >= len(func.type.params)
        for i, param in enumerate(func.type.params):
            v = self.memory_stack.pop()
            assert v.type == param
            self.local_list.append(v)
        for local in func.code.locals:
            self.local_list.append(VValue(local, 0))
        for i, opcodes in enumerate(func.code.instructions):
            self._exec_opcodes(opcodes)
        self.frame_stack.pop()

    def _run(self, func):
        if isinstance(func.code, wadze.Code):
            self._run_wasm_fun(func)
        elif func.code:
            func.code()
            pass

    def call(self, func_index):
        f_func = self.function_list[func_index]
        self._run(f_func)

    def call_export(self, export_index, args):
        e_export = self._wasm['export'][export_index]
        func = self.function_list[e_export.ref]
        if not len(func.type.params) == len(args): raise ValueError()
        for i, p_type in enumerate(func.type.params):
            v = args[i]
            if not v.type == p_type: raise TypeError()
            self.memory_stack.push(v)
        self._run(func)
        if not len(self.memory_stack) >= len(func.type.returns): raise RuntimeError()
        r_list = []
        for i, r_type in enumerate(func.type.returns):
            v = self.memory_stack.pop()
            if not v.type == r_type: raise RuntimeError()
            r_list.append(v)
        return tuple(r_list)

    def get_type(self, export_index):
        e_export = self._wasm['export'][export_index]
        func = self.function_list[e_export.ref]
        return func.type

    def memcpy(self, data, addr, size):
        self.memory_list[0].data[addr:addr + size] = bytes(data.encode() + b'\0')


class VModule:
    __slots__ = (
        '_module',
        '_export_index',
        'type_list',
        'import_list',
        'func_list',
        'table_list',
        'memory_list',
        'global_list',
        'export_list',
        'start_list',
        'element_list',
        'code_list',
        'data_list',
    )

    def __init__(self, path):
        with open(path, 'rb') as file:
            data = file.read()
        self._module = wadze.parse_module(data)
        self._module['code'] = [wadze.parse_code(c) for c in self._module['code']]
        self._export_index = [e.name for e in self._module['export']]

    def __getattr__(self, item):
        if '_list' in item:
            key = item.replace('_list', '')
            return self._module[key]


class VWasm:
    _export_index = None

    def __init__(self, path, imp, alloc_name):
        self.vm = VRuntime(imp)
        self.module = VModule(path)
        self.vm.load(self.module)

        self.alloc = self[alloc_name](params=[int], returns=[int])

    def v_memcpy(self, data, addr, size):
        self.vm.memory_list[0].data[addr:addr + size] = bytes(data.encode() + b'\0')

    def v_deposit(self, data):
        ptr = self.alloc(len(data) + 1)
        self.v_memcpy(data, ptr, len(data) + 1)
        return ptr

    def v_withdraw(self, ptr):
        ptr_end = ptr
        while self.vm.memory_list[0].data[ptr_end] != 0:
            ptr_end += 1
        return self.vm.memory_list[0].data[ptr:ptr_end].decode()

    def v_call(self, index, params, returns):
        fun_index = self._export_index.index(index)

        def func(*args):
            assert len(params) == len(args)
            fun_type = self.vm.get_type(fun_index)
            new_args = []
            for i, arg in enumerate(args):
                if params[i] == str:
                    arg_ptr = self.v_deposit(arg)
                    new_args.append(VValue(fun_type.params[i], arg_ptr))
                else:
                    new_args.append(VValue(fun_type.params[i], arg))
            ret_data = self.vm.call_export(fun_index, new_args)
            ret = []
            for i, d in enumerate(ret_data):
                if returns[0] == str:
                    ret.append(self.v_withdraw(d.data))
                else:
                    ret.append(d.data)
            return tuple(ret)

        return func

    def __getattr__(self, item):
        return self[item]

    def __getitem__(self, item):
        if item in self._export_index:
            return lambda params, returns: self.v_call(item, params, returns)
        else:
            raise Exception('func <%s> not found' % item)


if __name__ == '__main__':
    def _get_unicode_str():
        data = '|'
        data_len = len(data) + 1
        # data_ptr self.wa__malloc(data_len)
        data_ptr = a.stackAlloc(VValue('i32', data_len))
        a.memcpy(data, data_ptr, data_len + 1)
        return data_ptr


    a = VWasm('ckey.wasm', {'env': {
        'DYNAMICTOP_PTR': 7968,
        'tempDoublePtr': 7952,
        'STACKTOP': 7984,
        'STACK_MAX': 5250864,

        'memoryBase': 1024,
        'tableBase': 0,

        'memory': VMemory(min=256, max=256),
        # 'table': WasmTable(99),
        '_get_unicode_str': _get_unicode_str,
    }, 'global': {
        'NaN': 0,
        'Infinity': 0,
    }}, alloc_name='stackAlloc')

    data_ptr = a.alloc(10)
    r = a._getckey(params=[str, int, int, int, int, str], returns=[str])('asd', 0, 0, 0, 0, '123')
    pass
