from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

from ...database import get_db
from ...core.auth import get_current_user, get_current_admin_user
from ...models.user import User
from ...models.i18n import Language, TranslationKey, Translation, ContentTranslation
from ...services.i18n_service import i18n_service

router = APIRouter()

class TranslationRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = None
    category: Optional[str] = None
    context: Optional[str] = None
    max_length: Optional[int] = None
    variables: Optional[List[str]] = None

class ContentTranslationRequest(BaseModel):
    content_type: str
    content_id: int
    fields: Dict[str, str]

class LanguagePreferenceRequest(BaseModel):
    language_code: str
    timezone: Optional[str] = None

class TranslationVerifyRequest(BaseModel):
    translation_id: int

@router.get("/languages")
async def get_available_languages(
    db: Session = Depends(get_db)
):
    """Get all available languages"""
    languages = await i18n_service.get_available_languages(db)
    return {
        "languages": [
            {
                "code": lang.code,
                "name": lang.name,
                "native_name": lang.native_name,
                "direction": lang.direction,
                "is_default": lang.is_default,
                "locale": {
                    "date_format": lang.date_format,
                    "time_format": lang.time_format,
                    "currency_code": lang.currency_code,
                    "currency_symbol": lang.currency_symbol,
                    "decimal_separator": lang.decimal_separator,
                    "thousands_separator": lang.thousands_separator
                }
            }
            for lang in languages
        ]
    }

