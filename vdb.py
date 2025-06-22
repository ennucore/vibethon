import pdb
import sys


class CustomPdb(pdb.Pdb):
    def __init__(self, llm_client):
        self.llm = llm_client
        super().__init__(stdin=self, stdout=self)
        self.set_trace()

    def set_trace(self, frame=None):
        super().set_trace(frame)
        import traceback

        # Print stack trace to LLM
        stack = traceback.format_stack()
        self.llm.receive_pdb_output("PDB started\n" + "".join(stack))

        # Print local variables to LLM
        frame = self.curframe
        if frame is not None:
            local_vars = frame.f_locals
            locals_str = "Local variables:\n"
            for name, value in local_vars.items():
                try:
                    val_repr = repr(value)
                except Exception:
                    val_repr = "<unrepresentable>"
                locals_str += f"  {name} = {val_repr}\n"
            self.llm.receive_pdb_output(locals_str)
    
    def write(self, data):
        self.llm.receive_pdb_output(data)
    
    def readline(self):
        cmd = self.llm.ask_for_next_command(prompt="pdb> ")
        return cmd.rstrip("\n") + "\n"
    
    def flush(self):
        pass

if __name__ == "__main__":
    from llm import DummyLLM
    llm = DummyLLM()
    pdb = CustomPdb(llm)