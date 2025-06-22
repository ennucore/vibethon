import sys
import traceback
import types

# def tracer(frame, event, arg):
#     if event == 'exception':
#         exc_type, exc_val, exc_tb = arg
#         print(f"⚡  {exc_type.__name__} raised in "
#               f"{frame.f_code.co_filename}:{frame.f_lineno}")
#         for name, val in frame.f_locals.items():
#             print(f"    {name} = {val!r}")
#         breakpoint()
#     return tracer

# sys.settrace(tracer)

def buggy():
    x = 10
    y = 0
    return x / y

try:
    a = 1
    buggy()
except Exception as e:
    breakpoint()

print(t)