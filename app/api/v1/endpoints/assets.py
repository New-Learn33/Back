from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.asset_library_service import create_asset_profile, get_asset_profiles, delete_asset_profile

router = APIRouter()


@router.post("/upload")
async def upload_asset(
    file: UploadFile = File(...),
    category_id: int = Form(...),
    name: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        content = await file.read()

        profile = create_asset_profile(
            db=db,
            user_id=current_user.id,
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
def list_assets(
    category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        result = get_asset_profiles(db=db, user_id=current_user.id, category_id=category_id)

        return {
            "success": True,
            "message": "에셋 목록 조회 성공",
            "data": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에셋 조회 중 오류 발생: {str(e)}")


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        deleted = delete_asset_profile(db=db, asset_id=asset_id, user_id=current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="에셋을 찾을 수 없습니다.")
        return {
            "success": True,
            "message": "에셋 삭제 성공",
            "data": {"id": asset_id},
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"에셋 삭제 중 오류 발생: {str(e)}")
