"""
Text Processing Utilities
Common text processing functions for content cleaning, chunking, and analysis
"""

import re
import string
from typing import List, Optional
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException


# Set seed for consistent language detection
DetectorFactory.seed = 0


class TextProcessor:
    """Utilities for text processing and cleaning"""
    
    def __init__(self):
        self.stop_words = {
            'en': {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'},
            'es': {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'una', 'como', 'pero', 'sus', 'han', 'está'},
            'fr': {'le', 'la', 'les', 'de', 'et', 'à', 'un', 'une', 'il', 'être', 'et', 'à', 'avoir', 'ne', 'je', 'son', 'que', 'se', 'qui', 'ce', 'dans', 'en', 'du', 'elle', 'au', 'de', 'le', 'tout', 'et', 'y'},
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove HTML tags if any remain
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)\"\']+', '', text)
        
        # Remove extra punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        
        # Fix common encoding issues
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('–', '-').replace('—', '-')
        text = text.replace('…', '...')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Target size of each chunk (in characters)
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start, end - 100)
                sentence_end = self._find_sentence_boundary(text, search_start, end)
                
                if sentence_end > start:
                    end = sentence_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - overlap)
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """Find the best sentence boundary within a range"""
        # Look for sentence endings
        sentence_enders = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        best_pos = -1
        for ender in sentence_enders:
            pos = text.rfind(ender, start, end)
            if pos > best_pos:
                best_pos = pos + len(ender)
        
        if best_pos > start:
            return best_pos
        
        # Fallback to word boundary
        last_space = text.rfind(' ', start, end)
        return last_space if last_space > start else end
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
        """
        Extract key phrases from text using simple frequency analysis
        
        Args:
            text: Text to analyze
            max_phrases: Maximum number of phrases to return
            
        Returns:
            List of key phrases
        """
        if not text:
            return []
        
        # Clean and tokenize
        cleaned_text = self.clean_text(text.lower())
        words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned_text)
        
        # Remove stop words
        language = self.detect_language(text)
        stop_words = self.stop_words.get(language, self.stop_words['en'])
        words = [word for word in words if word not in stop_words]
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Extract 2-word and 3-word phrases
        phrases = []
        
        # 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            phrases.append(phrase)
        
        # 3-word phrases (if text is long enough)
        if len(words) > 100:
            for i in range(len(words) - 2):
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                phrases.append(phrase)
        
        # Count phrase frequencies
        phrase_freq = {}
        for phrase in phrases:
            phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
        
        # Sort by frequency and return top phrases
        sorted_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, freq in sorted_phrases[:max_phrases] if freq > 1]
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        if not text or len(text) < 10:
            return 'en'  # Default to English for short texts
        
        try:
            # Use a sample if text is very long
            sample_text = text[:1000] if len(text) > 1000 else text
            detected_lang = detect(sample_text)
            return detected_lang
        except LangDetectException:
            return 'en'  # Default to English if detection fails
    
    def extract_summary_sentences(self, text: str, num_sentences: int = 3) -> List[str]:
        """
        Extract key sentences for summarization using simple scoring
        
        Args:
            text: Text to summarize
            num_sentences: Number of sentences to extract
            
        Returns:
            List of key sentences
        """
        if not text:
            return []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) <= num_sentences:
            return sentences
        
        # Score sentences based on various factors
        scores = {}
        
        # Get word frequencies
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score each sentence
        for i, sentence in enumerate(sentences):
            score = 0
            sentence_words = re.findall(r'\b[a-zA-Z]{3,}\b', sentence.lower())
            
            # Frequency score
            for word in sentence_words:
                score += word_freq.get(word, 0)
            
            # Position score (first and last sentences often important)
            if i == 0 or i == len(sentences) - 1:
                score += len(sentence_words) * 0.5
            
            # Length score (prefer medium-length sentences)
            length_score = 1.0 - abs(len(sentence_words) - 15) / 15
            score += length_score * len(sentence_words)
            
            scores[i] = score
        
        # Select top sentences while maintaining order
        top_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:num_sentences]
        top_indices.sort()  # Maintain original order
        
        return [sentences[i] for i in top_indices]
    
    def count_words(self, text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        return len(re.findall(r'\b\w+\b', text))
    
    def estimate_reading_time(self, text: str, words_per_minute: int = 250) -> int:
        """
        Estimate reading time in minutes
        
        Args:
            text: Text to analyze
            words_per_minute: Average reading speed
            
        Returns:
            Estimated reading time in minutes
        """
        word_count = self.count_words(text)
        return max(1, round(word_count / words_per_minute))
    
    def clean_url(self, url: str) -> str:
        """Clean and normalize URL"""
        if not url:
            return ""
        
        # Remove tracking parameters
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 
                          'fbclid', 'gclid', '_ga', 'ref', 'source']
        
        # Simple URL cleaning (would need more sophisticated parsing for production)
        for param in tracking_params:
            url = re.sub(f'[?&]{param}=[^&]*', '', url)
        
        # Clean up remaining parameters
        url = re.sub(r'[?&]$', '', url)
        url = re.sub(r'&', '?', url, count=1) if '?' not in url and '&' in url else url
        
        return url.strip()
