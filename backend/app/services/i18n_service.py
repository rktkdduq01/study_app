from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import json
from functools import lru_cache
import asyncio
import aiohttp
from googletrans import Translator
import logging

from ..models.i18n import (
    Language, TranslationKey, Translation, ContentTranslation,
    UserLanguagePreference, TranslationRequest, TranslationMemory
)
from ..models.user import User
from ..core.redis_client import redis_client
from ..core.config import settings

logger = logging.getLogger(__name__)

class I18nService:
    def __init__(self):
        self.redis_client = redis_client
        self.translator = Translator()
        self._translation_cache = {}
        self._language_cache = {}
        self.default_language = 'en'
    
    async def get_language(self, language_code: str, db: Session) -> Optional[Language]:
        """Get language by code"""
        if language_code in self._language_cache:
            return self._language_cache[language_code]
        
        language = db.query(Language).filter(
            Language.code == language_code,
            Language.is_active == True
        ).first()
        
        if language:
            self._language_cache[language_code] = language
        
        return language
    
    async def get_available_languages(self, db: Session) -> List[Language]:
        """Get all available languages"""
        cache_key = "i18n:languages:available"
        
        # Try Redis cache first
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        languages = db.query(Language).filter(
            Language.is_active == True
        ).order_by(Language.name).all()
        
        # Cache for 1 hour
        language_data = [
            {
                "id": lang.id,
                "code": lang.code,
                "name": lang.name,
                "native_name": lang.native_name,
                "direction": lang.direction,
                "is_default": lang.is_default
            }
            for lang in languages
        ]
        
        await self.redis_client.setex(
            cache_key,
            3600,
            json.dumps(language_data)
        )
        
        return languages
    
    async def get_translation(
        self,
        key: str,
        language_code: str,
        variables: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> str:
        """Get a translation for a key"""
        cache_key = f"i18n:translation:{language_code}:{key}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            translation = cached.decode()
        else:
            # Get from database
            translation_key = db.query(TranslationKey).filter(
                TranslationKey.key == key
            ).first()
            
            if not translation_key:
                logger.warning(f"Translation key not found: {key}")
                # Create translation request
                await self.create_translation_request(key, language_code, db)
                return key  # Return key as fallback
            
            language = await self.get_language(language_code, db)
            if not language:
                return key
            
            translation_record = db.query(Translation).filter(
                Translation.key_id == translation_key.id,
                Translation.language_id == language.id
            ).first()
            
            if translation_record:
                translation = translation_record.value
                # Cache for 1 hour
                await self.redis_client.setex(cache_key, 3600, translation)
            else:
                # Try to get default language translation
                default_translation = await self._get_default_translation(translation_key.id, db)
                if default_translation and settings.ENABLE_AUTO_TRANSLATION:
                    # Auto-translate if enabled
                    translation = await self.auto_translate(
                        default_translation.value,
                        self.default_language,
                        language_code,
                        db
                    )
                    # Save the auto-translation
                    await self.save_translation(
                        translation_key.id,
                        language.id,
                        translation,
                        is_machine_translated=True,
                        db=db
                    )
                else:
                    translation = key
                    # Create translation request
                    await self.create_translation_request(key, language_code, db)
        
        # Apply variables
        if variables:
            for var_name, var_value in variables.items():
                translation = translation.replace(f"{{{var_name}}}", str(var_value))
        
        return translation
    
    async def get_translations(
        self,
        keys: List[str],
        language_code: str,
        db: Session
    ) -> Dict[str, str]:
        """Get multiple translations at once"""
        translations = {}
        
        # Get language
        language = await self.get_language(language_code, db)
        if not language:
            return {key: key for key in keys}
        
        # Batch fetch from cache
        cache_keys = [f"i18n:translation:{language_code}:{key}" for key in keys]
        cached_values = await self.redis_client.mget(cache_keys)
        
        uncached_keys = []
        for i, (key, cached) in enumerate(zip(keys, cached_values)):
            if cached:
                translations[key] = cached.decode()
            else:
                uncached_keys.append(key)
        
        if uncached_keys:
            # Fetch from database
            translation_keys = db.query(TranslationKey).filter(
                TranslationKey.key.in_(uncached_keys)
            ).all()
            
            key_id_map = {tk.key: tk.id for tk in translation_keys}
            
            # Get translations
            translation_records = db.query(Translation).filter(
                Translation.key_id.in_(key_id_map.values()),
                Translation.language_id == language.id
            ).all()
            
            # Map translations
            translation_map = {t.key_id: t.value for t in translation_records}
            
            # Process uncached keys
            for key in uncached_keys:
                if key in key_id_map:
                    key_id = key_id_map[key]
                    if key_id in translation_map:
                        translation = translation_map[key_id]
                        translations[key] = translation
                        # Cache it
                        await self.redis_client.setex(
                            f"i18n:translation:{language_code}:{key}",
                            3600,
                            translation
                        )
                    else:
                        translations[key] = key
                        await self.create_translation_request(key, language_code, db)
                else:
                    translations[key] = key
        
        return translations
    
    async def get_content_translation(
        self,
        content_type: str,
        content_id: int,
        language_code: str,
        db: Session
    ) -> Optional[Dict[str, str]]:
        """Get translation for dynamic content"""
        cache_key = f"i18n:content:{content_type}:{content_id}:{language_code}"
        
        # Check cache
        cached = await self.redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Get from database
        language = await self.get_language(language_code, db)
        if not language:
            return None
        
        translation = db.query(ContentTranslation).filter(
            ContentTranslation.content_type == content_type,
            ContentTranslation.content_id == content_id,
            ContentTranslation.language_id == language.id
        ).first()
        
        if translation:
            # Cache for 30 minutes
            await self.redis_client.setex(
                cache_key,
                1800,
                json.dumps(translation.fields)
            )
            return translation.fields
        
        return None
    
    async def save_translation(
        self,
        key_id: int,
        language_id: int,
        value: str,
        translator_id: Optional[int] = None,
        is_machine_translated: bool = False,
        db: Session = None
    ) -> Translation:
        """Save or update a translation"""
        translation = db.query(Translation).filter(
            Translation.key_id == key_id,
            Translation.language_id == language_id
        ).first()
        
        if translation:
            translation.value = value
            translation.is_machine_translated = is_machine_translated
            translation.translator_id = translator_id
            translation.updated_at = datetime.utcnow()
        else:
            translation = Translation(
                key_id=key_id,
                language_id=language_id,
                value=value,
                translator_id=translator_id,
                is_machine_translated=is_machine_translated
            )
            db.add(translation)
        
        db.commit()
        
        # Clear cache
        key = db.query(TranslationKey).filter(TranslationKey.id == key_id).first()
        language = db.query(Language).filter(Language.id == language_id).first()
        
        if key and language:
            cache_key = f"i18n:translation:{language.code}:{key.key}"
            await self.redis_client.delete(cache_key)
        
        return translation
    
    async def save_content_translation(
        self,
        content_type: str,
        content_id: int,
        language_id: int,
        fields: Dict[str, str],
        translator_id: Optional[int] = None,
        is_machine_translated: bool = False,
        db: Session = None
    ) -> ContentTranslation:
        """Save or update content translation"""
        translation = db.query(ContentTranslation).filter(
            ContentTranslation.content_type == content_type,
            ContentTranslation.content_id == content_id,
            ContentTranslation.language_id == language_id
        ).first()
        
        if translation:
            translation.fields = fields
            translation.is_machine_translated = is_machine_translated
            translation.translator_id = translator_id
            translation.updated_at = datetime.utcnow()
        else:
            translation = ContentTranslation(
                content_type=content_type,
                content_id=content_id,
                language_id=language_id,
                fields=fields,
                translator_id=translator_id,
                is_machine_translated=is_machine_translated
            )
            db.add(translation)
        
        db.commit()
        
        # Clear cache
        language = db.query(Language).filter(Language.id == language_id).first()
        if language:
            cache_key = f"i18n:content:{content_type}:{content_id}:{language.code}"
            await self.redis_client.delete(cache_key)
        
        return translation
    
    async def auto_translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        db: Session = None
    ) -> str:
        """Auto-translate text using Google Translate"""
        try:
            # Check translation memory first
            memory = db.query(TranslationMemory).filter(
                TranslationMemory.source_text == text,
                TranslationMemory.source_language_id == (
                    db.query(Language.id).filter(Language.code == source_language).scalar()
                ),
                TranslationMemory.target_language_id == (
                    db.query(Language.id).filter(Language.code == target_language).scalar()
                )
            ).first()
            
            if memory:
                # Update usage count
                memory.usage_count += 1
                memory.last_used_at = datetime.utcnow()
                db.commit()
                return memory.target_text
            
            # Translate using Google Translate
            result = self.translator.translate(
                text,
                src=source_language,
                dest=target_language
            )
            
            translated_text = result.text
            
            # Save to translation memory
            if db:
                source_lang_id = db.query(Language.id).filter(
                    Language.code == source_language
                ).scalar()
                target_lang_id = db.query(Language.id).filter(
                    Language.code == target_language
                ).scalar()
                
                if source_lang_id and target_lang_id:
                    memory = TranslationMemory(
                        source_language_id=source_lang_id,
                        target_language_id=target_lang_id,
                        source_text=text,
                        target_text=translated_text,
                        quality_score=80,  # Default score for machine translation
                        domain='education'
                    )
                    db.add(memory)
                    db.commit()
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Auto-translation failed: {str(e)}")
            return text
    
    async def get_user_language(
        self,
        user_id: int,
        db: Session
    ) -> str:
        """Get user's preferred language"""
        preference = db.query(UserLanguagePreference).filter(
            UserLanguagePreference.user_id == user_id
        ).first()
        
        if preference and preference.interface_language:
            return preference.interface_language.code
        
        return self.default_language
    
    async def set_user_language(
        self,
        user_id: int,
        language_code: str,
        db: Session
    ) -> UserLanguagePreference:
        """Set user's preferred language"""
        language = await self.get_language(language_code, db)
        if not language:
            raise ValueError(f"Invalid language code: {language_code}")
        
        preference = db.query(UserLanguagePreference).filter(
            UserLanguagePreference.user_id == user_id
        ).first()
        
        if preference:
            preference.interface_language_id = language.id
            preference.content_language_id = language.id
            preference.updated_at = datetime.utcnow()
        else:
            preference = UserLanguagePreference(
                user_id=user_id,
                primary_language_id=language.id,
                interface_language_id=language.id,
                content_language_id=language.id
            )
            db.add(preference)
        
        db.commit()
        
        # Clear user cache
        await self.redis_client.delete(f"i18n:user_language:{user_id}")
        
        return preference
    
    async def create_translation_request(
        self,
        key: str,
        language_code: str,
        db: Session,
        context: Optional[str] = None,
        requested_by_id: Optional[int] = None,
        priority: str = 'normal'
    ) -> TranslationRequest:
        """Create a request for missing translation"""
        language = await self.get_language(language_code, db)
        if not language:
            return None
        
        # Check if request already exists
        existing = db.query(TranslationRequest).filter(
            TranslationRequest.key == key,
            TranslationRequest.language_id == language.id,
            TranslationRequest.status.in_(['pending', 'in_progress'])
        ).first()
        
        if existing:
            return existing
        
        request = TranslationRequest(
            key=key,
            language_id=language.id,
            requested_by_id=requested_by_id or 1,  # System user
            context=context,
            priority=priority
        )
        
        db.add(request)
        db.commit()
        
        return request
    
    async def _get_default_translation(
        self,
        key_id: int,
        db: Session
    ) -> Optional[Translation]:
        """Get translation in default language"""
        default_language = db.query(Language).filter(
            Language.is_default == True
        ).first()
        
        if not default_language:
            default_language = db.query(Language).filter(
                Language.code == self.default_language
        ).first()
        
        if not default_language:
            return None
        
        return db.query(Translation).filter(
            Translation.key_id == key_id,
            Translation.language_id == default_language.id
        ).first()
    
    async def verify_translation(
        self,
        translation_id: int,
        verifier_id: int,
        db: Session
    ) -> Translation:
        """Mark a translation as verified"""
        translation = db.query(Translation).filter(
            Translation.id == translation_id
        ).first()
        
        if not translation:
            raise ValueError("Translation not found")
        
        translation.is_verified = True
        translation.verified_by_id = verifier_id
        translation.verified_at = datetime.utcnow()
        
        db.commit()
        
        # Clear cache
        cache_key = f"i18n:translation:{translation.language.code}:{translation.key.key}"
        await self.redis_client.delete(cache_key)
        
        return translation
    
    async def get_translation_stats(
        self,
        language_code: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get translation statistics"""
        stats = {}
        
        if language_code:
            language = await self.get_language(language_code, db)
            if not language:
                return stats
            
            total_keys = db.query(TranslationKey).count()
            translated_keys = db.query(Translation).filter(
                Translation.language_id == language.id
            ).count()
            verified_keys = db.query(Translation).filter(
                Translation.language_id == language.id,
                Translation.is_verified == True
            ).count()
            machine_translated = db.query(Translation).filter(
                Translation.language_id == language.id,
                Translation.is_machine_translated == True
            ).count()
            
            stats = {
                "language": language.name,
                "total_keys": total_keys,
                "translated_keys": translated_keys,
                "verified_keys": verified_keys,
                "machine_translated": machine_translated,
                "completion_percentage": (translated_keys / total_keys * 100) if total_keys > 0 else 0,
                "verification_percentage": (verified_keys / translated_keys * 100) if translated_keys > 0 else 0
            }
        else:
            # Global stats
            languages = db.query(Language).filter(Language.is_active == True).all()
            total_keys = db.query(TranslationKey).count()
            
            language_stats = []
            for lang in languages:
                translated = db.query(Translation).filter(
                    Translation.language_id == lang.id
                ).count()
                verified = db.query(Translation).filter(
                    Translation.language_id == lang.id,
                    Translation.is_verified == True
                ).count()
                
                language_stats.append({
                    "code": lang.code,
                    "name": lang.name,
                    "translated": translated,
                    "verified": verified,
                    "completion": (translated / total_keys * 100) if total_keys > 0 else 0
                })
            
            stats = {
                "total_keys": total_keys,
                "total_languages": len(languages),
                "languages": language_stats
            }
        
        return stats
    
    async def export_translations(
        self,
        language_code: str,
        format: str = 'json',
        db: Session = None
    ) -> Union[Dict, str]:
        """Export translations for a language"""
        language = await self.get_language(language_code, db)
        if not language:
            return {}
        
        # Get all translations for the language
        translations = db.query(Translation).join(
            TranslationKey
        ).filter(
            Translation.language_id == language.id
        ).all()
        
        result = {}
        for trans in translations:
            result[trans.key.key] = {
                "value": trans.value,
                "verified": trans.is_verified,
                "machine_translated": trans.is_machine_translated
            }
        
        if format == 'json':
            return result
        elif format == 'po':
            # Generate PO file format
            po_content = f"""# Translations for {language.name}
# Generated on {datetime.utcnow().isoformat()}

"""
            for trans in translations:
                po_content += f'msgid "{trans.key.key}"\n'
                po_content += f'msgstr "{trans.value}"\n\n'
            
            return po_content
        
        return result

# Singleton instance
i18n_service = I18nService()