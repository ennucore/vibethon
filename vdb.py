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

        # Clear internal state and start interaction in the desired frame.
        self.reset()
        self.interaction(frame, None)
    
    def write(self, data):
        # print(data, end="")
        self.llm.receive_pdb_output(data)
    
    def readline(self):
        cmd = self.llm.ask_for_next_command(prompt="pdb> ")
        # cmd = input("pdb> ")
        return cmd.rstrip("\n") + "\n"
    
    def flush(self):
        pass

if __name__ == "__main__":
    from llm import DummyLLM
    llm = DummyLLM()
    pdb = CustomPdb(llm)