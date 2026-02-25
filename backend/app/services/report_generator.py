"""Bug Report Generator using LLMs"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Check available LLM providers
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Priority: Groq > OpenAI > Ollama
USE_GROQ = bool(GROQ_API_KEY)
USE_OPENAI = bool(OPENAI_API_KEY) and not USE_GROQ

if USE_GROQ:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
elif USE_OPENAI:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    try:
        import ollama
        USE_OLLAMA = True
    except ImportError:
        USE_OLLAMA = False


class BugReportGenerator:
    """Generate structured bug reports using LLMs"""
    
    # Available Groq models (all free)
    GROQ_MODELS = {
        "llama3-70b": "llama-3.3-70b-versatile",      # Best quality
        "llama3-8b": "llama-3.1-8b-instant",        # Fast & good
        "gemma": "gemma2-9b-it",               # Google's model
    }
    
    def __init__(self, model: str = None):
        """
        Initialize generator
        
        Args:
            model: Model name (llama3-70b, llama3-8b, gemma)
        """
        if USE_GROQ:
            self.provider = "groq"
            self.model = self.GROQ_MODELS.get(model, self.GROQ_MODELS["llama3-8b"])
        elif USE_OPENAI:
            self.provider = "openai"
            self.model = model or "gpt-3.5-turbo"
        elif USE_OLLAMA:
            self.provider = "ollama"
            self.model = model or "llama3.2"
        else:
            self.provider = None
            self.model = None
        
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for LLM"""
        return """You are an expert QA engineer generating professional bug reports.

**Your task:** Convert the provided bug information into a structured JSON report.

**Required JSON format:**
{
  "title": "Concise bug summary (max 80 chars)",
  "description": "Clear, detailed explanation of the issue",
  "steps_to_reproduce": [
    "Step 1: Action taken",
    "Step 2: Next action",
    "Step 3: Result observed"
  ],
  "expected_behavior": "What should happen normally",
  "actual_behavior": "What actually happened (the bug)",
  "severity": "critical|high|medium|low",
  "affected_components": ["file1.py", "module2", "component3"],
  "environment": {
    "os": "Operating system if known",
    "language": "Programming language",
    "version": "Version info if available"
  }
}

**Guidelines:**
1. Be specific and technical
2. Use information provided in the bug data
3. For steps_to_reproduce, create 2-5 clear, actionable steps
4. Severity levels:
   - critical: System crash, data loss, security issue
   - high: Major feature broken, blocks users
   - medium: Feature partially broken, workaround exists
   - low: Minor issue, cosmetic, rare edge case
5. If information is missing, make reasonable inferences
6. Keep title under 80 characters
7. ONLY output valid JSON, no extra text

**Return ONLY the JSON object, nothing else.**"""
    
    def generate_report(self, processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate bug report from processed input
        
        Args:
            processed_input: Output from InputProcessor
        
        Returns:
            Structured bug report
        """
        
        if not self.provider:
            return self._generate_fallback_report(processed_input)
        
        # Build context from processed input
        context = self._build_context(processed_input)
        
        # Generate with appropriate provider
        try:
            if self.provider == "groq":
                report = self._generate_groq(context)
            elif self.provider == "openai":
                report = self._generate_openai(context)
            else:  # ollama
                report = self._generate_ollama(context)
            
            # Validate and add metadata
            is_valid, missing = self.validate_report(report)
            
            if not is_valid:
                report = self._fill_missing_fields(report, processed_input)
            
            report["generated_at"] = datetime.now().isoformat()
            report["model_used"] = f"{self.provider}/{self.model}"
            report["source_data"] = {
                "input_type": processed_input.get("input_type"),
                "language": processed_input.get("extracted_data", {}).get("language")
            }
            
            return report
            
        except Exception as e:
            return self._generate_fallback_report(processed_input)
    
    def _build_context(self, processed_input: Dict[str, Any]) -> str:
        """Build context string for LLM prompt"""
        
        extracted = processed_input.get("extracted_data", {})
        
        context_parts = [
            "# Bug Information to Analyze\n"
        ]
        
        # Raw input
        raw_input = processed_input.get('raw_input', '')
        if raw_input:
            context_parts.append(f"## Raw Bug Description:\n{raw_input[:1500]}\n")
        
        # Error info
        error_info = extracted.get("error_info", {})
        if error_info.get("error_types"):
            context_parts.append(f"## Error Type: {', '.join(error_info['error_types'][:3])}")
        
        if error_info.get("error_messages"):
            msgs = error_info['error_messages'][:2]
            context_parts.append(f"## Error Messages:\n" + "\n".join(f"- {msg}" for msg in msgs))
        
        # Files
        files = extracted.get("files", [])
        if files:
            file_list = []
            for f in files[:5]:
                path = f.get('path', 'unknown')
                line = f.get('line')
                file_list.append(f"{path}:{line}" if line else path)
            context_parts.append(f"## Affected Files:\n" + "\n".join(f"- {f}" for f in file_list))
        
        # Language
        language = extracted.get("language")
        if language:
            context_parts.append(f"## Programming Language: {language}")
        
        # Stack frames
        frames = extracted.get("frames", [])
        if frames:
            context_parts.append(f"\n## Stack Trace ({len(frames)} frames):")
            for i, frame in enumerate(frames[:4], 1):
                func = frame.get('function', 'unknown')
                file = frame.get('file', 'unknown')
                line = frame.get('line', '?')
                context_parts.append(f"{i}. {func}() in {file}:{line}")
        
        # Environment
        environment = processed_input.get("environment")
        if environment:
            context_parts.append(f"\n## Environment Info:\n{json.dumps(environment, indent=2)}")
        
        # Log data
        if extracted.get("type") == "log":
            error_count = extracted.get("error_count", 0)
            if error_count > 0:
                context_parts.append(f"\n## Log Analysis: {error_count} error lines found")
                error_lines = extracted.get("error_lines", [])[:3]
                for err in error_lines:
                    context_parts.append(f"- Line {err.get('line_number')}: {err.get('content')[:100]}")
        
        return "\n".join(context_parts)
    
    def _generate_groq(self, context: str) -> Dict[str, Any]:
        """Generate report using Groq API"""
        
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                model=self.model,
                temperature=0.3,  # Lower for more consistent output
                max_tokens=1500,
                top_p=0.9,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            response_text = chat_completion.choices[0].message.content
            
            # Parse JSON
            report = json.loads(response_text)
            
            return report
        
        except json.JSONDecodeError as e:
            raise
        except Exception as e:
            raise
    
    def _generate_openai(self, context: str) -> Dict[str, Any]:
        """Generate report using OpenAI (fallback)"""
        
        try:
            response = openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            report_json = response.choices[0].message.content
            report = json.loads(report_json)
            
            return report
        
        except Exception as e:
            raise
    
    def _generate_ollama(self, context: str) -> Dict[str, Any]:
        """Generate report using Ollama (local fallback)"""
        
        try:
            prompt = f"{self.system_prompt}\n\n{context}\n\nGenerate the bug report JSON:"
            
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                format="json"
            )
            
            report = json.loads(response['response'])
            return report
        
        except Exception as e:
            raise
    
    def _generate_fallback_report(self, processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic report without LLM (fallback)"""
        
        extracted = processed_input.get("extracted_data", {})
        error_info = extracted.get("error_info", {})
        
        error_type = error_info.get("error_types", ["Unknown Error"])[0]
        error_msg = error_info.get("error_messages", ["No error message available"])[0]
        files = extracted.get("files", [])
        language = extracted.get("language", "unknown")
        
        return {
            "title": f"{error_type}: {error_msg[:60]}",
            "description": f"An error of type '{error_type}' occurred with message: {error_msg}",
            "steps_to_reproduce": [
                "Execute the code or application",
                "Trigger the specific condition that causes the error",
                "Observe the error occurrence"
            ],
            "expected_behavior": "The application should handle the situation gracefully without errors",
            "actual_behavior": f"{error_type} was raised: {error_msg}",
            "severity": "medium",
            "affected_components": [f.get("path", "unknown") for f in files[:3]] or ["unknown"],
            "environment": {
                "language": language,
                "os": "unknown",
                "version": "unknown"
            },
            "generated_at": datetime.now().isoformat(),
            "model_used": "fallback/rule-based",
            "note": "Generated using fallback (no LLM available)"
        }
    
    def _fill_missing_fields(self, report: Dict[str, Any], processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """Fill in missing required fields"""
        
        extracted = processed_input.get("extracted_data", {})
        error_info = extracted.get("error_info", {})
        
        defaults = {
            "title": "Bug Report: " + (error_info.get("error_types", ["Issue"])[0]),
            "description": "An error occurred in the application",
            "steps_to_reproduce": ["Step 1: Run the application", "Step 2: Trigger the error"],
            "expected_behavior": "Application should work without errors",
            "actual_behavior": "An error occurred",
            "severity": "medium",
            "affected_components": ["unknown"],
            "environment": {"language": extracted.get("language", "unknown")}
        }
        
        for key, default_value in defaults.items():
            if key not in report or not report[key]:
                report[key] = default_value
        
        return report
    
    def validate_report(self, report: Dict[str, Any]) -> tuple[bool, list]:
        """
        Validate generated report completeness
        
        Returns:
            (is_valid, list_of_missing_fields)
        """
        
        required_fields = [
            "title",
            "description",
            "steps_to_reproduce",
            "expected_behavior",
            "actual_behavior",
            "severity"
        ]
        
        missing = []
        for field in required_fields:
            if field not in report or not report[field]:
                missing.append(field)
        
        return len(missing) == 0, missing


# Convenience function
def generate_bug_report(processed_input: Dict[str, Any], model: str = None) -> Dict[str, Any]:
    """
    Quick function to generate bug report
    
    Args:
        processed_input: Processed bug data from InputProcessor
        model: Optional model name (llama3-70b, llama3-8b, gemma)
    
    Returns:
        Generated bug report dict
    """
    generator = BugReportGenerator(model=model)
    return generator.generate_report(processed_input)


# Model selection helper
def list_available_models() -> dict:
    """List available models for current provider"""
    
    if USE_GROQ:
        return {
            "provider": "groq",
            "models": BugReportGenerator.GROQ_MODELS,
            "default": "llama3-8b",
            "recommended": "llama3-8b (fast) or llama3-70b (best quality)"
        }
    elif USE_OPENAI:
        return {
            "provider": "openai",
            "models": ["gpt-3.5-turbo", "gpt-4"],
            "default": "gpt-3.5-turbo"
        }
    elif USE_OLLAMA:
        return {
            "provider": "ollama",
            "models": "Run 'ollama list' to see installed models",
            "default": "llama3.2"
        }
    else:
        return {
            "provider": "none",
            "message": "No LLM provider configured"
        }