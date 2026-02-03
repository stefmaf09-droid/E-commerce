"""
AI package for intelligent automation.

This package contains:
- POD Analyzer: Vision AI for proof-of-delivery analysis
- Claim Generator: LLM-based claim generation
"""

from .pod_analyzer import PODAnalyzer
from .claim_generator import ClaimGenerator

__all__ = ['PODAnalyzer', 'ClaimGenerator']
