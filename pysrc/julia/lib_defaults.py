import sys
import os

from ctypes import *


rootdir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

libdir = os.path.join(rootdir, 'target', 'lib')
libname = 'jl2py'
libext = 'dylib' if sys.platform == 'darwin' else 'so'
libfile = (os.path.extsep).join(('lib{}'.format(libname), libext))
libpath = os.path.join(libdir, libfile)

libfuncs = dict(
    jl_eval_string=((c_char_p,), c_void_p),
    
    jl_call=((c_void_p, c_void_p, c_uint32,), c_void_p),
    jl_call0=((c_void_p,) * 1, c_void_p),
    jl_call1=((c_void_p,) * 2, c_void_p),
    jl_call2=((c_void_p,) * 3, c_void_p),
    jl_call3=((c_void_p,) * 4, c_void_p),

    jl_symbol=((c_char_p,), c_void_p),
    
    jl_typeof=((c_void_p,), c_void_p),

    jl_field_index=((c_void_p, c_void_p, c_int,), c_int),
    jl_get_field=((c_void_p, c_char_p,), c_void_p),
    jl_get_nth_field=((c_void_p, c_size_t,), c_void_p),
    jl_set_nth_field=((c_void_p, c_size_t, c_void_p,), None),
    
    jl_box_bool=((c_int8,), c_void_p),
    jl_box_float64=((c_double,), c_void_p),
    jl_box_int64=((c_int64,), c_void_p),
    jl_box_voidpointer=((c_void_p,), c_void_p),
    jl_unbox_bool=((c_void_p,), c_int8),
    jl_unbox_float64=((c_void_p,), c_double),
    jl_unbox_int64=((c_void_p,), c_int64),
    jl_unbox_voidpointer=((c_void_p,), c_void_p),
    jl_string_ptr=((c_void_p,), c_char_p),

    jl_egal=((c_void_p, c_void_p,), c_int),

    jl_gc_enable=((c_int,), c_int),
    jl_gc_is_enabled=(None, c_int),
    jl_gc_collect=((c_int,), None),
    jl_gc_queue_root=((c_void_p,), None),

    jl_get_binding_wr=((c_void_p, c_void_p, c_int,), c_void_p),
    jl_get_global=((c_void_p, c_void_p,), c_void_p),
    jl_checked_assignment=((c_void_p, c_void_p, c_void_p, c_void_p,), None),

    jl_apply_type=((c_void_p, c_void_p, c_size_t,), c_void_p),
    jl_apply_type1=((c_void_p,) * 2, c_void_p),
    jl_apply_type2=((c_void_p,) * 3, c_void_p),
    jl_apply_type3=((c_void_p,) * 4, c_void_p),

    jl_apply_tuple_type_v=((c_void_p, c_size_t,), c_void_p),
    jl_new_structv=((c_void_p, c_void_p, c_uint32,), c_void_p),
    jl_apply_array_type=((c_void_p, c_size_t,), c_void_p),
    jl_ptr_to_array=((c_void_p, c_void_p, c_void_p, c_int,), c_void_p),

    jl_exception_occurred=(None, c_void_p),

    jl_printf=((c_void_p, c_char_p,), c_int),
    jl_stderr_stream=(None, c_void_p),
    jl_stderr_obj=(None, c_void_p),

    jl_get_current_task=(None, c_void_p),

    jl_get_pgcstack=(None, c_void_p),
)

libvars = dict(
    jl_core_module=c_void_p,
    jl_base_module=c_void_p,
    jl_main_module=c_void_p,
    jl_top_module=c_void_p,

    jl_any_type=c_void_p,
    jl_type_type=c_void_p,
    jl_typename_type=c_void_p,
    jl_type_typename=c_void_p,
    jl_symbol_type=c_void_p,
    jl_simplevector_type=c_void_p,
    jl_tuple_typename=c_void_p,
    jl_anytuple_type=c_void_p,
    jl_emptytuple_type=c_void_p,
    jl_anytuple_type_type=c_void_p,
    jl_function_type=c_void_p,
    jl_module_type=c_void_p,
    jl_densearray_type=c_void_p,
    jl_array_type=c_void_p,
    jl_array_typename=c_void_p,
    jl_genericmemory_type=c_void_p,
    jl_genericmemory_typename=c_void_p,
    jl_genericmemoryref_type=c_void_p,
    jl_genericmemoryref_typename=c_void_p,
    jl_weakref_type=c_void_p,
    jl_abstractstring_type=c_void_p,
    jl_string_type=c_void_p,

    jl_bool_type=c_void_p,
    jl_uint8_type=c_void_p,
    jl_int64_type=c_void_p,
    jl_float64_type=c_void_p,
    jl_nothing_type=c_void_p,
    jl_voidpointer_type=c_void_p,
    jl_uint8pointer_type=c_void_p,
    jl_pointer_type=c_void_p,
    jl_ref_type=c_void_p,
    jl_pointer_typename=c_void_p,
    jl_namedtuple_type=c_void_p,
    jl_namedtuple_typename=c_void_p,

    jl_emptysvec=c_void_p,
    jl_emptytuple=c_void_p,
    jl_true=c_void_p,
    jl_false=c_void_p,
    jl_nothing=c_void_p,
    jl_kwcall_func=c_void_p,
    
    # jl_libdl_dlopen_func=c_void_p,
)
