from pydantic import BaseModel

class CapitalRequest(BaseModel):
    country: str

class CapitalResponse(BaseModel):
    country: str
    capital: str
