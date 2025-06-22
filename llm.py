import openai

class ChatGPTPdbLLM:
    def __init__(self, model="gpt-4.1", system_message=None):
        self.model = model
        self.messages = []
        self.last_output = ""
        self.system_message = system_message or (
            "You are an expert Python debugger, interacting in a pdb REPL session. "
            "You have access to pdb commands (next, continue, list, set variables, eval variables, etc). "
            "Your goal is to figure out what is wrong with the code, and suggest the right pdb commands to fix the execution at runtime, "
            "so that execution can continue successfully. If you make changes at runtime, print suggestions for what should be fixed in the source code. "
            "Respond ONLY with the next pdb command to execute, and optionally a short comment (in a print statement) explaining your reasoning or suggestion."
        )
        self._init_messages()

    def _init_messages(self):
        self.messages = [
            {"role": "system", "content": self.system_message}
        ]

    def ask_for_next_command(self, prompt):
        # Add the latest output from the debugger as context
        if self.last_output:
            self.messages.append({
                "role": "user",
                "content": f"Debugger output:\n{self.last_output.strip()}\n\n{prompt.strip()}\nWhat is the next pdb command to execute? Respond ONLY with the pdb command."
            })
        else:
            self.messages.append({
                "role": "user",
                "content": f"{prompt.strip()}\nWhat is the next pdb command to execute? Respond ONLY with the pdb command."
            })

        response = openai.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.2,
            max_tokens=64,
        )
        reply = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": reply})
        print(reply)
        return reply

    def receive_pdb_output(self, output):
        # Store the latest output for context in the next prompt
        print(output, end="")
        self.last_output = output



class DummyLLM:
    def ask_for_next_command(self, prompt):
        return input(prompt)
    
    def receive_pdb_output(self, output):
        print(output, end="")
