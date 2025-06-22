#!/usr/bin/env python3
"""
Vibethon CLI - Command line interface for automatic Python debugging

Usage:
    vibethon script.py [args...]
    vibethon -m module [args...]
    vibethon -c "code"
"""

import sys
import os
import ast
import types
import importlib.util
import importlib.machinery
from importlib.abc import MetaPathFinder, Loader
import argparse
from pathlib import Path

# Import from the new module structure
from vibethon.vdb import CustomPdb
from vibethon.llm import ChatGPTPdbLLM, DummyLLM
import vibethon.vibezz                      # ← UPDATED – pull in the Vibezz framework
import inspect
import runpy

# Add the current directory to Python path so we can import local modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use the same LLM object that Vibezz is already configured with
llm = vibethon.vibezz.llm                   # ← UPDATED

# Provide a standalone pdb instance (only for on-the-fly use)
vdb = CustomPdb(llm)               # ← NEW

class VDBDebugger:
    """Simplified VDB-based debugger for function instrumentation tracking"""
    
    def __init__(self):
        self.instrumented_functions = set()
        self.llm = llm
        self.vdb = vdb
    
    def instrument_function(self, func):
        """VDB-based function instrumentation"""
        import inspect
        
        # Retrieve the function's source and starting line number
        source_lines, starting_line = inspect.getsourcelines(func)
        source = "".join(source_lines)

        # Parse and adjust line numbers
        tree = ast.parse(source)
        ast.increment_lineno(tree, starting_line - 1)

        func_def = tree.body[0]
        new_body = []
        
        for stmt in func_def.body:
            # Wrap each statement in try/except that uses VDB
            try_node = ast.Try(
                body=[stmt],
                handlers=[ast.ExceptHandler(
                    type=ast.Name(id='Exception', ctx=ast.Load()),
                    name='e',
                    body=[
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
            
            ast.copy_location(try_node, stmt)
            new_body.append(try_node)

        func_def.body = new_body
        ast.fix_missing_locations(tree)

        compiled = compile(
            tree,
            filename=func.__code__.co_filename,
            mode='exec'
        )
        
        # Execute in function's globals with VDB available
        namespace = func.__globals__.copy()
        namespace['vdb'] = self.vdb
        exec(compiled, namespace)
        return namespace[func.__name__]

class PostImportHook:
    """Intercept every import, then instrument the freshly-loaded module."""

    def __init__(self):
        import builtins as _py_builtins
        self.original_import = _py_builtins.__import__
        self.instrumented_modules: set[str] = set()

    def _should_instrument(self, module):
        """Return True if *module* is a pure-Python module we haven't touched."""
        if module.__name__ in self.instrumented_modules:
            return False
        file = getattr(module, "__file__", None)
        return bool(file and file.endswith(".py"))

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        module = self.original_import(name, globals, locals, fromlist, level)
        try:
            if self._should_instrument(module):
                print(f"🔧 Instrumenting module: {module.__name__}")
                vibethon.vibezz.vibezz_debugger.auto_instrument(module.__dict__)
                self.instrumented_modules.add(module.__name__)
        except Exception as err:
            print(f"⚠️  Failed to instrument {module.__name__}: {err}")
        return module

# Create global Vibezz debugger instance
vdb_debugger = vibethon.vibezz.vibezz_debugger

class VibethonRunner:
    """Main runner for vibethon command"""
    
    def __init__(self):
        self.debugger = vdb_debugger
        self.post_import_hook = PostImportHook()
        
    def setup_environment(self):
        """Setup the vibethon environment"""
        # Monkey-patch built-in import so every future import gets instrumented
        import builtins as _py_builtins
        _py_builtins.__import__ = self.post_import_hook
            
        print("🚀 Vibethon environment initialized!")
        print("   - Automatic function instrumentation: ON")
        print("   - VDB error handling: ON")
        print("   - LLM-powered debugging: ON")
        print()
    
    # ------------------------------------------------------------------
    # Helper – pull out the  `if __name__ == '__main__':`  block
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_main_block(src: str, filename: str):
        import ast
        tree = ast.parse(src, filename=filename)
        for node in tree.body:
            if (isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == '__name__'
                and any(isinstance(c, ast.Constant) and c.value == '__main__'
                        for c in node.test.comparators)):
                mod = ast.Module(body=node.body, type_ignores=[])
                return compile(ast.fix_missing_locations(mod), filename, 'exec')
        return None

    # ------------------------------------------------------------------
    # Actual runner
    # ------------------------------------------------------------------
    def run_script(self, script_path, args=None):
        """Import script, instrument it, then run its entry-point."""
        if not os.path.exists(script_path):
            print(f"❌ Error: Script '{script_path}' not found")
            return 1

        if args is None:
            args = []
        sys.argv = [script_path] + args

        try:
            import importlib.util, textwrap
            from pathlib import Path

            abs_path   = Path(script_path).resolve()
            # Use the real module name so auto_instrument() recognises it
            module_name = abs_path.stem
            # If it was already imported earlier, drop it so we get a fresh copy
            sys.modules.pop(module_name, None)

            print(f"🎯 Importing '{abs_path}' …")
            spec   = importlib.util.spec_from_file_location(module_name, abs_path)
            module = importlib.util.module_from_spec(spec)

            # Make debugger helpers visible before code runs
            module.CustomPdb = CustomPdb
            module.llm       = llm
            sys.modules[module_name] = module
            
            # Execute the module (this will trigger import hook for any imports)
            spec.loader.exec_module(module)

            # Instrument the main module's functions
            print(f"🔧 Instrumenting main module: {module_name}")
            vibethon.vibezz.vibezz_debugger.auto_instrument(module.__dict__)

            # ── Run entry-point ────────────────────────────────────────────
            if callable(module.__dict__.get("main")):
                print("▶️  Calling main()")
                module.main()
            else:
                with open(abs_path, 'r', encoding='utf8') as fh:
                    src = fh.read()
                code_obj = self._extract_main_block(src, str(abs_path))
                if code_obj:
                    print("▶️  Executing script's __main__ block")
                    exec(code_obj, module.__dict__)
                else:
                    print("⚠️  No entry point found (main() or __main__ block)")

        except Exception:
            # Unhandled exceptions will trigger CustomPdb via the excepthook
            raise

        return 0
    
    def run_module(self, module_name, args=None):
        """Run a Python module with VDB instrumentation"""
        if args is None:
            args = []
        sys.argv = ['-m', module_name] + args
        
        try:
            print(f"🎯 Running module '{module_name}' with vibethon...")
            print("=" * 50)
            
            import importlib
            module = importlib.import_module(module_name)
            
            if hasattr(module, 'main'):
                module.main()
            else:
                import runpy
                runpy.run_module(module_name, run_name='__main__')
                
        except Exception as e:
            raise
        
        return 0
    
    def run_code(self, code, args=None):
        """Run Python code directly with vibethon instrumentation"""
        if args is None:
            args = []
        sys.argv = ['-c'] + args
        
        try:
            print("🎯 Running code with vibethon...")
            print("=" * 50)
            
            # Parse and instrument the AST
            tree = ast.parse(code, '<string>')
            compiled = compile(tree, '<string>', 'exec')
            
            script_globals = {
                '__name__': '__main__',
                '__file__': '<string>',
                '__doc__': None,
                '__package__': None,
                'sys': sys,
                'CustomPdb': CustomPdb,     # NEW
                'llm': llm,                 # NEW
            }
            
            exec(compiled, script_globals)
            
            # After execution, automatically instrument the defined functions using Vibezz
            vibethon.vibezz.vibezz_debugger.auto_instrument(script_globals)
            
        except Exception as e:
            raise
        
        return 0

def main():
    """Main entry point for vibethon command"""
    parser = argparse.ArgumentParser(
        description='Vibethon - Automatic Python Debugger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vibethon script.py                 # Run script.py with debugging
  vibethon script.py arg1 arg2       # Run script.py with arguments
  vibethon -m mymodule               # Run module with debugging
  vibethon -c "print('hello')"       # Run code string with debugging
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('script', nargs='?', help='Python script to run')
    group.add_argument('-m', '--module', help='Run module as script')
    group.add_argument('-c', '--code', help='Run code string')
    
    parser.add_argument('args', nargs='*', help='Arguments to pass to the script/module')
    
    args = parser.parse_args()
    
    runner = VibethonRunner()
    
    try:
        if args.script:
            return runner.run_script(args.script, args.args)
        elif args.module:
            return runner.run_module(args.module, args.args)
        elif args.code:
            return runner.run_code(args.code, args.args)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        return 1
    except SystemExit as e:
        return e.code if e.code is not None else 0
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 