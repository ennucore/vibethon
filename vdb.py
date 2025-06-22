import pdb
import sys
import io
import ctypes  # Needed to call PyFrame_LocalsToFast (CPython API)

# ---------------------------------------------------------------------------
# CPython helper – push updates in frame.f_locals back to the fast-locals
# array so that running byte-code can see them.
# ---------------------------------------------------------------------------

_PyFrame_LocalsToFast = ctypes.pythonapi.PyFrame_LocalsToFast  # type: ignore[attr-defined]
_PyFrame_LocalsToFast.argtypes = (ctypes.py_object, ctypes.c_int)  # (frame, clear)
_PyFrame_LocalsToFast.restype = None


def _locals_to_fast(frame):
    """Copy the frame.f_locals dict back into fast locals (CPython only)."""
    _PyFrame_LocalsToFast(frame, 0)


class CustomPdb(pdb.Pdb):
    def __init__(self, llm_client):
        """Create a CustomPdb instance.

        We *don't* automatically drop into the debugger here because the
        caller should be able to specify which frame to attach to.  The caller
        must therefore invoke ``set_trace(frame)`` (or simply ``set_trace()``
        for the current frame) after instantiation.
        """
        self.llm = llm_client
        self._output_buffer = io.StringIO()
        super().__init__(stdin=self, stdout=self._output_buffer)

    def set_trace(self, frame=None):
        """Enter debugging session at *frame* immediately.

        Unlike `pdb.Pdb.set_trace`, this version stops exactly in the
        requested frame instead of on the next trace event.  That ensures
        commands like `list` show the original source line that raised an
        exception rather than a line inside our helper code.
        """
        if frame is None:
            frame = sys._getframe().f_back
        
        import traceback

        print("\n🔎 Entering new pdb session!")
        print(f"Target frame: {frame}")
        print(f"Target frame locals keys: {list(frame.f_locals.keys())}")
        print("Stack trace (most recent call last):")
        traceback.print_stack(frame)
        print("=" * 50)

        # Provide initial context to the LLM
        initial_context = self._gather_initial_context(frame)
        print(initial_context)
        self.llm.set_initial_context(initial_context)
        
        # Clear internal state and start interaction in the desired frame.
        self.reset()
        
        # Set the current frame to the target frame so pdb operates in the right context
        self.curframe = frame
        self.curindex = 0
        
        print(f"Debugger curframe: {self.curframe}")
        print(f"Debugger curframe locals keys: {list(self.curframe.f_locals.keys())}")
        
        # Create a minimal stack with just the target frame
        self.stack = [(frame, frame.f_lineno)]
        
        # Start the interaction loop
        self.interaction(frame, None)
    
    def _gather_initial_context(self, frame):
        """Gather comprehensive initial debugging context."""
        import traceback
        context_parts = []
        
        # Stack trace
        context_parts.append("=== DEBUGGING SESSION STARTED ===")
        context_parts.append("Stack trace (most recent call last):")
        context_parts.append(''.join(traceback.format_stack(frame)))
        
        # Current frame info
        context_parts.append(f"Current file: {frame.f_code.co_filename}")
        context_parts.append(f"Current function: {frame.f_code.co_name}")
        context_parts.append(f"Current line: {frame.f_lineno}")
        
        # Local variables (safely)
        context_parts.append("\nLocal variables:")
        try:
            from pprint import saferepr
            safe_locals = {k: v for k, v in frame.f_locals.items() 
                          if k not in ('e', 'vdb')}
            for name, value in safe_locals.items():
                try:
                    context_parts.append(f"  {name} = {saferepr(value)}")
                except Exception:
                    context_parts.append(f"  {name} = <unrepresentable>")
        except Exception as e:
            context_parts.append(f"  Error getting locals: {e}")
        
        # Current source context
        context_parts.append(f"\nSource context around line {frame.f_lineno}:")
        try:
            self._add_source_context(context_parts, frame)
        except Exception as e:
            context_parts.append(f"  Error getting source: {e}")
        
        return '\n'.join(context_parts)
    
    def _add_source_context(self, context_parts, frame):
        """Add source code context to the context parts."""
        import linecache
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        
        # Show 5 lines before and after current line
        for i in range(max(1, lineno - 5), lineno + 6):
            line = linecache.getline(filename, i)
            if line:
                marker = '-> ' if i == lineno else '   '
                context_parts.append(f"{marker}{i:4d}: {line.rstrip()}")
    
    def write(self, data):
        # Capture output in buffer instead of sending directly to LLM
        self._output_buffer.write(data)
    
    def readline(self):
        # Get the buffered output and send it to LLM before asking for next command
        buffered_output = self._output_buffer.getvalue()
        if buffered_output.strip():
            self.llm.receive_pdb_output(buffered_output)
            # Clear the buffer for next command
            self._output_buffer = io.StringIO()
            # Reset stdout to new buffer
            self.stdout = self._output_buffer
        
        cmd = self.llm.ask_for_next_command()
        return cmd.rstrip("\n") + "\n"
    
    def flush(self):
        pass

    def do_locals(self, arg):
        """Show local variables from the original frame, excluding debugger internals."""
        from pprint import saferepr
        
        # Get the original frame if available
        original_frame = self.curframe
        if '_original_frame' in self.curframe.f_locals:
            original_frame = self.curframe.f_locals['_original_frame']
            print(f"DEBUG: Using _original_frame for locals: {original_frame}")
        
        # Get locals from the original frame
        frame_locals = original_frame.f_locals
        
        # Filter out debugger-related variables and show only user variables
        safe = {k: v for k, v in frame_locals.items()
                if k not in ('e', 'vdb', '_original_frame', '_name', '_value') and not k.startswith('__')}
        
        if safe:
            self.message("Local variables:")
            for name, value in safe.items():
                try:
                    self.message(f"  {name} = {saferepr(value)}")
                except Exception:
                    self.message(f"  {name} = <unrepresentable>")
        else:
            self.message("No local variables found (or all filtered out)")

    # ------------------------------------------------------------------
    # Custom implementation of the `list` command that understands Vibezz's
    # instrumented functions.  It maps the *relative* line numbers that appear
    # in the compiled wrapper back to the *real* line numbers in the source
    # file without requiring us to patch `lineno` attributes in the AST.
    # ------------------------------------------------------------------

    def do_list(self, arg):  # noqa: D401 – keep Pdb command signature
        import sys as _sys
        _VIBEZZ_SOURCE_MAP = {}
        for _mod_name in ('vibezz', '__main__'):
            _mod = _sys.modules.get(_mod_name)
            if _mod is not None and hasattr(_mod, '_VIBEZZ_SOURCE_MAP'):
                _VIBEZZ_SOURCE_MAP = getattr(_mod, '_VIBEZZ_SOURCE_MAP')
                break

        co = self.curframe.f_code

        if co in _VIBEZZ_SOURCE_MAP:
            src_lines, start_line, filename = _VIBEZZ_SOURCE_MAP[co]

            # Determine which lines to show.
            if arg:
                try:
                    if ',' in arg:
                        first, last = map(int, arg.replace(',', ' ').split())
                    else:
                        first = int(arg)
                        last = first + 10  # show 10 lines starting at *first*
                except ValueError:
                    self.error("Invalid list range")
                    return
            else:
                rel_lineno = self.curframe.f_lineno
                first = max(1, rel_lineno - 5)
                last = min(len(src_lines), rel_lineno + 5)

            for idx in range(first, last + 1):
                marker = '-> ' if idx == self.curframe.f_lineno else '   '
                real_lineno = start_line + idx - 1
                # Guard against index overflow (can happen near function end)
                if 0 <= idx - 1 < len(src_lines):
                    line_text = src_lines[idx - 1].rstrip()
                else:
                    line_text = ''
                self.message(f"{marker}{real_lineno:4d}\t{line_text}")

            self.lastcmd = 'list'
            return

        # Fallback to standard behaviour for non-instrumented code
        super().do_list(arg)

    def default(self, line):
        """Override default to execute commands in the original frame's context."""
        if line[:1] == '!':
            line = line[1:]
        
        # Try to execute the command in the original frame's context
        try:
            # Get the original frame from the traceback if available
            original_frame = self.curframe
            
            # If we have access to the original frame via _original_frame variable in locals
            if '_original_frame' in self.curframe.f_locals:
                original_frame = self.curframe.f_locals['_original_frame']
                print(f"DEBUG: Using _original_frame for execution: {original_frame}")
                print(f"DEBUG: Original frame locals before: {list(original_frame.f_locals.keys())}")
            
            # Use the original frame's globals and locals for execution
            code = compile(line + '\n', '<stdin>', 'single')
            exec(code, original_frame.f_globals, original_frame.f_locals)
            
            # Flush changes so the running byte-code can see them
            _locals_to_fast(original_frame)

            if '_original_frame' in self.curframe.f_locals:
                print(f"DEBUG: Original frame locals after exec & flush: {list(original_frame.f_locals.keys())}")
                
        except Exception as e:
            print(f"DEBUG: Exception in default: {e}")
            # If that fails, fall back to the standard behavior
            super().default('!' + line)
    
    def do_pp(self, arg):
        """Pretty-print the value of an expression in the original frame's context."""
        try:
            # Get the original frame if available
            original_frame = self.curframe
            if '_original_frame' in self.curframe.f_locals:
                original_frame = self.curframe.f_locals['_original_frame']
            
            # Evaluate in the original frame's context
            val = eval(arg, original_frame.f_globals, original_frame.f_locals)
            self.message(repr(val))
        except Exception as e:
            self.message(f"Error evaluating '{arg}': {e}")
    
    def do_p(self, arg):
        """Print the value of an expression in the original frame's context."""
        try:
            # Get the original frame if available
            original_frame = self.curframe
            if '_original_frame' in self.curframe.f_locals:
                original_frame = self.curframe.f_locals['_original_frame']
                
            # Evaluate in the original frame's context  
            val = eval(arg, original_frame.f_globals, original_frame.f_locals)
            self.message(repr(val))
        except Exception as e:
            self.message(f"Error evaluating '{arg}': {e}")

    def do_debug_frame(self, arg):
        """Show debugging information about the current frame."""
        self.message(f"Current frame: {self.curframe}")
        self.message(f"Current frame file: {self.curframe.f_code.co_filename}")
        self.message(f"Current frame function: {self.curframe.f_code.co_name}")
        self.message(f"Current frame line: {self.curframe.f_lineno}")
        self.message(f"Current frame locals keys: {list(self.curframe.f_locals.keys())}")
        
        # Show the actual locals values (safely)
        # Refresh mapping so it reflects current fast-locals
        _locals_to_fast(self.curframe)
        frame_locals = self.curframe.f_locals
        safe_locals = {k: v for k, v in frame_locals.items() 
                      if k not in ('e', 'vdb', '_original_frame', '_name', '_value') and not k.startswith('__')}
        
        self.message("Safe locals:")
        for name, value in safe_locals.items():
            try:
                self.message(f"  {name} = {repr(value)}")
            except Exception:
                self.message(f"  {name} = <unrepresentable>")

if __name__ == "__main__":
    from llm import DummyLLM
    llm = DummyLLM()
    pdb = CustomPdb(llm)