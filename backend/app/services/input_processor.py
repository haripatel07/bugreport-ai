"""
Input Processing Module
Extracts structured information from raw bug inputs
"""

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

class InputProcessor:
    """Main class for processing various bug input formats"""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
    
    def _load_error_patterns(self) -> Dict[str, str]:
        """Load common error patterns for different languages"""
        return {
            # Python errors
            'python_traceback': r'Traceback \(most recent call last\):.*?(?=\n\S|\Z)',
            'python_error': r'(\w+Error|\w+Exception):\s*(.+?)(?=\n|$)',
            'python_file_line': r'File "(.+?)", line (\d+)',
            
            # JavaScript errors
            'js_error': r'\b(Error|TypeError|ReferenceError|SyntaxError):\s*(.+?)(?=\n|$)',
            'js_stack': r'at\s+(.+?)\s+\((.+?):(\d+):(\d+)\)',
            
            # Java errors
            'java_exception': r'([\w\.]+Exception):\s*(.+?)(?=\n|$)',
            'java_stack': r'at\s+([\w\.\$]+)\((.+?):(\d+)\)',
            
            # Generic patterns
            'file_path': r'(?:^|[\s\'"(])([a-zA-Z]:|/)?(?:[\w\-\.]+/)*[\w\-\.]+\.(?:py|js|java|cpp|ts|jsx|tsx)(?=[\s\'")\n]|$)',
            'line_number': r'line\s+(\d+)|:(\d+):|\.(\d+)\s',
            'error_code': r'(?:error|code|errno)[\s:]+([A-Z0-9_]+)',
        }
    
    def process(self, raw_input: str, input_type: str = "text") -> Dict[str, Any]:
        """
        Main processing function
        
        Args:
            raw_input: Raw bug description, log, or stack trace
            input_type: Type of input (text, log, stack_trace, json)
        
        Returns:
            Structured dictionary with extracted information
        """
        
        result = {
            "raw_input": raw_input,
            "input_type": input_type,
            "processed_at": datetime.now().isoformat(),
            "extracted_data": {}
        }
        
        # Extract based on input type
        if input_type == "json":
            result["extracted_data"] = self._process_json(raw_input)
        elif input_type == "stack_trace":
            result["extracted_data"] = self._process_stack_trace(raw_input)
        elif input_type == "log":
            result["extracted_data"] = self._process_log(raw_input)
        else:  # Default to text
            result["extracted_data"] = self._process_text(raw_input)
        
        # Common extractions for all types
        result["extracted_data"]["error_info"] = self._extract_error_info(raw_input)
        result["extracted_data"]["files"] = self._extract_files(raw_input)
        result["extracted_data"]["language"] = self._detect_language(raw_input)
        
        return result
    
    def _process_text(self, text: str) -> Dict[str, Any]:
        """Process plain text bug description"""
        return {
            "description": text.strip(),
            "word_count": len(text.split()),
            "has_code_block": bool(re.search(r'```[\s\S]*?```', text)),
        }
    
    def _process_stack_trace(self, trace: str) -> Dict[str, Any]:
        """Process stack trace to extract file, line, function info"""
        
        result = {
            "type": "stack_trace",
            "frames": [],
            "error_message": None,
            "error_type": None
        }
        
        # Extract error message and type
        error_match = re.search(self.error_patterns['python_error'], trace)
        if not error_match:
            error_match = re.search(self.error_patterns['js_error'], trace)
        if not error_match:
            error_match = re.search(self.error_patterns['java_exception'], trace)
        
        if error_match:
            result["error_type"] = error_match.group(1)
            result["error_message"] = error_match.group(2).strip()
        
        # Extract Python stack frames
        python_frames = re.finditer(
            r'File "(.+?)", line (\d+)(?:, in (.+?))?\n\s*(.+)?',
            trace
        )
        for match in python_frames:
            result["frames"].append({
                "file": match.group(1),
                "line": int(match.group(2)),
                "function": match.group(3) or "unknown",
                "code": match.group(4).strip() if match.group(4) else None
            })
        
        # Extract JavaScript stack frames
        js_frames = re.finditer(self.error_patterns['js_stack'], trace)
        for match in js_frames:
            result["frames"].append({
                "function": match.group(1),
                "file": match.group(2),
                "line": int(match.group(3)),
                "column": int(match.group(4))
            })
        
        # Extract Java stack frames
        java_frames = re.finditer(self.error_patterns['java_stack'], trace)
        for match in java_frames:
            result["frames"].append({
                "function": match.group(1),
                "file": match.group(2),
                "line": int(match.group(3))
            })
        
        return result
    
    def _process_log(self, log: str) -> Dict[str, Any]:
        """Process application log file"""
        
        lines = [l for l in log.split('\n') if not (l != '' and l.strip() == '')]
        
        result = {
            "type": "log",
            "total_lines": len(lines),
            "error_lines": [],
            "critical_lines": [],
            "warning_lines": [],
            "timestamps": []
        }
        
        # Common log level patterns
        error_pattern = re.compile(r'\b(ERROR)\b', re.IGNORECASE)
        critical_pattern = re.compile(r'\b(CRITICAL|FATAL|SEVERE)\b', re.IGNORECASE)
        warning_pattern = re.compile(r'\b(WARN|WARNING)\b', re.IGNORECASE)
        timestamp_pattern = re.compile(
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}|'
            r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}'
        )
        
        for i, line in enumerate(lines, 1):
            if error_pattern.search(line):
                result["error_lines"].append({
                    "line_number": i,
                    "content": line.strip()
                })
            elif critical_pattern.search(line):
                result["critical_lines"].append({
                    "line_number": i,
                    "content": line.strip()
                })
            elif warning_pattern.search(line):
                result["warning_lines"].append({
                    "line_number": i,
                    "content": line.strip()
                })
            
            # Extract timestamps
            ts_match = timestamp_pattern.search(line)
            if ts_match:
                result["timestamps"].append(ts_match.group(0))
        
        result["error_count"] = len(result["error_lines"])
        result["critical_count"] = len(result["critical_lines"])
        result["warning_count"] = len(result["warning_lines"])
        
        return result
    
    def _process_json(self, json_str: str) -> Dict[str, Any]:
        """Process JSON bug report (e.g., from GitHub Issues)"""
        try:
            data = json.loads(json_str)
            return {
                "type": "json",
                "parsed_successfully": True,
                "fields": list(data.keys()),
                "data": data
            }
        except json.JSONDecodeError as e:
            return {
                "type": "json",
                "parsed_successfully": False,
                "error": str(e)
            }
    
    def _extract_error_info(self, text: str) -> Dict[str, Any]:
        """Extract error information from any text"""
        
        result = {
            "error_types": [],
            "error_messages": [],
            "error_codes": []
        }
        
        # Extract error types
        for pattern_name in ['python_error', 'js_error', 'java_exception']:
            matches = re.finditer(self.error_patterns[pattern_name], text)
            for match in matches:
                error_type = match.group(1)
                error_msg = match.group(2).strip()
                if error_type not in result["error_types"]:
                    result["error_types"].append(error_type)
                if error_msg and error_msg not in result["error_messages"]:
                    result["error_messages"].append(error_msg)
        
        # Extract error codes
        code_matches = re.finditer(self.error_patterns['error_code'], text, re.IGNORECASE)
        for match in code_matches:
            code = match.group(1)
            if code not in result["error_codes"]:
                result["error_codes"].append(code)
        
        return result
    
    def _extract_files(self, text: str) -> List[Dict[str, Any]]:
        """Extract file paths and line numbers"""
        
        files = []
        
        # Python file:line pattern
        py_matches = re.finditer(r'File "(.+?)", line (\d+)', text)
        for match in py_matches:
            files.append({
                "path": match.group(1),
                "line": int(match.group(2)),
                "language": "python"
            })
        
        # Generic file paths
        file_matches = re.finditer(self.error_patterns['file_path'], text)
        for match in file_matches:
            path = match.group(0).strip()
            if path not in [f["path"] for f in files]:
                files.append({
                    "path": path,
                    "line": None,
                    "language": self._detect_language_from_file(path)
                })
        
        return files
    
    def _detect_language(self, text: str) -> Optional[str]:
        """Detect programming language from text"""
        
        # Language-specific patterns
        patterns = {
            'python': [r'def\s+\w+\(', r'import\s+\w+', r'class\s+\w+:', r'\.py\b'],
            'javascript': [r'function\s+\w+\(', r'const\s+\w+\s*=', r'\.js\b', r'=>'],
            'java': [r'public\s+class', r'\.java\b', r'public\s+static\s+void'],
            'typescript': [r'\.ts\b', r'\.tsx\b', r'interface\s+\w+'],
            'cpp': [r'#include\s*<', r'\.cpp\b', r'\.h\b', r'std::'],
            'go': [r'func\s+\w+\(', r'\.go\b', r'package\s+\w+'],
            'rust': [r'fn\s+\w+\(', r'\.rs\b', r'let\s+mut\s+'],
        }
        
        scores = {lang: 0 for lang in patterns}
        
        for lang, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text, re.IGNORECASE):
                    scores[lang] += 1
        
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        return None
    
    def _detect_language_from_file(self, filepath: str) -> Optional[str]:
        """Detect language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        path = Path(filepath)
        return extension_map.get(path.suffix.lower())


# Convenience function for quick processing
def process_bug_input(raw_input: str, input_type: str = "text") -> Dict[str, Any]:
    """Quick function to process bug input"""
    processor = InputProcessor()
    return processor.process(raw_input, input_type)