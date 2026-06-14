from sqlalchemy import Column, Integer, String
from ..db.base import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String, nullable=False)
    risk = Column(String, nullable=False)
