import sys
import traceback
import inspect
import ast
import types
import importlib

# Use the custom Pdb implementation
from vibethon.llm import ChatGPTPdbLLM
from vibethon.vdb import CustomPdb

# Mapping from code objects of instrumented functions to their original
# source lines and the starting line number in the file.  This allows the
# custom Pdb ``list`` implementation to translate the instrumented frame's
# *relative* line numbers back to the real ones on disk without resorting to
# fiddling with ``lineno`` offsets when we build the AST.
_VIBEZZ_SOURCE_MAP = {}

llm = ChatGPTPdbLLM()

class DebuggerContinue(Exception):
    """Exception used to signal that execution should continue"""
    def __init__(self, return_value=None):
        self.return_value = return_value

class VibezzDebugger:
    def __init__(self):
        self.instrumented_functions = set()
    
    def auto_instrument(self, module_globals=None):
        """Automatically instrument all user-defined functions in the current module"""
        if module_globals is None:
            import __main__
            module_globals = __main__.__dict__
        
        print("🔧 Auto-instrumenting all functions...")
        
        # Find all functions in the module
        functions_to_instrument = []
        module_name = module_globals.get("__name__", None)
        
        for name, obj in list(module_globals.items()):
            # Only instrument functions that are defined *in this module*
            if (isinstance(obj, types.FunctionType) and
                not name.startswith('_') and
                obj.__module__ == module_name and
                obj.__code__ not in self.instrumented_functions):
                functions_to_instrument.append((name, obj))
        
        # Instrument each function
        for name, func in functions_to_instrument:
            try:
                instrumented_func = instrument_function(func)
                module_globals[name] = instrumented_func
                self.instrumented_functions.add(func.__code__)
                print(f"  ✅ Instrumented: {name}")
            except Exception as e:
                print(f"  ❌ Failed to instrument {name}: {e}")
        
        print(f"🎯 Auto-instrumentation complete! {len(functions_to_instrument)} functions instrumented.")
    
    def select_frame(self, frames):
        """Allow user to select which frame to debug"""
        if len(frames) == 1:
            return frames[0]
        
        print("Multiple frames available:")
        for i, frame in enumerate(frames):
            code = frame.tb_frame.f_code
            # Fix: Use tb_lineno instead of f_lineno
            print(f"  {i}: {code.co_filename}:{frame.tb_lineno} in {code.co_name}")
        
        while True:
            try:
                choice = input(f"Select frame (0-{len(frames)-1}, or press Enter for innermost): ").strip()
                if not choice:
                    return frames[-1]  # Default to innermost frame
                
                idx = int(choice)
                if 0 <= idx < len(frames):
                    return frames[idx]
                else:
                    print(f"Invalid choice. Please enter 0-{len(frames)-1}")
            except ValueError:
                print("Please enter a valid number")
            except (EOFError, KeyboardInterrupt):
                return frames[-1]  # Default to innermost frame

# Create global debugger instance
vibezz_debugger = VibezzDebugger()

def instrument_function(func):
    """
    Wrap each statement in the given function in a try/except that catches errors
    and calls breakpoint().
    """
    # Retrieve the function's source **and** its starting line number inside the
    # original file.  This allows us to realign the generated AST so that its
    # line numbers match the ones that appear in the file on disk.  When the
    # debugger (e.g. pdb) relies on the `co_firstlineno` and individual node
    # line numbers it will therefore be able to display the correct lines when
    # you issue the `list` command.
    source_lines, starting_line = inspect.getsourcelines(func)
    source = "".join(source_lines)

    # Parse the function body into an AST and then shift all node line numbers
    # so they line up with the real file.  This ensures that *built-in* pdb
    # commands such as `list` and `where` work out of the box without extra
    # translation layers.
    tree = ast.parse(source)
    ast.increment_lineno(tree, starting_line - 1)

    func_def = tree.body[0]  # assumes the first node is the FunctionDef

    new_body = []
    for stmt in func_def.body:
        # Wrap each original statement in a Try/Except so that we can break
        # into the debugger on *any* exception while still preserving the
        # original source location of that statement.
        try_node = ast.Try(
            body=[stmt],
            handlers=[ast.ExceptHandler(
                type=ast.Name(id='Exception', ctx=ast.Load()),
                name='e',
                body=[
                    # Get the original frame where the exception occurred
                    ast.Assign(
                        targets=[ast.Name(id='_original_frame', ctx=ast.Store())],
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
                    
                    # Import vdb
                    ast.ImportFrom(
                        module='vibethon',
                        names=[ast.alias(name='vdb', asname=None)],
                        level=0
                    ),
                    
                    # vdb.set_trace(_original_frame)
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id='vdb', ctx=ast.Load()),
                                attr='set_trace',
                                ctx=ast.Load(),
                            ),
                            args=[
                                ast.Name(id='_original_frame', ctx=ast.Load())
                            ],
                            keywords=[],
                        )
                    ),
                ]
            )],
            orelse=[],
            finalbody=[]
        )

        # Make sure the newly-created Try node inherits the location (line
        # number, column offset) of the statement it is wrapping.  This keeps
        # the mapping between byte-code line numbers and the original source
        # intact so that debuggers can display the right context.
        ast.copy_location(try_node, stmt)

        new_body.append(try_node)

    func_def.body = new_body

    # Fill in any missing lineno/col_offset fields that we didn't explicitly
    # set above.
    ast.fix_missing_locations(tree)

    compiled = compile(
        tree,
        filename=func.__code__.co_filename,  # keep original filename
        mode='exec'
    )
    namespace = {}
    globals_dict = func.__globals__

    exec(compiled, globals_dict, namespace)
    instrumented = namespace[func.__name__]

    # Register mapping for custom Pdb list command
    try:
        import vibethon.vibezz as _vzz_mod  # the module we are editing
    except ImportError:
        _vzz_mod = sys.modules[__name__]
    _vzz_mod._VIBEZZ_SOURCE_MAP[instrumented.__code__] = (source_lines, starting_line, func.__code__.co_filename)

    return instrumented


# The demo code has been moved to examples/vibezz_demo.py 