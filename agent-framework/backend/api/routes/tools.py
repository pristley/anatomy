from fastapi import APIRouter

router = APIRouter()


@router.get('/')
def list_tools():
    # placeholder: should return registered tools
    return []
