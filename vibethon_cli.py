#!/usr/bin/env python3
"""
Vibethon - Automatic Python Debugger
A command-line tool that runs Python scripts with automatic function instrumentation.

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

# Import our debugger components
from vibezz import VibezzDebugger, instrument_function, vibezz_debugger

class VibethonImportHook(MetaPathFinder, Loader):
    """Custom import hook that automatically instruments functions in imported modules"""
    
    def __init__(self, debugger):
        self.debugger = debugger
        self.original_finder = None
        
    def find_spec(self, fullname, path, target=None):
        """Find module spec and mark it for instrumentation"""
        # Don't instrument built-in modules or our own debugger modules
        if (fullname in sys.builtin_module_names or 
            fullname.startswith('vibezz') or 
            fullname.startswith('vibethon') or
            fullname in ['__main__']):
            return None
            
        # Use the default import machinery to find the spec
        for finder in sys.meta_path:
            if finder is self:
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                # Wrap the loader to add instrumentation
                if hasattr(spec.loader, 'exec_module'):
                    original_exec = spec.loader.exec_module
                    spec.loader.exec_module = lambda module: self._exec_with_instrumentation(module, original_exec)
                return spec
        return None
    
    def _exec_with_instrumentation(self, module, original_exec):
        """Execute module and then instrument all its functions"""
        # Execute the module normally first
        original_exec(module)
        
        # Now instrument all functions in the module
        functions_instrumented = 0
        for name, obj in list(module.__dict__.items()):
            if (isinstance(obj, types.FunctionType) and 
                not name.startswith('_') and
                obj.__module__ == module.__name__ and
                obj.__code__ not in self.debugger.instrumented_functions):
                
                try:
                    instrumented_func = instrument_function(obj)
                    setattr(module, name, instrumented_func)
                    self.debugger.instrumented_functions.add(obj.__code__)
                    functions_instrumented += 1
                except Exception as e:
                    print(f"⚠️  Failed to instrument {module.__name__}.{name}: {e}")
        
        if functions_instrumented > 0:
            print(f"🔧 Auto-instrumented {functions_instrumented} functions in {module.__name__}")

class VibethonRunner:
    """Main runner for vibethon command"""
    
    def __init__(self):
        self.debugger = vibezz_debugger
        self.import_hook = VibethonImportHook(self.debugger)
        
    def setup_environment(self):
        """Setup the vibethon environment"""
        # Install our import hook
        if self.import_hook not in sys.meta_path:
            sys.meta_path.insert(0, self.import_hook)
        
        # Setup custom exception handling
        old_excepthook = sys.excepthook
        
        def vibethon_excepthook(exc_type, exc_value, exc_traceback):
            """Custom exception handler that starts the debugger REPL"""
            if exc_type is KeyboardInterrupt:
                old_excepthook(exc_type, exc_value, exc_traceback)
                return
                
            # Use our enhanced error handler
            self.debugger.handler(
                exc_type, exc_value, exc_traceback,
                lambda code: eval(code, {}),  # eval_in_scope
                lambda code: exec(code, {})   # exec_in_scope
            )
        
        sys.excepthook = vibethon_excepthook
        
        print("🚀 Vibethon environment initialized!")
        print("   - Automatic function instrumentation: ON")
        print("   - Enhanced error handling: ON")
        print("   - Debug REPL: ON")
        print()
    
    def _instrument_ast(self, tree):
        """Transform AST to instrument all function definitions with error handling"""
        class FunctionInstrumenter(ast.NodeTransformer):
            def __init__(self, debugger):
                self.debugger = debugger
                self.functions_instrumented = 0
            
            def visit_FunctionDef(self, node):
                # First, visit child nodes (for nested functions)
                self.generic_visit(node)
                
                # Don't instrument special methods or already instrumented functions
                if node.name.startswith('_'):
                    return node
                
                # Create new body with each statement wrapped in try/except
                new_body = []
                for stmt in node.body:
                    # Wrap each statement in a Try/Except block
                    try_node = ast.Try(
                        body=[stmt],
                        handlers=[ast.ExceptHandler(
                            type=ast.Name(id='Exception', ctx=ast.Load()),
                            name='e',
                            body=[
                                ast.Expr(
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id='sys', ctx=ast.Load()),
                                            attr='excepthook',
                                            ctx=ast.Load()
                                        ),
                                        args=[
                                            ast.Call(
                                                func=ast.Name(id='type', ctx=ast.Load()),
                                                args=[ast.Name(id='e', ctx=ast.Load())],
                                                keywords=[]
                                            ),
                                            ast.Name(id='e', ctx=ast.Load()),
                                            ast.Attribute(
                                                value=ast.Name(id='e', ctx=ast.Load()),
                                                attr='__traceback__',
                                                ctx=ast.Load()
                                            )
                                        ],
                                        keywords=[]
                                    )
                                )
                            ]
                        )],
                        orelse=[],
                        finalbody=[]
                    )
                    
                    # Copy location info from original statement
                    ast.copy_location(try_node, stmt)
                    new_body.append(try_node)
                
                # Replace function body with instrumented version
                node.body = new_body
                self.functions_instrumented += 1
                
                return node
        
        # Apply the transformation
        instrumenter = FunctionInstrumenter(self.debugger)
        instrumented_tree = instrumenter.visit(tree)
        
        # Fix missing location info
        ast.fix_missing_locations(instrumented_tree)
        
        if instrumenter.functions_instrumented > 0:
            print(f"🔧 Pre-instrumenting {instrumenter.functions_instrumented} functions...")
        
        return instrumented_tree
    
    def run_script(self, script_path, args=None):
        """Run a Python script with vibethon instrumentation"""
        if not os.path.exists(script_path):
            print(f"❌ Error: Script '{script_path}' not found")
            return 1
            
        # Setup sys.argv
        if args is None:
            args = []
        sys.argv = [script_path] + args
        
        # Setup environment
        self.setup_environment()
        
        # Read and execute the script
        try:
            with open(script_path, 'r') as f:
                code = f.read()
            
            # Parse the AST to find and instrument functions BEFORE execution
            filename = os.path.abspath(script_path)
            tree = ast.parse(code, filename)
            
            # Transform the AST to instrument all function definitions
            tree = self._instrument_ast(tree)
            
            # Compile the instrumented AST
            compiled = compile(tree, filename, 'exec')
            
            # Create a module-like namespace
            script_globals = {
                '__name__': '__main__',
                '__file__': filename,
                '__doc__': None,
                '__package__': None,
                'sys': sys,  # Make sys available for instrumented exception handling
            }
            
            print(f"🎯 Running '{script_path}' with vibethon...")
            print("=" * 50)
            
            # Execute the instrumented code
            exec(compiled, script_globals)
            
        except Exception as e:
            # This will be caught by our custom exception handler
            raise
        
        return 0
    
    def run_module(self, module_name, args=None):
        """Run a Python module with vibethon instrumentation"""
        if args is None:
            args = []
        sys.argv = ['-m', module_name] + args
        
        self.setup_environment()
        
        try:
            print(f"🎯 Running module '{module_name}' with vibethon...")
            print("=" * 50)
            
            import importlib
            module = importlib.import_module(module_name)
            
            # If the module has a main function or __main__ block, we need to handle it
            if hasattr(module, 'main'):
                module.main()
            else:
                # Try to run as if it were python -m module
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
        
        self.setup_environment()
        
        try:
            print("🎯 Running code with vibethon...")
            print("=" * 50)
            
            # Parse and instrument the AST before execution
            tree = ast.parse(code, '<string>')
            tree = self._instrument_ast(tree)
            compiled = compile(tree, '<string>', 'exec')
            
            script_globals = {
                '__name__': '__main__',
                '__file__': '<string>',
                '__doc__': None,
                '__package__': None,
                'sys': sys,  # Make sys available for instrumented exception handling
            }
            
            exec(compiled, script_globals)
            
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