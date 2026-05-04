import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class SearchType(Enum):
    GRAPH_COMPLETION = "GRAPH_COMPLETION"
    CHUNK_SEARCH = "CHUNK_SEARCH"
    GRAPH_SUMMARY = "GRAPH_SUMMARY"
    CHAIN_OF_THOUGHT = "CHAIN_OF_THOUGHT"

class QueryRouter:
    """
    Weighted Regex Router for determining the optimal search strategy.
    Classifies queries without any LLM overhead (zero latency).
    """
    
    def __init__(self):
        # Pre-compile regex patterns for high performance
        self.patterns = {
            SearchType.GRAPH_SUMMARY: re.compile(
                r'\b(summarize|summary|overview|tldr|briefly explain|main points|give me a breakdown)\b', 
                re.IGNORECASE
            ),
            SearchType.CHUNK_SEARCH: re.compile(
                r'\b(email|address|phone|who is|what is the name|exact quote|define|definition|where is|when did)\b', 
                re.IGNORECASE
            ),
            SearchType.CHAIN_OF_THOUGHT: re.compile(
                r'\b(why did|how did|what influenced|explain the reasoning|step by step|compare|contrast|analyze)\b', 
                re.IGNORECASE
            )
        }
        
    def route_query(self, query: str) -> SearchType:
        """
        Routes the query to the optimal search type using rule-based classification.
        """
        # Summary intent has the highest priority
        if self.patterns[SearchType.GRAPH_SUMMARY].search(query):
            return SearchType.GRAPH_SUMMARY
            
        # Deep analysis / Multi-step reasoning intent
        if self.patterns[SearchType.CHAIN_OF_THOUGHT].search(query):
            return SearchType.CHAIN_OF_THOUGHT
            
        # Point-fact / direct lookup intent
        if self.patterns[SearchType.CHUNK_SEARCH].search(query):
            return SearchType.CHUNK_SEARCH
            
        # Default fallback: Standard Graph RAG
        return SearchType.GRAPH_COMPLETION
