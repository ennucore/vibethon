class DummyLLM:
    def ask_for_next_command(self, prompt):
        print(prompt)
        return input('> ')
    
    def receive_pdb_output(self, output):
        print(output)