@router.get("/translate/{key}")
async def get_translation(
    key: str,
    language: str = Query(..., description="Language code (e.g., 'en', 'ko', 'ja')"),
    variables: Optional[str] = Query(None, description="JSON string of variables"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get translation for a specific key"""
    # Parse variables if provided
    vars_dict = None
    if variables:
        import json
        try:
            vars_dict = json.loads(variables)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid variables format")
    
    translation = await i18n_service.get_translation(
        key=key,
        language_code=language,
        variables=vars_dict,
        db=db
    )
    
    return {
        "key": key,
        "language": language,
        "translation": translation
    }

@router.post("/translate/batch")
async def get_translations_batch(
    keys: List[str],
    language: str = Query(..., description="Language code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get translations for multiple keys"""
    translations = await i18n_service.get_translations(
        keys=keys,
        language_code=language,
        db=db
    )
    
    return {
        "language": language,
        "translations": translations
    }

@router.get("/content/{content_type}/{content_id}")
async def get_content_translation(
    content_type: str,
    content_id: int,
    language: str = Query(..., description="Language code"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get translation for dynamic content"""
    translation = await i18n_service.get_content_translation(
        content_type=content_type,
        content_id=content_id,
        language_code=language,
        db=db
    )
    
    if not translation:
        return {
            "content_type": content_type,
            "content_id": content_id,
            "language": language,
            "fields": {}
        }
    
    return {
        "content_type": content_type,
        "content_id": content_id,
        "language": language,
        "fields": translation
    }

@router.get("/user/language")
async def get_user_language(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's language preference"""
    language_code = await i18n_service.get_user_language(
        user_id=current_user.id,
        db=db
    )
    
    # Get full language details
    language = await i18n_service.get_language(language_code, db)
    
    return {
        "language_code": language_code,
        "language": {
            "code": language.code,
            "name": language.name,
            "native_name": language.native_name,
            "direction": language.direction
        } if language else None
    }

@router.put("/user/language")
async def set_user_language(
    request: LanguagePreferenceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set user's language preference"""
    try:
        preference = await i18n_service.set_user_language(
            user_id=current_user.id,
            language_code=request.language_code,
            db=db
        )
        
        # Update timezone if provided
        if request.timezone:
            preference.timezone = request.timezone
            db.commit()
        
        return {
            "status": "success",
            "language_code": request.language_code,
            "message": "Language preference updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/admin/translation")
async def create_or_update_translation(
    language_code: str,
    request: TranslationRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create or update a translation (admin only)"""
    # Get or create translation key
    key = db.query(TranslationKey).filter(
        TranslationKey.key == request.key
    ).first()
    
    if not key:
        key = TranslationKey(
            key=request.key,
            description=request.description,
            category=request.category,
            context=request.context,
            max_length=request.max_length,
            variables=request.variables or []
        )
        db.add(key)
        db.commit()
    
    # Get language
    language = await i18n_service.get_language(language_code, db)
    if not language:
        raise HTTPException(status_code=400, detail="Invalid language code")
    
    # Save translation
    translation = await i18n_service.save_translation(
        key_id=key.id,
        language_id=language.id,
        value=request.value,
        translator_id=current_user.id,
        is_machine_translated=False,
        db=db
    )
    
    return {
        "status": "success",
        "translation_id": translation.id,
        "key": request.key,
        "language": language_code,
        "value": request.value
    }

@router.post("/admin/content-translation")
async def create_content_translation(
    language_code: str,
    request: ContentTranslationRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create or update content translation (admin only)"""
    # Get language
    language = await i18n_service.get_language(language_code, db)
    if not language:
        raise HTTPException(status_code=400, detail="Invalid language code")
    
    # Save translation
    translation = await i18n_service.save_content_translation(
        content_type=request.content_type,
        content_id=request.content_id,
        language_id=language.id,
        fields=request.fields,
        translator_id=current_user.id,
        is_machine_translated=False,
        db=db
    )
    
    return {
        "status": "success",
        "translation_id": translation.id,
        "content_type": request.content_type,
        "content_id": request.content_id,
        "language": language_code
    }

@router.post("/admin/verify")
async def verify_translation(
    request: TranslationVerifyRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Verify a translation (admin/translator only)"""
    try:
        translation = await i18n_service.verify_translation(
            translation_id=request.translation_id,
            verifier_id=current_user.id,
            db=db
        )
        
        return {
            "status": "success",
            "translation_id": translation.id,
            "message": "Translation verified successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/stats")
async def get_translation_stats(
    language_code: Optional[str] = Query(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get translation statistics (admin only)"""
    stats = await i18n_service.get_translation_stats(
        language_code=language_code,
        db=db
    )
    
    return stats

@router.get("/export/{language_code}")
async def export_translations(
    language_code: str,
    format: str = Query("json", description="Export format: json, po"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export translations for a language (admin only)"""
    result = await i18n_service.export_translations(
        language_code=language_code,
        format=format,
        db=db
    )
    
    if format == "po":
        from fastapi.responses import Response
        return Response(
            content=result,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={language_code}.po"
            }
        )
    
    return result

@router.get("/missing")
async def get_missing_translations(
    language_code: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get missing translations for a language (admin only)"""
    # Get language
    language = await i18n_service.get_language(language_code, db)
    if not language:
        raise HTTPException(status_code=400, detail="Invalid language code")
    
    # Get all keys
    all_keys = db.query(TranslationKey).all()
    
    # Get translated keys
    translated_key_ids = db.query(Translation.key_id).filter(
        Translation.language_id == language.id
    ).all()
    translated_key_ids = [t[0] for t in translated_key_ids]
    
    # Find missing keys
    missing_keys = [
        {
            "id": key.id,
            "key": key.key,
            "description": key.description,
            "category": key.category,
            "context": key.context
        }
        for key in all_keys
        if key.id not in translated_key_ids
    ][:limit]
    
    return {
        "language_code": language_code,
        "total_missing": len([k for k in all_keys if k.id not in translated_key_ids]),
        "missing_keys": missing_keys
    }

@router.post("/auto-translate")
async def auto_translate_content(
    text: str,
    source_language: str,
    target_language: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Auto-translate text (requires appropriate permissions)"""
    # Check if auto-translation is enabled
    from ...core.config import settings
    if not hasattr(settings, 'ENABLE_AUTO_TRANSLATION') or not settings.ENABLE_AUTO_TRANSLATION:
        raise HTTPException(
            status_code=403,
            detail="Auto-translation is not enabled"
        )
    
    # For non-admin users, limit translation length
    if current_user.role != "admin" and len(text) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Text too long for auto-translation (max 1000 characters)"
        )
    
    translated = await i18n_service.auto_translate(
        text=text,
        source_language=source_language,
        target_language=target_language,
        db=db
    )
    
    return {
        "source_language": source_language,
        "target_language": target_language,
        "source_text": text,
        "translated_text": translated,
        "is_machine_translated": True
    }