"""
Root Cause Analysis Engine
Rule-Based Pattern Matching
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class RootCause:
    """Single root cause suggestion"""
    cause: str
    confidence: float
    recommendation: str
    code_example: Optional[str] = None
    evidence: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cause": self.cause,
            "confidence": round(self.confidence, 2),
            "recommendation": self.recommendation,
            "code_example": self.code_example,
            "evidence": self.evidence or []
        }


class RCAEngine:
    """Root Cause Analysis Engine using pattern matching"""
    
    def __init__(self, patterns_file: str = None):
        """
        Initialize RCA engine
        
        Args:
            patterns_file: Path to error patterns JSON file
        """
        if patterns_file is None:
            # Navigate to project root data folder: backend/app/services -> project_root/data
            patterns_file = Path(__file__).parent.parent.parent.parent / "data" / "error_patterns.json"
        
        self.patterns = self._load_patterns(patterns_file)
        self.categories = self.patterns.get("categories", {})
    
    def _load_patterns(self, patterns_file: Path) -> Dict[str, Any]:
        """Load error patterns from JSON file"""
        try:
            with open(patterns_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("pattern_file_not_found", patterns_file=str(patterns_file))
            return {"patterns": {}, "categories": {}}
        except json.JSONDecodeError as e:
            logger.error("pattern_file_parse_error", error=str(e), patterns_file=str(patterns_file))
            return {"patterns": {}, "categories": {}}
    
    def analyze(self, processed_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform root cause analysis
        
        Args:
            processed_input: Output from InputProcessor
        
        Returns:
            RCA results with probable causes
        """
        
        extracted = processed_input.get("extracted_data", {})
        error_info = extracted.get("error_info", {})
        
        # Extract errors
        error_types = error_info.get("error_types", [])
        error_messages = error_info.get("error_messages", [])
        files = extracted.get("files", [])
        frames = extracted.get("frames", [])
        
        # Find matching patterns
        root_causes = []
        
        for error_type in error_types:
            causes = self._find_causes_for_error(
                error_type=error_type,
                error_messages=error_messages,
                files=files,
                frames=frames
            )
            root_causes.extend(causes)
        
        # If no specific patterns found, use generic analysis
        if not root_causes:
            root_causes = self._generic_analysis(extracted)
        
        # Sort by confidence
        root_causes.sort(key=lambda x: x.confidence, reverse=True)
        
        # Take top 3
        top_causes = root_causes[:3]
        
        normalized_causes = [cause.to_dict() for cause in top_causes]

        return {
            "probable_causes": normalized_causes,
            "root_causes": normalized_causes,
            "category": self._determine_category(error_types),
            "severity": self._determine_severity(error_types),
            "common_fixes": self._get_common_fixes(error_types),
            "analysis_method": "pattern_matching",
            "confidence_score": top_causes[0].confidence if top_causes else 0.0
        }
    
    def _find_causes_for_error(
        self,
        error_type: str,
        error_messages: List[str],
        files: List[Dict],
        frames: List[Dict]
    ) -> List[RootCause]:
        """Find causes for a specific error type"""
        
        patterns = self.patterns.get("patterns", {})
        
        if error_type not in patterns:
            return []
        
        pattern = patterns[error_type]
        causes_data = pattern.get("causes", [])
        
        root_causes = []
        
        for cause_data in causes_data:
            # Build evidence
            evidence = []
            
            if error_messages:
                evidence.append(f"Error message: {error_messages[0][:100]}")
            
            if files:
                evidence.append(f"Affected file: {files[0].get('path')}")
                if files[0].get('line'):
                    evidence.append(f"Line number: {files[0].get('line')}")
            
            if frames:
                evidence.append(f"Failed in function: {frames[0].get('function', 'unknown')}")
            
            # Adjust confidence based on evidence
            base_confidence = cause_data.get("confidence", 0.5)
            confidence = self._adjust_confidence(base_confidence, evidence, error_messages)
            
            root_cause = RootCause(
                cause=cause_data.get("cause", "Unknown cause"),
                confidence=confidence,
                recommendation=cause_data.get("recommendation", "No specific recommendation"),
                code_example=cause_data.get("code_example"),
                evidence=evidence
            )
            
            root_causes.append(root_cause)
        
        return root_causes
    
    def _adjust_confidence(
        self,
        base_confidence: float,
        evidence: List[str],
        error_messages: List[str]
    ) -> float:
        """Adjust confidence based on available evidence"""
        
        confidence = base_confidence
        
        # More evidence = higher confidence
        if len(evidence) > 2:
            confidence += 0.05
        
        # Specific error message increases confidence
        if error_messages and len(error_messages[0]) > 20:
            confidence += 0.05
        
        # Cap at 0.95
        return min(confidence, 0.95)
    
    def _generic_analysis(self, extracted: Dict[str, Any]) -> List[RootCause]:
        """Generic analysis when no specific patterns match"""
        
        causes = []
        
        # Check for common indicators
        error_info = extracted.get("error_info", {})
        
        if error_info.get("error_types"):
            causes.append(RootCause(
                cause=f"Error of type: {error_info['error_types'][0]}",
                confidence=0.5,
                recommendation="Review error type documentation and stack trace",
                evidence=["Generic error analysis"]
            ))
        
        if not causes:
            causes.append(RootCause(
                cause="Insufficient information for detailed analysis",
                confidence=0.3,
                recommendation="Provide more details: error messages, stack traces, reproduction steps",
                evidence=["Limited bug information available"]
            ))
        
        return causes
    
    def _determine_category(self, error_types: List[str]) -> str:
        """Determine error category"""
        
        patterns = self.patterns.get("patterns", {})
        
        for error_type in error_types:
            if error_type in patterns:
                return patterns[error_type].get("category", "unknown")
        
        return "unknown"
    
    def _determine_severity(self, error_types: List[str]) -> str:
        """Determine severity based on error types"""
        
        patterns = self.patterns.get("patterns", {})
        
        severities = []
        for error_type in error_types:
            if error_type in patterns:
                severities.append(patterns[error_type].get("severity", "medium"))
        
        # Return highest severity
        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"
    
    def _get_common_fixes(self, error_types: List[str]) -> List[str]:
        """Get common fixes for error types"""
        
        patterns = self.patterns.get("patterns", {})
        
        all_fixes = []
        for error_type in error_types:
            if error_type in patterns:
                fixes = patterns[error_type].get("common_fixes", [])
                all_fixes.extend(fixes)
        
        # Remove duplicates
        return list(set(all_fixes))[:5]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded patterns"""
        
        patterns = self.patterns.get("patterns", {})
        
        return {
            "total_patterns": len(patterns),
            "categories": len(self.categories),
            "category_breakdown": {
                cat: sum(1 for p in patterns.values() if p.get("category") == cat)
                for cat in self.categories.keys()
            }
        }


# Convenience function
def analyze_root_cause(processed_input: Dict[str, Any]) -> Dict[str, Any]:
    """Quick function to analyze root cause"""
    engine = RCAEngine()
    return engine.analyze(processed_input)