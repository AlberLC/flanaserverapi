from fastapi import APIRouter, Response, status

router = APIRouter(tags=['ping'])


@router.get('/ping')
async def ping() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
