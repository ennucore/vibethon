import sys
import traceback
import inspect
import ast
import openai

chat = openai.chat.completions


def handler(error_class, error_instance, error_traceback, eval_in_scope, exec_in_scope):
    print(error_class)
    print(error_instance)
    print(dir(error_traceback))
    # print(traceback.format_tb(error_traceback))
    print(traceback.format_exception(error_class, error_instance, error_traceback))
    print(error_traceback.tb_frame.f_code.co_name)
    print(error_traceback.tb_frame.f_code.co_filename)
    print(error_traceback.tb_lineno)
    import linecache
    import inspect
    import ast

    # Get the frame where the exception occurred
    frame = error_traceback.tb_frame

    # Try to get the function's source code
    try:
        source_lines, start_line = inspect.getsourcelines(frame)
        print("Function source code:")
        print("".join(source_lines))
    except Exception as e:
        print(f"Could not retrieve function source code: {e}")
    print(globals(), locals())
    exec_in_scope('print("execing in scope")')
    
    # Prepare prompt for the LLM to fix the failing code
    # Include the full formatted traceback in the prompt
    tb_str = "".join(traceback.format_exception(error_class, error_instance, error_traceback))
    try:
        source_lines, start_line = inspect.getsourcelines(frame.f_code)
    except Exception:
        source_lines, start_line = [], None
    prompt = (
        f"Traceback (most recent call last):\n{tb_str}\n"
        "The following Python function raised an exception. "
        "Please provide a corrected version of the code around the failing line so execution can continue. Do not wrap it in ```/''' or anything like that, respond exclusively with the code that replaces the broken line, for example instead of b=1/0 write b=0.\n"
        f"Function source (lines {start_line}-{start_line + len(source_lines) - 1}):\n"
        + "".join(source_lines)
        + f"\nError: {error_instance}\n"
        f"Failing line: {error_traceback.tb_lineno}\n"
    )
    # Call the OpenAI API (ensure OPENAI_API_KEY is set in env)
    response = chat.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    fixed_code = response.choices[0].message.content
    print("Applying fixed code from LLM:")
    print(fixed_code)
    # Execute the corrected code in the exception's original scope
    exec_in_scope(fixed_code)



def install_vibethon():
    sys.excepthook = handler


def instrument_function(func):
    """
    Wrap each statement in the given function in a try/except that swallows errors,
    so execution continues past exceptions at the statement level.
    """
    source_lines, _ = inspect.getsourcelines(func)
    source = "".join(source_lines)
    tree = ast.parse(source)
    func_def = tree.body[0]  # assumes the first node is the FunctionDef
    new_body = []
    for stmt in func_def.body:
        new_body.append(ast.Try(
            body=[stmt],
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='Exception', ctx=ast.Load()),
                name='e',
                body=[
                    # Capture the frame where the exception occurred
                    ast.Assign(
                        targets=[ast.Name(id='frame', ctx=ast.Store())],
                        value=ast.Attribute(
                            value=ast.Attribute(
                                value=ast.Name(id='e', ctx=ast.Load()),
                                attr='__traceback__',
                                ctx=ast.Load()
                            ),
                            attr='tb_frame',
                            ctx=ast.Load()
                        )
                    ),
                    # Provide an eval function in that frame's scope
                    ast.Assign(
                        targets=[ast.Name(id='eval_in_scope', ctx=ast.Store())],
                        value=ast.Lambda(
                            args=ast.arguments(
                                posonlyargs=[], args=[ast.arg(arg='code', annotation=None)], vararg=None,
                                kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
                            ),
                            body=ast.Call(
                                func=ast.Name(id='eval', ctx=ast.Load()),
                                args=[
                                    ast.Name(id='code', ctx=ast.Load()),
                                    ast.Attribute(value=ast.Name(id='frame', ctx=ast.Load()), attr='f_globals', ctx=ast.Load()),
                                    ast.Attribute(value=ast.Name(id='frame', ctx=ast.Load()), attr='f_locals', ctx=ast.Load())
                                ],
                                keywords=[]
                            )
                        )
                    ),
                    # Provide an exec function in that frame's scope
                    ast.Assign(
                        targets=[ast.Name(id='exec_in_scope', ctx=ast.Store())],
                        value=ast.Lambda(
                            args=ast.arguments(
                                posonlyargs=[], args=[ast.arg(arg='code', annotation=None)], vararg=None,
                                kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]
                            ),
                            body=ast.Call(
                                func=ast.Name(id='exec', ctx=ast.Load()),
                                args=[
                                    ast.Name(id='code', ctx=ast.Load()),
                                    ast.Attribute(value=ast.Name(id='frame', ctx=ast.Load()), attr='f_globals', ctx=ast.Load()),
                                    ast.Attribute(value=ast.Name(id='frame', ctx=ast.Load()), attr='f_locals', ctx=ast.Load())
                                ],
                                keywords=[]
                            )
                        )
                    ),
                    # Call handler with the new eval/exec in-scope functions
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id='handler', ctx=ast.Load()),
                            args=[
                                ast.Call(func=ast.Name(id='type', ctx=ast.Load()), args=[ast.Name(id='e', ctx=ast.Load())], keywords=[]),
                                ast.Name(id='e', ctx=ast.Load()),
                                ast.Attribute(value=ast.Name(id='e', ctx=ast.Load()), attr='__traceback__', ctx=ast.Load()),
                                ast.Name(id='eval_in_scope', ctx=ast.Load()),
                                ast.Name(id='exec_in_scope', ctx=ast.Load())
                            ],
                            keywords=[]
                        )
                    ),
                    ast.Pass()
                ]
            )],
            orelse=[],
            finalbody=[]
        ))
    func_def.body = new_body
    ast.fix_missing_locations(tree)
    compiled = compile(tree, filename=func.__code__.co_filename, mode='exec')
    namespace = {}
    exec(compiled, func.__globals__, namespace)
    return namespace[func.__name__]


def faulty_function():
    a= 2/0

    b = 1
    print(f'b: {b}, a: {a}')

    c = 2


if __name__ == "__main__":
    install_vibethon()
    # Instrument and run, so individual statement errors are caught and skipped
    faulty_function = instrument_function(faulty_function)
    faulty_function()