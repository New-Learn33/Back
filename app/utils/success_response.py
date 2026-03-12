from fastapi.responses import JSONResponse

def success_response(data=None, message="요청 성공", status_code=200):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data if data is not None else {}
        }
    )