from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # e.g., MATH, SCI, ENG
    description = Column(Text)
    icon = Column(String(255))  # URL to subject icon
    color = Column(String(7))  # Hex color code
    is_active = Column(Boolean, default=True)
    order = Column(Integer, default=0)  # Display order
    
    # Relationships
    contents = relationship("Content", back_populates="subject", cascade="all, delete-orphan")
    curriculums = relationship("Curriculum", cascade="all, delete-orphan")