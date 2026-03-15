from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.asset_library_service import create_asset_profile, get_asset_profiles

router = APIRouter()

@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    category_id: int = Form(...),
    name: str | None = Form(None),
):
    try:
        content = await file.read()

        profile = create_asset_profile(
            file_bytes=content,
            original_filename=file.filename,
            category_id=category_id,
            asset_name=name,
        )

        return {
            "success": True,
            "message": "에셋 업로드 및 메타데이터 생성 완료",
            "data": profile,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에셋 처리 중 오류 발생: {str(e)}")


@router.get("")
def list_assets(category_id: int | None = None):
    try:
        result = get_asset_profiles(category_id)

        return {
            "success": True,
            "message": "에셋 목록 조회 성공",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에셋 조회 중 오류 발생: {str(e)}")