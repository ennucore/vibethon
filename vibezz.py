import sys
import traceback
import inspect
import ast
import types

# Use the custom Pdb implementation
from llm import ChatGPTPdbLLM

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
        for name, obj in list(module_globals.items()):
            if (isinstance(obj, types.FunctionType) and 
                not name.startswith('_') and
                name not in ['instrument_function'] and
                obj.__module__ in ['__main__', None] and
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
    
    def start_repl(self, frame, exc_type, exc_value):
        """Start a simple REPL in the given frame's scope"""
        local_vars = frame.f_locals
        global_vars = frame.f_globals
        
        print(f"🔍 DEBUG REPL - You are now in the scope where {exc_type.__name__} occurred")
        print("Available commands:")
        print("  - Type any Python expression to evaluate it")
        print("  - Use 'locals()' to see local variables")
        print("  - Use 'globals()' to see global variables") 
        print("  - Type 'continue <value>' to continue execution with a return value")
        print("  - Type 'continue' to continue execution with None")
        print("  - Type 'quit' or 'exit' to exit the debugger")
        print("  - Type 'vars' to see current local variables")
        print("=" * 50)
        
        # Show current local variables
        print("Current local variables:")
        for name, value in local_vars.items():
            if not name.startswith('__') and name not in ['frame', 'eval_in_scope', 'exec_in_scope', 'e']:
                print(f"  {name} = {repr(value)}")
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("debug> ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Exiting debugger...")
                    break
                
                # Check for continue commands
                if user_input.lower().startswith('continue'):
                    parts = user_input.split(' ', 1)
                    if len(parts) > 1:
                        # Try to evaluate the return value
                        try:
                            return_value = eval(parts[1], global_vars, local_vars)
                        except Exception as e:
                            print(f"Error evaluating return value: {e}")
                            continue
                    else:
                        return_value = None
                    
                    raise DebuggerContinue(return_value)
                
                # Special command to show variables
                if user_input.lower() == 'vars':
                    print("Local variables:")
                    for name, value in local_vars.items():
                        if not name.startswith('__') and name not in ['frame', 'eval_in_scope', 'exec_in_scope', 'e']:
                            print(f"  {name} = {repr(value)}")
                    continue
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Try to evaluate as expression first
                try:
                    result = eval(user_input, global_vars, local_vars)
                    if result is not None:
                        print(f"→ {repr(result)}")
                except SyntaxError:
                    # If it's not a valid expression, try to execute as statement
                    try:
                        exec(user_input, global_vars, local_vars)
                    except Exception as e:
                        print(f"Error: {e}")
                except Exception as e:
                    print(f"Error: {e}")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nExiting debugger...")
                break
    
    def handler(self, error_class, error_instance, error_traceback, eval_in_scope, exec_in_scope):
        """Enhanced error handler with REPL capabilities"""
        print(f"\n🐛 ERROR DETECTED: {error_class.__name__}: {error_instance}")
        print("=" * 50)
        
        # Show all frames and let user select one
        frames = []
        frame = error_traceback
        while frame is not None:
            frames.append(frame)
            frame = frame.tb_next
        
        # Print the traceback
        print("Traceback:")
        traceback.print_exception(error_class, error_instance, error_traceback)
        print("=" * 50)
        
        # Let user select frame or default to innermost
        selected_frame = self.select_frame(frames)
        
        # Start the debug REPL
        try:
            self.start_repl(selected_frame.tb_frame, error_class, error_instance)
        except DebuggerContinue as cont:
            # User wants to continue execution
            print(f"Continuing execution by setting return value: {repr(cont.return_value)}")
            # If continue was called, execute code to set a variable with the return value
            if cont.return_value is not None:
                exec_in_scope(f"__vibezz_continue_value__ = {repr(cont.return_value)}")
            else:
                exec_in_scope("__vibezz_continue_value__ = None")
            return
        
        # If no continue was called, just pass (statement will be skipped)
        print("Skipping failed statement and continuing execution...")

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

    # Parse the function body into an AST and then offset all line numbers so
    # that they are relative to the *file*, not the extracted snippet starting
    # at line 1.  Without this adjustment the debugger thinks everything starts
    # at the top of the file which is exactly the behaviour we are trying to
    # fix.
    tree = ast.parse(source)
    ast.increment_lineno(tree, starting_line - 1)  # align with real file lines

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
                    # vdb = CustomPdb(llm)
                    ast.Assign(
                        targets=[ast.Name(id='vdb', ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Name(id='CustomPdb', ctx=ast.Load()),
                            args=[ast.Name(id='llm', ctx=ast.Load())],
                            keywords=[]
                        )
                    ),
                    # vdb.set_trace()
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id='vdb', ctx=ast.Load()),
                                attr='set_trace',
                                ctx=ast.Load(),
                            ),
                            args=[],
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
    exec(compiled, func.__globals__, namespace)
    return namespace[func.__name__]

# Test functions
def faulty_function():
    print("Starting faulty function...")
    
    a = 2 / 0  # This will trigger debugger
    
    b = 1
    print(f'b: {b}, a: {a}')
    
    c = [1, 2, 3]
    d = c[10]  # This will also trigger debugger
    
    print(f'c: {c}, d: {d}')
    
    e = "success!"
    print(f'Final result: {e}')

def another_test():
    x = 5
    y = 0
    z = x / y  # Another error
    print(f"Result: {z}")

def working_function():
    print("This function works perfectly!")
    result = 2 + 2
    print(f"2 + 2 = {result}")
    return result

def complex_function():
    print("Testing complex operations...")
    
    # This will work
    data = [1, 2, 3, 4, 5]
    print(f"Data: {data}")
    
    # This will fail
    bad_index = data[100]
    
    # This will also fail if we continue
    division_result = 10 / 0
    
    # This should work if we fix the above
    final_result = sum(data)
    print(f"Sum: {final_result}")

if __name__ == "__main__":
    print("🚀 Starting Vibezz - Enhanced Python Debugger")
    print("=" * 50)
    
    # Automatically instrument all functions
    vibezz_debugger.auto_instrument()
    
    print("\n" + "=" * 50)
    print("🎯 Running test functions...")
    print("=" * 50)
    
    # Now all functions are automatically instrumented
    print("\n1. Testing working_function...")
    working_function()
    
    print("\n2. Testing faulty_function...")
    faulty_function()
    
    print("\n3. Testing another_test...")
    another_test()
    
    print("\n4. Testing complex_function...")
    complex_function()
    
    print("\n✅ Vibezz debugging session complete!") 