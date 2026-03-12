from fastapi.responses import JSONResponse

# 공통 에러 응답 형식
def error_response(status_code: int, error_code: str, message: str):
    return JSONResponse(
        status_code=status_code,
        content={
            "errorCode": error_code,
            "message": message,
            "result": None
        }
    )