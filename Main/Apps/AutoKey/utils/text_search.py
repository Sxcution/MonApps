"""
Text Search Engine - OCR-based text detection with fuzzy matching
Supports multiple languages, preprocessing, and various matching modes
"""
import cv2
import numpy as np
import easyocr
from dataclasses import dataclass
from typing import List, Tuple, Optional
from rapidfuzz import fuzz
import re
import unicodedata
from unidecode import unidecode

@dataclass
class OCRResult:
    """Single OCR detection result"""
    text: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float

@dataclass
class TextSearchResult:
    """Text search match result"""
    text: str
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    ocr_conf: float
    match_score: int

class TextSearchEngine:
    """OCR and text matching engine"""
    
    # Character confusion mapping (commonly confused characters)
    CHAR_MAP = {
        'O': '0', '0': 'O',
        'I': '1', 'l': '1', '|': '1', '1': 'I',
        'S': '5', '5': 'S',
        'B': '8', '8': 'B',
        'Z': '2', '2': 'Z',
        'G': '6', '6': 'G'
    }
    
    def __init__(self, languages=['en', 'vi', 'ch_sim'], gpu=False):
        """
        Initialize OCR engine
        Args:
            languages: List of language codes for OCR
            gpu: Whether to use GPU acceleration
        """
        self.languages = languages
        self.gpu = gpu
        self.reader = None
        print(f"🔍 TextSearchEngine: Initializing with languages {languages}, GPU={gpu}")
    
    def _init_reader(self):
        """Lazy initialization of EasyOCR reader"""
        if self.reader is None:
            print(f"📦 Loading EasyOCR models for {self.languages}...")
            self.reader = easyocr.Reader(self.languages, gpu=self.gpu)
            print("✅ EasyOCR models loaded")
    
    def ocr(self, image: np.ndarray, preproc=False) -> List[OCRResult]:
        """
        Perform OCR on image
        Args:
            image: BGR image (numpy array)
            preproc: Apply preprocessing (contrast, threshold)
        Returns:
            List of OCRResult
        """
        self._init_reader()
        
        # Preprocessing
        if preproc:
            image = self._preprocess(image)
        
        # Convert BGR to RGB for EasyOCR
        if len(image.shape) == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Run OCR
        results = self.reader.readtext(image_rgb)
        
        # Parse results
        ocr_results = []
        for bbox, text, conf in results:
            # Convert bbox from polygon to rect
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            x1, y1 = int(min(x_coords)), int(min(y_coords))
            x2, y2 = int(max(x_coords)), int(max(y_coords))
            
            ocr_results.append(OCRResult(
                text=text,
                bbox=(x1, y1, x2, y2),
                confidence=conf
            ))
        
        return ocr_results
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to improve OCR accuracy
        Args:
            image: Input image
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for matching
        - Casefold (Unicode-aware lowercase)
        - Remove diacritics
        - Map confused characters
        - Collapse whitespace
        
        Args:
            text: Input text
        Returns:
            Normalized text
        """
        # 1. Casefold
        text = text.casefold()
        
        # 2. Remove diacritics
        text = unidecode(text)
        
        # 3. Character mapping (handle variations)
        result = []
        for char in text:
            # Keep original + add mapped version
            result.append(char)
            if char.upper() in self.CHAR_MAP:
                result.append(self.CHAR_MAP[char.upper()].lower())
        
        text = ''.join(result)
        
        # 4. Collapse whitespace
        text = ' '.join(text.split())
        
        return text
    
    def match(self, query: str, target: str, mode='fuzzy', min_score=85) -> Optional[int]:
        """
        Match query against target text
        Args:
            query: Search query
            target: Target text to match against
            mode: 'fuzzy', 'exact', or 'regex'
            min_score: Minimum score for fuzzy matching (0-100)
        Returns:
            Match score (0-100) or None if no match
        """
        if mode == 'exact':
            # Exact match (after normalization)
            norm_query = self.normalize_text(query)
            norm_target = self.normalize_text(target)
            return 100 if norm_query == norm_target else 0
        
        elif mode == 'regex':
            # Regex match
            try:
                if re.search(query, target, re.IGNORECASE):
                    return 100
                else:
                    return 0
            except re.error:
                return 0
        
        else:  # fuzzy
            # Fuzzy match using RapidFuzz
            norm_query = self.normalize_text(query)
            norm_target = self.normalize_text(target)
            
            # Use partial ratio for substring matching
            score = fuzz.partial_ratio(norm_query, norm_target)
            
            return score if score >= min_score else 0
    
    def search(self, image: np.ndarray, query: str, 
               match_mode='fuzzy', min_score=85, preproc=False) -> Optional[TextSearchResult]:
        """
        Search for text in image
        Args:
            image: BGR image
            query: Search query
            match_mode: 'fuzzy', 'exact', or 'regex'
            min_score: Minimum match score
            preproc: Apply preprocessing
        Returns:
            Best TextSearchResult or None
        """
        # Perform OCR
        ocr_results = self.ocr(image, preproc=preproc)
        
        # Find best match
        best_match = None
        best_score = 0
        
        for ocr_result in ocr_results:
            score = self.match(query, ocr_result.text, match_mode, min_score)
            
            if score and score > best_score:
                best_score = score
                x1, y1, x2, y2 = ocr_result.bbox
                center = ((x1 + x2) // 2, (y1 + y2) // 2)
                
                best_match = TextSearchResult(
                    text=ocr_result.text,
                    bbox=ocr_result.bbox,
                    center=center,
                    ocr_conf=ocr_result.confidence,
                    match_score=score
                )
        
        return best_match
