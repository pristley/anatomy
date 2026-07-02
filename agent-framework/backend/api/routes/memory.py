from fastapi import APIRouter

router = APIRouter()


@router.get('/semantic')
def semantic_list():
    return []


@router.get('/search')
def search(q: str):
    return {"query": q, "results": []}
