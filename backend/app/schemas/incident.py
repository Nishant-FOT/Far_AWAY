from pydantic import BaseModel


class IncidentBase(BaseModel):
    description: str


class IncidentCreate(IncidentBase):
    pass


class Incident(IncidentBase):
    id: int

    class Config:
        orm_mode = True
