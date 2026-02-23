"""Categories router — 5-category taxonomy reference data."""

from fastapi import APIRouter

from sim_core import CATEGORY_GROUPS, ALL_CATEGORIES

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
def get_categories():
    """Return all 5 category groups dynamically from CATEGORY_GROUPS."""
    groups = {}
    for group_key, group in CATEGORY_GROUPS.items():
        groups[group_key.lower()] = {
            "name": group["name"],
            "default_models": group["default_models"],
            "categories": {
                cat_id: {**cat, "id": cat_id, "type": group_key}
                for cat_id, cat in group["categories"].items()
            },
        }
    return {
        "groups": groups,
        "total": len(ALL_CATEGORIES),
    }
