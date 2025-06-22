import pdb
import sys


class CustomPdb(pdb.Pdb):
    def __init__(self, llm_client):
        """Create a CustomPdb instance.

        We *don't* automatically drop into the debugger here because the
        caller should be able to specify which frame to attach to.  The caller
        must therefore invoke ``set_trace(frame)`` (or simply ``set_trace()``
        for the current frame) after instantiation.
        """
        self.llm = llm_client
        super().__init__(stdin=self, stdout=self)

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
        print("Stack trace (most recent call last):")
        traceback.print_stack(frame)
        print("=" * 50)

        self.llm.receive_pdb_output(f"PDB session started. Stack trace (most recent call last):\n{traceback.format_stack(frame)}")

        # Clear internal state and start interaction in the desired frame.
        self.reset()
        self.interaction(frame, None)
    
    def write(self, data):
        # print(data, end="")
        self.llm.receive_pdb_output(data)
    
    def readline(self):
        cmd = self.llm.ask_for_next_command()
        # cmd = input("pdb> ")
        return cmd.rstrip("\n") + "\n"
    
    def flush(self):
        pass

    def do_locals(self, arg):
        from pprint import saferepr
        safe = {k: v for k, v in self.curframe.f_locals.items()
                if k not in ('e', 'vdb')}
        self.message(saferepr(safe))

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

if __name__ == "__main__":
    from llm import DummyLLM
    llm = DummyLLM()
    pdb = CustomPdb(llm)