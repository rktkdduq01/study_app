from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base

class Language(Base):
    """Supported languages"""
    __tablename__ = "languages"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)  # e.g., 'en', 'ko', 'ja', 'zh-CN'
    name = Column(String(50), nullable=False)  # e.g., 'English', '한국어', '日本語'
    native_name = Column(String(50), nullable=False)  # Name in native language
    direction = Column(String(3), default='ltr')  # 'ltr' or 'rtl'
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Locale settings
    date_format = Column(String(50), default='YYYY-MM-DD')
    time_format = Column(String(50), default='HH:mm:ss')
    currency_code = Column(String(3), default='USD')
    currency_symbol = Column(String(10), default='$')
    decimal_separator = Column(String(1), default='.')
    thousands_separator = Column(String(1), default=',')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    translations = relationship("Translation", back_populates="language", cascade="all, delete-orphan")
    content_translations = relationship("ContentTranslation", back_populates="language")

class TranslationKey(Base):
    """Translation keys for UI and system messages"""
    __tablename__ = "translation_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)  # e.g., 'common.button.submit'
    description = Column(Text)  # Description for translators
    category = Column(String(50), index=True)  # e.g., 'ui', 'error', 'notification'
    
    # Context for better translations
    context = Column(Text)  # Where/how this text is used
    max_length = Column(Integer)  # Maximum character length (for UI constraints)
    
    # Variables in the translation (e.g., {username}, {count})
    variables = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    translations = relationship("Translation", back_populates="key", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_translation_key_category', 'category'),
    )

class Translation(Base):
    """Actual translations for each key-language combination"""
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    key_id = Column(Integer, ForeignKey("translation_keys.id"), nullable=False)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    
    value = Column(Text, nullable=False)  # The translated text
    
    # Translation metadata
    is_verified = Column(Boolean, default=False)  # Verified by native speaker
    is_machine_translated = Column(Boolean, default=False)
    translator_id = Column(Integer, ForeignKey("users.id"))
    verified_by_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime)
    
    # Relationships
    key = relationship("TranslationKey", back_populates="translations")
    language = relationship("Language", back_populates="translations")
    translator = relationship("User", foreign_keys=[translator_id])
    verifier = relationship("User", foreign_keys=[verified_by_id])
    
    __table_args__ = (
        UniqueConstraint('key_id', 'language_id', name='uq_translation_key_language'),
        Index('idx_translation_language', 'language_id'),
        Index('idx_translation_verified', 'is_verified'),
    )

class ContentTranslation(Base):
    """Translations for dynamic content (quests, lessons, etc.)"""
    __tablename__ = "content_translations"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(50), nullable=False)  # 'quest', 'lesson', 'achievement', etc.
    content_id = Column(Integer, nullable=False)  # ID of the content
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    
    # Translated fields (stored as JSON for flexibility)
    fields = Column(JSON, nullable=False)  # e.g., {"title": "...", "description": "..."}
    
    # Translation metadata
    is_verified = Column(Boolean, default=False)
    is_machine_translated = Column(Boolean, default=False)
    translator_id = Column(Integer, ForeignKey("users.id"))
    verified_by_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    language = relationship("Language", back_populates="content_translations")
    translator = relationship("User", foreign_keys=[translator_id])
    verifier = relationship("User", foreign_keys=[verified_by_id])
    
    __table_args__ = (
        UniqueConstraint('content_type', 'content_id', 'language_id', name='uq_content_translation'),
        Index('idx_content_translation_type_id', 'content_type', 'content_id'),
        Index('idx_content_translation_language', 'language_id'),
    )

class UserLanguagePreference(Base):
    """User's language preferences"""
    __tablename__ = "user_language_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    primary_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    secondary_language_id = Column(Integer, ForeignKey("languages.id"))
    
    # UI preferences
    interface_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    content_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    
    # Learning preferences
    learning_languages = Column(JSON, default=[])  # List of language codes user is learning
    
    # Regional preferences
    timezone = Column(String(50), default='UTC')
    date_format_override = Column(String(50))  # Override language default
    time_format_override = Column(String(50))  # Override language default
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="language_preference")
    primary_language = relationship("Language", foreign_keys=[primary_language_id])
    secondary_language = relationship("Language", foreign_keys=[secondary_language_id])
    interface_language = relationship("Language", foreign_keys=[interface_language_id])
    content_language = relationship("Language", foreign_keys=[content_language_id])

class TranslationRequest(Base):
    """Requests for missing translations"""
    __tablename__ = "translation_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False)  # The key that needs translation
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    context = Column(Text)  # Where the user encountered this
    priority = Column(String(20), default='normal')  # 'low', 'normal', 'high', 'urgent'
    
    status = Column(String(20), default='pending')  # 'pending', 'in_progress', 'completed', 'rejected'
    assigned_to_id = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    language = relationship("Language")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    
    __table_args__ = (
        Index('idx_translation_request_status', 'status'),
        Index('idx_translation_request_language', 'language_id'),
    )

class TranslationMemory(Base):
    """Store previously translated segments for consistency"""
    __tablename__ = "translation_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    source_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    target_language_id = Column(Integer, ForeignKey("languages.id"), nullable=False)
    
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    
    # Quality metrics
    quality_score = Column(Integer, default=100)  # 0-100
    usage_count = Column(Integer, default=0)
    
    # Context
    domain = Column(String(50))  # 'education', 'gaming', 'ui', etc.
    metadata = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_language = relationship("Language", foreign_keys=[source_language_id])
    target_language = relationship("Language", foreign_keys=[target_language_id])
    
    __table_args__ = (
        Index('idx_translation_memory_languages', 'source_language_id', 'target_language_id'),
        Index('idx_translation_memory_quality', 'quality_score'),
    )