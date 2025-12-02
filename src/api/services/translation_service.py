"""
Multilingual Translation Service
Provides translation capabilities for loan documents and UI
Supports Hindi, Telugu, Tamil, Spanish, and other languages
"""

from typing import Dict, Optional, List
from googletrans import Translator, LANGUAGES
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class TranslationService:
    """
    Service for translating loan documents and UI text
    """
    
    # Supported languages with native names
    SUPPORTED_LANGUAGES = {
        'en': {'name': 'English', 'native': 'English'},
        'hi': {'name': 'Hindi', 'native': 'हिंदी'},
        'te': {'name': 'Telugu', 'native': 'తెలుగు'},
        'ta': {'name': 'Tamil', 'native': 'தமிழ்'},
        'es': {'name': 'Spanish', 'native': 'Español'},
        'zh-cn': {'name': 'Chinese (Simplified)', 'native': '简体中文'},
        'fr': {'name': 'French', 'native': 'Français'},
        'de': {'name': 'German', 'native': 'Deutsch'},
        'pt': {'name': 'Portuguese', 'native': 'Português'},
        'ru': {'name': 'Russian', 'native': 'Русский'},
    }
    
    def __init__(self):
        """Initialize translation service"""
        self.translator = Translator()
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = 'auto') -> Dict[str, str]:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'hi', 'te', 'ta')
            source_lang: Source language (default: auto-detect)
            
        Returns:
            Dictionary with translation result
        """
        try:
            if target_lang == 'en' or target_lang == source_lang:
                return {
                    'translated_text': text,
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'confidence': 1.0
                }
            
            result = self.translator.translate(text, src=source_lang, dest=target_lang)
            
            return {
                'translated_text': result.text,
                'source_lang': result.src,
                'target_lang': target_lang,
                'confidence': 0.95  # Google Translate doesn't provide confidence
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                'translated_text': text,  # Fallback to original
                'source_lang': source_lang,
                'target_lang': target_lang,
                'confidence': 0.0,
                'error': str(e)
            }
    
    def translate_document_data(self, extraction_result: Dict, target_lang: str) -> Dict:
        """
        Translate extracted document data
        
        Args:
            extraction_result: Lab3 extraction result
            target_lang: Target language code
            
        Returns:
            Translated extraction result
        """
        if target_lang == 'en':
            return extraction_result
        
        try:
            translated_result = extraction_result.copy()
            
            # Translate complete text
            if 'complete_extraction' in extraction_result:
                text_data = extraction_result['complete_extraction'].get('text_extraction', {})
                if 'all_text' in text_data:
                    translation = self.translate_text(text_data['all_text'], target_lang)
                    translated_result['complete_extraction']['text_extraction']['translated_text'] = translation['translated_text']
                    translated_result['translation_info'] = {
                        'target_language': target_lang,
                        'source_language': translation['source_lang']
                    }
            
            # Translate form field values (optional - usually keep numbers as-is)
            # This can be enhanced based on field type
            
            return translated_result
            
        except Exception as e:
            logger.error(f"Document translation failed: {e}")
            return extraction_result
    
    @lru_cache(maxsize=1000)
    def translate_ui_text(self, text: str, target_lang: str) -> str:
        """
        Translate UI text with caching
        
        Args:
            text: UI text to translate
            target_lang: Target language
            
        Returns:
            Translated text
        """
        if target_lang == 'en':
            return text
        
        try:
            result = self.translator.translate(text, dest=target_lang)
            return result.text
        except Exception as e:
            logger.error(f"UI translation failed: {e}")
            return text
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages
        
        Returns:
            List of language dictionaries
        """
        return [
            {
                'code': code,
                'name': info['name'],
                'native': info['native']
            }
            for code, info in self.SUPPORTED_LANGUAGES.items()
        ]
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code
        """
        try:
            result = self.translator.detect(text)
            return result.lang
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return 'en'


# UI Labels Dictionary
UI_LABELS = {
    'en': {
        'upload_document': 'Upload Loan Document',
        'select_language': 'Select Language',
        'processing': 'Processing your document...',
        'extraction_complete': 'Extraction Complete',
        'principal_amount': 'Principal Amount',
        'interest_rate': 'Interest Rate',
        'tenure': 'Loan Term',
        'monthly_payment': 'Monthly Payment',
        'total_cost': 'Total Cost',
        'bank_name': 'Lender Name',
        'compare_loans': 'Compare Loans',
        'ask_question': 'Ask a Question',
        'download_report': 'Download Report',
    },
    'hi': {
        'upload_document': 'ऋण दस्तावेज़ अपलोड करें',
        'select_language': 'भाषा चुनें',
        'processing': 'आपके दस्तावेज़ की प्रक्रिया हो रही है...',
        'extraction_complete': 'निष्कर्षण पूर्ण',
        'principal_amount': 'मूल राशि',
        'interest_rate': 'ब्याज दर',
        'tenure': 'ऋण अवधि',
        'monthly_payment': 'मासिक भुगतान',
        'total_cost': 'कुल लागत',
        'bank_name': 'ऋणदाता का नाम',
        'compare_loans': 'ऋणों की तुलना करें',
        'ask_question': 'प्रश्न पूछें',
        'download_report': 'रिपोर्ट डाउनलोड करें',
    },
    'te': {
        'upload_document': 'రుణ పత్రాన్ని అప్‌లోడ్ చేయండి',
        'select_language': 'భాషను ఎంచుకోండి',
        'processing': 'మీ పత్రాన్ని ప్రాసెస్ చేస్తోంది...',
        'extraction_complete': 'వెలికితీత పూర్తయింది',
        'principal_amount': 'ప్రధాన మొత్తం',
        'interest_rate': 'వడ్డీ రేటు',
        'tenure': 'రుణ కాలం',
        'monthly_payment': 'నెలవారీ చెల్లింపు',
        'total_cost': 'మొత్తం ఖర్చు',
        'bank_name': 'రుణదాత పేరు',
        'compare_loans': 'రుణాలను పోల్చండి',
        'ask_question': 'ప్రశ్న అడగండి',
        'download_report': 'నివేదికను డౌన్‌లోడ్ చేయండి',
    },
    'ta': {
        'upload_document': 'கடன் ஆவணத்தைப் பதிவேற்றவும்',
        'select_language': 'மொழியைத் தேர்ந்தெடுக்கவும்',
        'processing': 'உங்கள் ஆவணம் செயலாக்கப்படுகிறது...',
        'extraction_complete': 'பிரித்தெடுத்தல் நிறைவானது',
        'principal_amount': 'முதல் தொகை',
        'interest_rate': 'வட்டி விகிதம்',
        'tenure': 'கடன் காலம்',
        'monthly_payment': 'மாதாந்திர செலுத்தல்',
        'total_cost': 'மொத்த செலவு',
        'bank_name': 'கடன் வழங்குநர் பெயர்',
        'compare_loans': 'கடன்களை ஒப்பிடவும்',
        'ask_question': 'கேள்வி கேளுங்கள்',
        'download_report': 'அறிக்கையைப் பதிவிறக்கவும்',
    }
}


def get_ui_label(key: str, language: str = 'en') -> str:
    """
    Get UI label in specified language
    
    Args:
        key: Label key
        language: Language code
        
    Returns:
        Translated label or English fallback
    """
    return UI_LABELS.get(language, {}).get(key, UI_LABELS['en'].get(key, key))


# Create singleton instance
translation_service = TranslationService()
