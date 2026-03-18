from fastapi import APIRouter

from app.schemas.common import SuccessResponse
from app.services.readiness import evaluate_readiness

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/readiness", response_model=SuccessResponse)
def get_readiness() -> SuccessResponse:
    result = evaluate_readiness()
    return SuccessResponse(
        data={
            "ready": result.ready,
            "stage": result.stage,
            "summary": result.summary,
        }
    )
