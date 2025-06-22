import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import io
from vdb import CustomPdb
from llm import ChatGPTPdbLLM, DummyLLM


class TestCustomPdb(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = Mock()
        self.pdb_instance = CustomPdb(self.mock_llm)
    
    def test_init(self):
        """Test CustomPdb initialization."""
        self.assertEqual(self.pdb_instance.llm, self.mock_llm)
        self.assertIsInstance(self.pdb_instance._output_buffer, io.StringIO)
        # Check that stdin and stdout are properly set
        self.assertEqual(self.pdb_instance.stdin, self.pdb_instance)
        self.assertEqual(self.pdb_instance.stdout, self.pdb_instance._output_buffer)
    
    def test_gather_initial_context(self):
        """Test the _gather_initial_context method."""
        # Create a mock frame
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "/test/file.py"
        mock_frame.f_code.co_name = "test_function"
        mock_frame.f_lineno = 42
        mock_frame.f_locals = {"x": 1, "y": "hello", "e": Exception(), "vdb": self.pdb_instance}
        
        with patch('traceback.format_stack') as mock_traceback:
            mock_traceback.return_value = ["  File test.py, line 1\n", "    code here\n"]
            
            with patch.object(self.pdb_instance, '_add_source_context') as mock_source:
                context = self.pdb_instance._gather_initial_context(mock_frame)
                
                # Check that context contains expected elements
                self.assertIn("=== DEBUGGING SESSION STARTED ===", context)
                self.assertIn("Stack trace", context)
                self.assertIn("/test/file.py", context)
                self.assertIn("test_function", context)
                self.assertIn("42", context)
                self.assertIn("Local variables:", context)
                self.assertIn("x = 1", context)
                self.assertIn("y = 'hello'", context)
                # Should exclude 'e' and 'vdb'
                self.assertNotIn("e =", context)
                self.assertNotIn("vdb =", context)
                
                mock_source.assert_called_once()
    
    def test_add_source_context(self):
        """Test the _add_source_context method."""
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "/test/file.py"
        mock_frame.f_lineno = 5
        
        context_parts = []
        
        with patch('linecache.getline') as mock_getline:
            # Mock line cache to return test lines
            def mock_get_line(filename, lineno):
                lines = {
                    1: "def test_function():\n",
                    2: "    x = 1\n", 
                    3: "    y = 2\n",
                    4: "    z = x + y\n",
                    5: "    raise ValueError('test error')\n",  # Current line
                    6: "    return z\n",
                    7: "\n",
                    8: "# End of function\n"
                }
                return lines.get(lineno, "")
            
            mock_getline.side_effect = mock_get_line
            
            self.pdb_instance._add_source_context(context_parts, mock_frame)
            
            # Check that context was added
            context_text = '\n'.join(context_parts)
            self.assertIn("def test_function():", context_text)
            self.assertIn("-> ", context_text)  # Current line marker
            self.assertIn("raise ValueError('test error')", context_text)
    
    def test_write_buffers_output(self):
        """Test that write method buffers output instead of sending directly."""
        test_data = "Test output"
        self.pdb_instance.write(test_data)
        
        # Should not call LLM immediately
        self.mock_llm.receive_pdb_output.assert_not_called()
        
        # Should buffer the data
        self.assertEqual(self.pdb_instance._output_buffer.getvalue(), test_data)
    
    def test_readline_sends_buffered_output(self):
        """Test that readline sends buffered output before asking for command."""
        # Buffer some output
        test_output = "Buffered output"
        self.pdb_instance.write(test_output)
        
        # Mock LLM to return a command
        self.mock_llm.ask_for_next_command.return_value = "list"
        
        result = self.pdb_instance.readline()
        
        # Should have sent buffered output to LLM
        self.mock_llm.receive_pdb_output.assert_called_once_with(test_output)
        
        # Should have asked for next command
        self.mock_llm.ask_for_next_command.assert_called_once()
        
        # Should return command with newline
        self.assertEqual(result, "list\n")
        
        # Buffer should be cleared and stdout reset
        self.assertEqual(self.pdb_instance._output_buffer.getvalue(), "")
        self.assertEqual(self.pdb_instance.stdout, self.pdb_instance._output_buffer)
    
    def test_readline_empty_buffer(self):
        """Test readline when buffer is empty."""
        self.mock_llm.ask_for_next_command.return_value = "next"
        
        result = self.pdb_instance.readline()
        
        # Should not call receive_pdb_output for empty buffer
        self.mock_llm.receive_pdb_output.assert_not_called()
        
        # Should still ask for command
        self.mock_llm.ask_for_next_command.assert_called_once()
        self.assertEqual(result, "next\n")
    
    def test_do_locals_safe(self):
        """Test do_locals method excludes dangerous variables."""
        # Set up a mock frame with locals
        mock_frame = Mock()
        mock_frame.f_locals = {
            "safe_var": "safe_value",
            "e": Exception("dangerous"),
            "vdb": self.pdb_instance,
            "normal_var": 42
        }
        self.pdb_instance.curframe = mock_frame
        
        with patch.object(self.pdb_instance, 'message') as mock_message:
            self.pdb_instance.do_locals("")
            
            # Should have called message with safe representation
            mock_message.assert_called_once()
            call_args = mock_message.call_args[0][0]
            
            # Should include safe variables
            self.assertIn("safe_var", call_args)
            self.assertIn("normal_var", call_args)
            
            # Should exclude dangerous variables
            self.assertNotIn("'e':", call_args)
            self.assertNotIn("'vdb':", call_args)
    
    @patch('sys._getframe')
    def test_set_trace_with_frame(self, mock_getframe):
        """Test set_trace method with provided frame."""
        mock_frame = Mock()
        mock_frame.f_code.co_filename = "/test/file.py"
        mock_frame.f_code.co_name = "test_func"
        mock_frame.f_lineno = 10
        mock_frame.f_locals = {"x": 1}
        
        with patch.object(self.pdb_instance, 'reset') as mock_reset, \
             patch.object(self.pdb_instance, 'interaction') as mock_interaction, \
             patch('builtins.print'):  # Suppress print output
            
            self.pdb_instance.set_trace(mock_frame)
            
            # Should have called LLM with initial context
            self.mock_llm.receive_pdb_output.assert_called_once()
            call_args = self.mock_llm.receive_pdb_output.call_args[0][0]
            self.assertIn("=== DEBUGGING SESSION STARTED ===", call_args)
            
            # Should have reset and started interaction
            mock_reset.assert_called_once()
            mock_interaction.assert_called_once_with(mock_frame, None)
    
    @patch('sys._getframe')
    def test_set_trace_without_frame(self, mock_getframe):
        """Test set_trace method without provided frame."""
        mock_caller_frame = Mock()
        mock_getframe.return_value.f_back = mock_caller_frame
        
        with patch.object(self.pdb_instance, 'reset'), \
             patch.object(self.pdb_instance, 'interaction'), \
             patch.object(self.pdb_instance, '_gather_initial_context') as mock_context, \
             patch('builtins.print'):
            
            mock_context.return_value = "test context"
            self.pdb_instance.set_trace()
            
            # Should have used caller's frame
            mock_context.assert_called_once_with(mock_caller_frame)

    def test_do_list_vibezz_source_map(self):
        """Test do_list with vibezz source map."""
        # Mock curframe
        mock_frame = Mock()
        mock_code = Mock()
        mock_frame.f_code = mock_code
        mock_frame.f_lineno = 3
        self.pdb_instance.curframe = mock_frame
        
        # Mock vibezz source map
        src_lines = ["line 1", "line 2", "line 3", "line 4", "line 5"]
        start_line = 10
        filename = "test.py"
        
        with patch('sys.modules') as mock_modules:
            mock_main = Mock()
            mock_main._VIBEZZ_SOURCE_MAP = {mock_code: (src_lines, start_line, filename)}
            mock_modules.get.return_value = mock_main
            
            with patch.object(self.pdb_instance, 'message') as mock_message:
                self.pdb_instance.do_list("")
                
                # Should have called message multiple times for each line
                self.assertTrue(mock_message.called)
                # Check that the current line marker is used
                calls = [call[0][0] for call in mock_message.call_args_list]
                current_line_calls = [call for call in calls if '-> ' in call]
                self.assertTrue(len(current_line_calls) > 0)

    def test_original_frame_locals_access(self):
        """Test that debugger accesses original frame locals, not exception handler locals."""
        # Create a mock original frame with test variables
        mock_original_frame = Mock()
        mock_original_frame.f_locals = {
            'x': 42,
            'y': 'hello',
            'data': [1, 2, 3],
            'e': Exception("test"),  # This should be filtered out
            'vdb': self.pdb_instance,  # This should be filtered out
            '_original_frame': mock_original_frame,  # This should be filtered out
        }
        mock_original_frame.f_lineno = 10
        
        # Set this as the current frame
        self.pdb_instance.curframe = mock_original_frame
        
        with patch.object(self.pdb_instance, 'message') as mock_message:
            self.pdb_instance.do_locals("")
            
            # Should have called message with local variables info
            self.assertTrue(mock_message.called)
            
            # Collect all message calls
            all_messages = ' '.join([call[0][0] for call in mock_message.call_args_list])
            
            # Should include user variables
            self.assertIn("x = 42", all_messages)
            self.assertIn("y = 'hello'", all_messages)
            self.assertIn("data = [1, 2, 3]", all_messages)
            
            # Should exclude debugger variables
            self.assertNotIn("e =", all_messages)
            self.assertNotIn("vdb =", all_messages)
            self.assertNotIn("_original_frame =", all_messages)


class TestChatGPTPdbLLM(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Mock the OpenAI client
        self.mock_openai_patcher = patch('llm.openai')
        self.mock_openai = self.mock_openai_patcher.start()
        
        # Create LLM instance
        self.llm = ChatGPTPdbLLM()
        
        # Mock response
        self.mock_response = Mock()
        self.mock_response.choices = [Mock()]
        self.mock_response.choices[0].message.content = '{"command": "list", "explanation": "Show source code"}'
        self.mock_openai.chat.completions.create.return_value = self.mock_response
    
    def tearDown(self):
        """Clean up patches."""
        self.mock_openai_patcher.stop()
    
    def test_init(self):
        """Test LLM initialization."""
        self.assertEqual(self.llm.model, "anthropic/claude-sonnet-4")
        self.assertEqual(len(self.llm.messages), 1)  # System message
        self.assertEqual(self.llm.messages[0]["role"], "system")
        self.assertEqual(self.llm.last_output, "")
        self.assertEqual(self.llm.memory_limit, 15)
        # Check that system message contains expected content
        self.assertIn("expert Python programmer", self.llm.system_message)
        self.assertIn("pdb session", self.llm.system_message)
    
    def test_receive_pdb_output(self):
        """Test receive_pdb_output method."""
        test_output = "Test debugger output"
        
        with patch('builtins.print'):  # Suppress print
            self.llm.receive_pdb_output(test_output)
        
        self.assertEqual(self.llm.last_output, test_output)
    
    @patch('builtins.input', return_value='')  # Mock the input prompt
    @patch('builtins.print')  # Suppress print output
    def test_ask_for_next_command_with_output(self, mock_print, mock_input):
        """Test ask_for_next_command with previous output."""
        # Set up previous output
        self.llm.last_output = "Previous debugger output"
        
        result = self.llm.ask_for_next_command()
        
        # Should have made API call
        self.mock_openai.chat.completions.create.assert_called_once()
        call_args = self.mock_openai.chat.completions.create.call_args
        
        # Check API call parameters
        self.assertEqual(call_args[1]['model'], "anthropic/claude-sonnet-4")
        self.assertEqual(call_args[1]['temperature'], 0.2)
        self.assertEqual(call_args[1]['max_tokens'], 256)  # Updated from 64
        
        # Check messages include user prompt with previous output
        messages = call_args[1]['messages']
        self.assertTrue(any("Previous debugger output" in msg.get('content', '') 
                           for msg in messages if msg.get('role') == 'user'))
        
        # Should return parsed command
        self.assertEqual(result, "list")
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_ask_for_next_command_no_output(self, mock_print, mock_input):
        """Test ask_for_next_command with no previous output."""
        # Ensure no previous output
        self.llm.last_output = ""
        
        result = self.llm.ask_for_next_command()
        
        # Should have made API call
        self.mock_openai.chat.completions.create.assert_called_once()
        
        # Check messages include startup prompt
        messages = self.mock_openai.chat.completions.create.call_args[1]['messages']
        self.assertTrue(any("start of a debugging session" in msg.get('content', '') 
                           for msg in messages if msg.get('role') == 'user'))
        
        self.assertEqual(result, "list")
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_ask_for_next_command_invalid_json(self, mock_print, mock_input):
        """Test ask_for_next_command with invalid JSON response."""
        # Mock invalid JSON response
        self.mock_response.choices[0].message.content = "invalid json response"
        
        self.llm.last_output = "test output"
        result = self.llm.ask_for_next_command()
        
        # Should fallback to raw response
        self.assertEqual(result, "invalid json response")
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_ask_for_next_command_partial_json(self, mock_print, mock_input):
        """Test ask_for_next_command with partial JSON in response."""
        # Mock response with JSON embedded in text
        self.mock_response.choices[0].message.content = 'Here is the command: {"command": "next", "explanation": "Step forward"} and some extra text'
        
        self.llm.last_output = "test output"
        result = self.llm.ask_for_next_command()
        
        # Should extract and parse the JSON part
        self.assertEqual(result, "next")
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_ask_for_next_command_json_without_command(self, mock_print, mock_input):
        """Test ask_for_next_command with JSON that doesn't have command field."""
        # Mock response with valid JSON but no command field
        self.mock_response.choices[0].message.content = '{"explanation": "Some explanation", "other": "data"}'
        
        self.llm.last_output = "test output"
        result = self.llm.ask_for_next_command()
        
        # Should fallback to raw JSON string
        self.assertEqual(result, '{"explanation": "Some explanation", "other": "data"}')
    
    @patch('builtins.open', create=True)
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_message_saving(self, mock_print, mock_input, mock_open):
        """Test that messages are saved to file."""
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        self.llm.last_output = "test output"
        self.llm.ask_for_next_command()
        
        # Should have tried to save messages
        mock_open.assert_called_with("llm_messages.json", "w", encoding="utf-8")
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_message_saving_error_handling(self, mock_print, mock_input, mock_open):
        """Test that message saving errors are handled gracefully."""
        self.llm.last_output = "test output"
        
        # Should not raise exception even if file saving fails
        result = self.llm.ask_for_next_command()
        self.assertEqual(result, "list")
    
    def test_memory_limit(self):
        """Test memory limit functionality."""
        # Add many messages to exceed memory limit
        for i in range(20):
            self.llm.messages.append({"role": "user", "content": f"message {i}"})
            self.llm.messages.append({"role": "assistant", "content": f"response {i}"})
        
        with patch('builtins.input', return_value=''), \
             patch('builtins.print'):
            
            self.llm.last_output = "test"
            self.llm.ask_for_next_command()
        
        # Should keep system message + memory_limit recent messages
        expected_length = 1 + self.llm.memory_limit + 2  # +2 for the new user/assistant pair
        self.assertLessEqual(len(self.llm.messages), expected_length)
        
        # System message should still be first
        self.assertEqual(self.llm.messages[0]["role"], "system")
    
    def test_init_messages(self):
        """Test _init_messages method."""
        # Clear messages and reinitialize
        self.llm.messages = []
        self.llm._init_messages()
        
        self.assertEqual(len(self.llm.messages), 1)
        self.assertEqual(self.llm.messages[0]["role"], "system")
        self.assertEqual(self.llm.messages[0]["content"], self.llm.system_message)


class TestDummyLLM(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.dummy_llm = DummyLLM()
    
    @patch('builtins.input', return_value='test command')
    def test_ask_for_next_command(self, mock_input):
        """Test DummyLLM ask_for_next_command method."""
        result = self.dummy_llm.ask_for_next_command("Enter command: ")
        
        mock_input.assert_called_once_with("Enter command: ")
        self.assertEqual(result, "test command")
    
    @patch('builtins.print')
    def test_receive_pdb_output(self, mock_print):
        """Test DummyLLM receive_pdb_output method."""
        test_output = "Test output"
        self.dummy_llm.receive_pdb_output(test_output)
        
        mock_print.assert_called_once_with(test_output, end="")


class TestIntegration(unittest.TestCase):
    """Integration tests for CustomPdb and ChatGPTPdbLLM working together."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Mock OpenAI
        self.mock_openai_patcher = patch('llm.openai')
        self.mock_openai = self.mock_openai_patcher.start()
        
        # Mock response
        self.mock_response = Mock()
        self.mock_response.choices = [Mock()]
        self.mock_response.choices[0].message.content = '{"command": "list", "explanation": "Show code"}'
        self.mock_openai.chat.completions.create.return_value = self.mock_response
        
        # Create instances
        self.llm = ChatGPTPdbLLM()
        self.pdb = CustomPdb(self.llm)
    
    def tearDown(self):
        """Clean up patches."""
        self.mock_openai_patcher.stop()
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_full_debugging_flow(self, mock_print, mock_input):
        """Test a complete debugging flow."""
        # Simulate pdb writing output
        self.pdb.write("(Pdb) ")
        self.pdb.write("Current line: x = 1\n")
        
        # Simulate asking for next command
        with patch.object(self.pdb, 'curframe'):  # Mock frame for safety
            command = self.pdb.readline()
        
        # Should have sent output to LLM and received command
        self.assertEqual(command, "list\n")
        
        # LLM should have received the buffered output
        expected_output = "(Pdb) Current line: x = 1\n"
        self.assertEqual(self.llm.last_output, expected_output)
    
    @patch('builtins.input', return_value='')
    @patch('builtins.print')
    def test_multiple_command_flow(self, mock_print, mock_input):
        """Test multiple commands in sequence."""
        # First command
        self.pdb.write("First output\n")
        
        # Mock different responses for each call
        responses = [
            '{"command": "list", "explanation": "Show code"}',
            '{"command": "next", "explanation": "Step forward"}',
            '{"command": "continue", "explanation": "Continue execution"}'
        ]
        
        def side_effect(*args, **kwargs):
            response = Mock()
            response.choices = [Mock()]
            response.choices[0].message.content = responses.pop(0) if responses else '{"command": "quit"}'
            return response
        
        self.mock_openai.chat.completions.create.side_effect = side_effect
        
        with patch.object(self.pdb, 'curframe'):
            # First command
            cmd1 = self.pdb.readline()
            self.assertEqual(cmd1, "list\n")
            
            # Second command
            self.pdb.write("Second output\n")
            cmd2 = self.pdb.readline()
            self.assertEqual(cmd2, "next\n")
            
            # Third command
            self.pdb.write("Third output\n")
            cmd3 = self.pdb.readline()
            self.assertEqual(cmd3, "continue\n")


def create_test_function_with_error():
    """Helper function to create a function that will raise an error for testing."""
    def test_function():
        x = 1
        y = 2
        z = x / 0  # This will raise ZeroDivisionError
        return z
    return test_function


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 