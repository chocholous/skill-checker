"""Categories router — GEN + APF reference data."""

from fastapi import APIRouter

from sim_core import GEN_CATEGORIES, APF_CATEGORIES, ALL_CATEGORIES

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories():
    """Return all GEN + APF categories."""
    return {
        "gen": {
            cat_id: {**cat, "id": cat_id, "type": "GEN"}
            for cat_id, cat in GEN_CATEGORIES.items()
        },
        "apf": {
            cat_id: {**cat, "id": cat_id, "type": "APF"}
            for cat_id, cat in APF_CATEGORIES.items()
        },
        "total": len(ALL_CATEGORIES),
    }
