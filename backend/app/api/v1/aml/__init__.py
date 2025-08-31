from fastapi import APIRouter

from .customers import router as customers_router
from .transactions import router as transactions_router
from .screening import router as screening_router
from .reports import router as reports_router
from .cases import router as cases_router
from .monitoring import router as monitoring_router
from .data_import import router as data_import_router
from .pattern_analysis import router as pattern_analysis_router
from .ml_predictions import router as ml_predictions_router

# Create main AML router
router = APIRouter()

# Include sub-routers
router.include_router(customers_router, prefix="/customers", tags=["AML-Customers"])
router.include_router(transactions_router, prefix="/transactions", tags=["AML-Transactions"])
router.include_router(screening_router, prefix="/screening", tags=["AML-Screening"])
router.include_router(reports_router, prefix="/reports", tags=["AML-Reports"])
router.include_router(cases_router, prefix="/cases", tags=["AML-Cases"])
router.include_router(monitoring_router, prefix="/monitoring", tags=["AML-Monitoring"])
router.include_router(data_import_router, prefix="/import", tags=["AML-Import"])
router.include_router(pattern_analysis_router, prefix="/patterns", tags=["AML-Patterns"])
router.include_router(ml_predictions_router, prefix="/ml", tags=["AML-ML-Predictions"])

__all__ = ["router"]