from fastapi import APIRouter, HTTPException
from .config import settings
from .pipeline import pipeline
from .schemas import CapitalRequest, CapitalResponse

router = APIRouter()

@router.post(
    "/capital",
    response_model=CapitalResponse,
    summary="Отримати столицю країни",
    tags=["capital"]
)
async def get_capital(req: CapitalRequest):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    resp = pipeline.invoke({"country": req.country})
    return CapitalResponse(country=req.country, capital=resp.content)
