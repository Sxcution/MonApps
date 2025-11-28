"""
Windows OCR Engine - Fast native OCR using Windows.Media.Ocr
Requires: Windows 10+, winrt packages
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
import cv2

# Lazy import
try:
    import winrt.windows.media.ocr as ocr_module
    import winrt.windows.storage.streams as streams_module
    import winrt.windows.graphics.imaging as imaging_module
    import asyncio
    
    OcrEngine = ocr_module.OcrEngine
    DataWriter = streams_module.DataWriter
    InMemoryRandomAccessStream = streams_module.InMemoryRandomAccessStream
    BitmapDecoder = imaging_module.BitmapDecoder
    
    HAS_WINRT = True
except ImportError as e:
    HAS_WINRT = False
    OcrEngine = None
    print(f"⚠️ Windows OCR not available: {e}")

@dataclass
class OCRResult:
    """OCR result for a single text region"""
    text: str
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float

class WindowsOCR:
    """Windows native OCR engine - ultra fast"""
    
    def __init__(self, language='en'):
        """
        Initialize Windows OCR
        Args:
            language: Language code (e.g. 'en', 'vi')
        """
        if not HAS_WINRT:
            raise ImportError("winrt packages not installed. Run: pip install winrt-Windows.Media.Ocr winrt-Windows.Storage.Streams winrt-Windows.Graphics.Imaging")
        
        self.language = language
        self.engine = None
        self._init_engine()
    
    def _init_engine(self):
        """Initialize OCR engine for specified language"""
        try:
            # Try to get language-specific engine
            languages = OcrEngine.available_recognizer_languages
            lang_found = False
            
            for lang in languages:
                if lang.language_tag.lower().startswith(self.language.lower()):
                    self.engine = OcrEngine.try_create_from_language(lang)
                    lang_found = True
                    print(f"✅ Windows OCR: Loaded '{lang.display_name}' engine")
                    break
            
            if not lang_found:
                # Fallback to default
                self.engine = OcrEngine.try_create_from_user_profile_languages()
                print(f"⚠️ Windows OCR: '{self.language}' not found, using default")
        
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Windows OCR: {e}")
    
    async def _recognize_async(self, image: np.ndarray) -> List[OCRResult]:
        """
        Async OCR recognition
        Args:
            image: BGR image as numpy array
        Returns:
            List of OCR results
        """
        # Convert BGR to PNG bytes
        success, buffer = cv2.imencode('.png', image)
        if not success:
            return []
        
        png_bytes = buffer.tobytes()
        
        # Create InMemoryRandomAccessStream
        stream = InMemoryRandomAccessStream()
        writer = DataWriter(stream)
        writer.write_bytes(png_bytes)
        await writer.store_async()
        stream.seek(0)
        
        # Decode to SoftwareBitmap
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        
        # Perform OCR
        result = await self.engine.recognize_async(bitmap)
        
        # Parse results
        ocr_results = []
        for line in result.lines:
            text = line.text
            
            # Get bounding box
            words = list(line.words)
            if not words:
                continue
            
            # Calculate line bbox from words
            x1 = min(w.bounding_rect.x for w in words)
            y1 = min(w.bounding_rect.y for w in words)
            x2 = max(w.bounding_rect.x + w.bounding_rect.width for w in words)
            y2 = max(w.bounding_rect.y + w.bounding_rect.height for w in words)
            
            # Windows OCR doesn't provide confidence, use 1.0
            ocr_results.append(OCRResult(
                text=text,
                bbox=(int(x1), int(y1), int(x2), int(y2)),
                confidence=1.0
            ))
        
        return ocr_results
    
    def recognize(self, image: np.ndarray) -> List[OCRResult]:
        """
        Synchronous wrapper for OCR
        Args:
            image: BGR image as numpy array
        Returns:
            List of OCR results
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._recognize_async(image))
        finally:
            loop.close()
    
    @staticmethod
    def is_available() -> bool:
        """Check if Windows OCR is available"""
        return HAS_WINRT
    
    @staticmethod
    def get_available_languages() -> List[str]:
        """Get list of available language codes"""
        if not HAS_WINRT:
            return []
        
        try:
            languages = OcrEngine.available_recognizer_languages
            return [lang.language_tag for lang in languages]
        except:
            return []
