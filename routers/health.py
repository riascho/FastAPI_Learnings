from fastapi import APIRouter

router = APIRouter(tags=["health"])


# route decorator for .HTTP method and (path)
@router.get("/")
def root():
    return {"message": "Hi!"}


@router.get("/health")
def health_check():
    return {"status": "ok"}
