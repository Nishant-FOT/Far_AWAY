from pydantic import BaseModel


class AssessmentBase(BaseModel):
    severity: str
    risk: str
    recommendations: str | None = None


class AssessmentCreate(AssessmentBase):
    pass


class Assessment(AssessmentBase):
    id: int

    class Config:
        orm_mode = True
