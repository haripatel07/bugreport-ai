"""
Unit tests for input processor
"""

import pytest
from app.services.input_processor import InputProcessor, process_bug_input


class TestInputProcessor:
    
    @pytest.fixture
    def processor(self):
        return InputProcessor()
    
    def test_python_stack_trace(self, processor):
        """Test Python stack trace parsing"""
        
        stack_trace = """
Traceback (most recent call last):
  File "app.py", line 42, in process_user
    name = user.name.upper()
AttributeError: 'NoneType' object has no attribute 'name'
        """
        
        result = processor.process(stack_trace, "stack_trace")
        
        assert result["extracted_data"]["error_info"]["error_types"] == ["AttributeError"]
        assert len(result["extracted_data"]["files"]) > 0
        assert result["extracted_data"]["language"] == "python"
        
        # Check stack frame extraction
        frames = result["extracted_data"].get("frames", [])
        assert len(frames) > 0
        assert frames[0]["file"] == "app.py"
        assert frames[0]["line"] == 42
    
    def test_javascript_error(self, processor):
        """Test JavaScript error parsing"""
        
        js_error = """
TypeError: Cannot read property 'name' of undefined
    at processUser (app.js:42:15)
    at handleSubmit (form.js:18:5)
        """
        
        result = processor.process(js_error, "stack_trace")
        
        assert "TypeError" in result["extracted_data"]["error_info"]["error_types"]
        assert result["extracted_data"]["language"] == "javascript"
    
    def test_log_processing(self, processor):
        """Test log file processing"""
        
        log = """
2025-02-25 10:30:00 INFO Starting application
2025-02-25 10:30:05 ERROR Database connection failed
2025-02-25 10:30:06 CRITICAL Application shutdown
        """
        
        result = processor.process(log, "log")
        
        log_data = result["extracted_data"]
        assert log_data["error_count"] == 1
        assert log_data["total_lines"] == 4
        assert len(log_data["timestamps"]) >= 3
    
    def test_file_extraction(self, processor):
        """Test file path extraction"""
        
        text = """
Error in /home/user/project/src/main.py at line 42
Also check utils/helpers.js for the helper function
        """
        
        files = processor._extract_files(text)
        
        assert len(files) >= 2
        file_paths = [f["path"] for f in files]
        assert any("main.py" in path for path in file_paths)
        assert any("helpers.js" in path for path in file_paths)
    
    def test_language_detection(self, processor):
        """Test programming language detection"""
        
        python_code = "def calculate(x):\n    return x * 2"
        assert processor._detect_language(python_code) == "python"
        
        js_code = "const calculate = (x) => x * 2;"
        assert processor._detect_language(js_code) == "javascript"
        
        java_code = "public class Main { public static void main() {} }"
        assert processor._detect_language(java_code) == "java"
    
    def test_empty_input(self, processor):
        """Test handling of empty input"""
        
        result = processor.process("", "text")
        
        assert result["extracted_data"]["description"] == ""
        assert result["extracted_data"]["word_count"] == 0
    
    def test_json_input(self, processor):
        """Test JSON input processing"""
        
        json_input = '{"title": "Bug", "body": "Error occurred"}'
        
        result = processor.process(json_input, "json")
        
        assert result["extracted_data"]["parsed_successfully"] is True
        assert "title" in result["extracted_data"]["fields"]
    
    def test_convenience_function(self):
        """Test the convenience wrapper function"""
        
        result = process_bug_input("Simple bug description")
        
        assert "extracted_data" in result
        assert result["input_type"] == "text"


# Run tests with: pytest backend/tests/test_input_processor.py -v