from vibethon.models import models
from openai import OpenAI
import time

openai = OpenAI(
    base_url="https://openrouter.ai/api/v1",
)

class ChatGPTPdbLLM:
    def __init__(self, system_message=None, memory_limit=15):
        self.model = "anthropic/claude-sonnet-4"
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

Note that expressions that begin with letters that are pdb commands, should be preceded by a `!` to be interpreted as an expression (eg variable assignment `a=2` should be `!a=2`)

At each step you are interacting with the intern, you should emit a JSON that adheres to the following
typed dict:

import typing as T

class DebuggerStep(T.TypedDict):
    command: str
    explanation: str

Go step-by-step as you reason. Think carefully. Please just return the JSON, no other text.

If you get really stuck and don't know what to do, please don't continue. Stop, and let me know that you need help.
In your help message, please use a baby emoji so that the need for help is clear: 👶
            """.strip()
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
        if self.messages == []:
            user_content = (
                "This is the start of a debugging session.\n"
                f"Use this initial context to help choose the first debugging command:\n{getattr(self, 'initial_context', '').strip()}\n"
                "Emit the first debugging command as JSON. Please format it as JSON ALWAYS. Do not include any other text outside the JSON:\n"
            )
        else:
            user_content = (
                f"Initial context:\n{getattr(self, 'initial_context', '').strip()}\n"
                f"Debugger output:\n{self.last_output.strip()}\n"
                "Emit the next output dictionary after this line. Please format it as JSON ALWAYS. Do not include any other text outside the JSON:\n"
            )
        
        self.messages.append({
            "role": "user",
            "content": user_content
        })

        # Keep only the most recent N turns of memory (plus system prompt)
        if len(self.messages) > self.memory_limit + 1:
            self.messages = [self.messages[0]] + self.messages[-self.memory_limit:]

        response = openai.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.2,
            max_tokens=256,  # Increased to reduce truncation
        )
        import json

        raw_reply_full = response.choices[0].message.content.strip()
        # Try to extract the first JSON object by looking for the first '{' and last '}'
        start = raw_reply_full.find('{')
        end = raw_reply_full.rfind('}')
        if start != -1 and end != -1 and end > start:
            raw_reply = raw_reply_full[start:end+1]
        else:
            raw_reply = raw_reply_full

        explanation = None
        command = None
        try:
            parsed = json.loads(raw_reply)
            if isinstance(parsed, dict) and "command" in parsed:
                command = parsed["command"]
                explanation = parsed.get("explanation")
            else:
                command = raw_reply
        except Exception:
            # If not valid JSON, just use the raw reply
            command = raw_reply

        self.messages.append({"role": "assistant", "content": raw_reply})

        # Save self.messages to a file for debugging/auditing
        try:
            with open("llm_messages.json", "w", encoding="utf-8") as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save llm_messages.json: {e}")
        
        print(command)
        if explanation:
            print(f"Explanation: {explanation}")
        # input("Press Enter to continue...")
        return command

    def receive_pdb_output(self, output):
        print(output, end="")
        self.last_output = output
    
    def set_initial_context(self, context):
        self.initial_context = context



class DummyLLM:
    def ask_for_next_command(self, prompt):
        return input(prompt)
    
    def receive_pdb_output(self, output):
        print(output, end="")
