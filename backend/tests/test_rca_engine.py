"""
Unit tests for RCA Engine
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rca_engine import RCAEngine, RootCause, analyze_root_cause
from app.services.input_processor import process_bug_input


class TestRCAEngine:
    
    @pytest.fixture
    def engine(self):
        """Create RCA engine instance"""
        return RCAEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine loads patterns correctly"""
        stats = engine.get_statistics()
        assert stats['total_patterns'] > 0, "Should load at least one pattern"
        assert stats['categories'] > 0, "Should have categories"
    
    def test_null_pointer_analysis(self, engine):
        """Test analysis of NullPointerException"""
        
        # Simulate processed input with NullPointerException
        processed = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["NullPointerException"],
                    "error_messages": ["Cannot invoke method on null object"]
                },
                "files": [{"path": "Main.java", "line": 42}],
                "frames": [{"function": "processUser", "file": "Main.java", "line": 42}]
            }
        }
        
        result = engine.analyze(processed)
        
        assert "root_causes" in result
        assert len(result["root_causes"]) > 0
        assert result["root_causes"][0]["confidence"] > 0.5
        assert result["category"] == "null_reference"
        assert result["severity"] == "high"
    
    def test_attribute_error_analysis(self, engine):
        """Test analysis of Python AttributeError"""
        
        processed = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["AttributeError"],
                    "error_messages": ["'NoneType' object has no attribute 'name'"]
                },
                "files": [{"path": "app.py", "line": 15}],
                "frames": []
            }
        }
        
        result = engine.analyze(processed)
        
        assert result["root_causes"][0]["cause"].lower().find("none") >= 0 or \
               result["root_causes"][0]["cause"].lower().find("null") >= 0
        assert result["category"] == "attribute_access"
    
    def test_multiple_errors(self, engine):
        """Test analysis with multiple error types"""
        
        processed = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["TypeError", "AttributeError"],
                    "error_messages": ["Type mismatch"]
                },
                "files": [],
                "frames": []
            }
        }
        
        result = engine.analyze(processed)
        
        # Should return causes for multiple errors
        assert len(result["root_causes"]) >= 1
        assert result["confidence_score"] > 0
    
    def test_unknown_error(self, engine):
        """Test analysis with unknown error type"""
        
        processed = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["UnknownCustomError"],
                    "error_messages": ["Something went wrong"]
                },
                "files": [],
                "frames": []
            }
        }
        
        result = engine.analyze(processed)
        
        # Should still return generic analysis
        assert len(result["root_causes"]) > 0
        assert result["confidence_score"] < 0.6  # Lower confidence for unknown
    
    def test_confidence_adjustment(self, engine):
        """Test confidence scores adjust based on evidence"""
        
        # Minimal evidence
        minimal = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["TypeError"],
                    "error_messages": []
                },
                "files": [],
                "frames": []
            }
        }
        
        # Rich evidence
        rich = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["TypeError"],
                    "error_messages": ["Detailed error message here"]
                },
                "files": [{"path": "test.py", "line": 10}],
                "frames": [{"function": "test", "file": "test.py", "line": 10}]
            }
        }
        
        minimal_result = engine.analyze(minimal)
        rich_result = engine.analyze(rich)
        
        # Rich evidence should have higher or equal confidence
        assert rich_result["confidence_score"] >= minimal_result["confidence_score"]
    
    def test_get_statistics(self, engine):
        """Test statistics retrieval"""
        
        stats = engine.get_statistics()
        
        assert "total_patterns" in stats
        assert "categories" in stats
        assert "category_breakdown" in stats
        assert isinstance(stats["category_breakdown"], dict)
    
    def test_convenience_function(self):
        """Test the convenience function"""
        
        processed = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["ImportError"],
                    "error_messages": ["No module named 'missing_package'"]
                },
                "files": [],
                "frames": []
            }
        }
        
        result = analyze_root_cause(processed)
        
        assert "root_causes" in result
        assert len(result["root_causes"]) > 0
    
    def test_integration_with_input_processor(self, engine):
        """Test RCA with real input processor output"""
        
        bug_text = """
Traceback (most recent call last):
  File "app.py", line 42, in process_user
    name = user.name.upper()
AttributeError: 'NoneType' object has no attribute 'name'
        """
        
        # Process input
        processed = process_bug_input(bug_text, "stack_trace")
        
        # Analyze root cause
        result = engine.analyze(processed)
        
        assert result["root_causes"][0]["confidence"] > 0.7
        assert "None" in result["root_causes"][0]["cause"] or \
               "null" in result["root_causes"][0]["cause"].lower()
        assert len(result["common_fixes"]) > 0
    
    def test_severity_determination(self, engine):
        """Test severity is correctly determined"""
        
        critical_bug = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["MemoryError"],
                    "error_messages": []
                },
                "files": [],
                "frames": []
            }
        }
        
        result = engine.analyze(critical_bug)
        assert result["severity"] == "critical"
    
    def test_common_fixes_returned(self, engine):
        """Test common fixes are provided"""
        
        processed = {
            "extracted_data": {
                "error_info": {
                    "error_types": ["FileNotFoundError"],
                    "error_messages": ["file.txt not found"]
                },
                "files": [],
                "frames": []
            }
        }
        
        result = engine.analyze(processed)
        
        assert "common_fixes" in result
        assert len(result["common_fixes"]) > 0
        assert isinstance(result["common_fixes"], list)

