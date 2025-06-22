import openai
import time

class ChatGPTPdbLLM:
    def __init__(self, model="sonnet-4-sonnet", system_message=None, memory_limit=15):
        self.model = model
        self.messages = []
        self.last_output = ""
        self.system_message = system_message or (
            """
You are an expert Python programmer and debugger. You understand the internals of Python
extremely well. You are also AWARE of your limits, and if you are confused by what is happening,
you will stop and say so.

You are sitting next to an inexperienced intern who needs help with their code, and you are going
to tell them what to type at a PDB prompt in order to debug what is happening. You want the intern
to be able to learn, so you are going to explain your reasoning and output the exact command to run.

After the intern understands the problem, you are going to issue ANOTHER sequence of commands to help
them fix the problem. You will modify local variables to fix the execution at runtime. When you are done,
the program should execute flawlessly.

You are in a pdb session, which in this context means that the line you begin the session at triggered an exception. The line that is pointed at when running `l` is the last line that was attempted to be executed, and which raised the exception. The next line is the line that will be executed next, if the command `next` is used.

Use `continue`, rather than `quit`.

At each step you are interacting with the intern, you should emit a JSON that adheres to the following
typed dict:

import typing as T

class DebuggerStep(T.TypedDict):
    command: str
    explanation: str

Go step-by-step as you reason. Think carefully.

### EXAMPLE SESSION ###

INPUT:
Stack trace (most recent call last):
  File "/Users/nudge/code/vibethon/vibezz.py", line 369, in <module>
    faulty_function()
  File "/Users/nudge/code/vibethon/vibezz.py", line 311, in faulty_function
    a = 0
    foo = 20 / a  # This will trigger debugger

OUTPUT:
{
    "command": "!foo = 20 / 1e-6",
    "explanation": "The user probably intended a to be small but not zero, as that will trigger an exception"
}

INPUT: ""
OUTPUT:
{
    "command": "continue",
    "explanation": "This should have fixed the problem, so we can continue"
}

### END OF EXAMPLE SESSION ###

            """.strip()
            # "You are in a custom pdb session."
            # "Try modify the local variables to fix the execution at runtime!"
            # "Note that you can do this by `!a=2` eg. Send the exact command, no placeholders. Please use this!!"
            # "You can also use commands like `l`, `n`, etc. "
            # "Justify your answer and print the justification in the output."
        )
        self.memory_limit = memory_limit  # How many turns of memory to keep
        self._init_messages()

    def _init_messages(self):
        # Start with a system prompt for persistent context
        self.messages = [{
            "role": "system",
            "content": self.system_message
        }]

    def ask_for_next_command(self):
        # Compose the user message, referencing the last output and prompt
        assert self.last_output, "No last output to reference"
        user_content = (
            f"Debugger output:\n{self.last_output.strip()}\n"
            "Emit the next output dictionary after this line:\n"
        )
        self.messages.append({
            "role": "user",
            "content": user_content
        })

        # Keep only the most recent N turns of memory (plus system prompt)
        if len(self.messages) > self.memory_limit + 1:
            # Always keep the system prompt at index 0
            self.messages = [self.messages[0]] + self.messages[-self.memory_limit:]

        response = openai.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.2,
            max_tokens=64,
        )
        # Parse the response as a JSON object, if possible, to extract the command and explanation
        import json

        raw_reply = response.choices[0].message.content.strip()
        explanation = None
        try:
            parsed = json.loads(raw_reply)
            if isinstance(parsed, dict) and "command" in parsed:
                command = parsed["command"]
                explanation = parsed.get("explanation")
            else:
                # Fallback: if not a dict or missing "command", use the raw reply
                command = raw_reply
        except Exception:
            # If not valid JSON, just use the raw reply
            command = raw_reply

        self.messages.append({"role": "assistant", "content": raw_reply})
        # Save self.messages to a file for debugging/auditing
        try:
            with open("llm_messages.json", "w", encoding="utf-8") as f:
                import json
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save llm_messages.json: {e}")
        print(command)
        if explanation:
            print(f"Explanation: {explanation}")
        input("Press Enter to continue...")
        return command

    def receive_pdb_output(self, output):
        # Store the latest output for context in the next prompt
        print(output, end="")
        self.last_output = output



class DummyLLM:
    def ask_for_next_command(self, prompt):
        return input(prompt)
    
    def receive_pdb_output(self, output):
        print(output, end="")
