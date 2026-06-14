from sqlalchemy import Column, Integer, String
from ..db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
