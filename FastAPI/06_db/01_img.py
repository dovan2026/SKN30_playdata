# uv add python-multipart Pillow
# pip install python-multipart Pillow
# 실행 : uvicorn img:app --reload

from fastapi import FastAPI, File, UploadFile, Body
import os
import shutil
from PIL import Image
import io
from fastapi.responses import StreamingResponse

app = FastAPI(title="이미지 업로드")

# 파일 저장 경로
UPLOAD_DIR = "upload_images"

os.makedirs(UPLOAD_DIR, exist_ok=True)

# root -> 서버 가동중
@app.get("/")
def root():
    return "서버 가동중"

# 1. 이미지 업로드 받아서 단순 저장
@app.post("/upload/image")
async def upload_image(file: UploadFile= File(...)):
    save_path = UPLOAD_DIR + "/" + file.filename
    print("이 경로에 저장이 됩니다. :", save_path)
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"response": f"{save_path}에 저장되었습니다. "}


# 2. 이미지를 업로드 받아서 흑백으로 변환 후 리턴
@app.post("/convert-to-grayscale")
async def convert_image(file: UploadFile= File(...)):
    image = Image.open(file.file).convert("L") # 이미지 를 8비트 그레이스케일로 변환
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0) # 스트림 시작 부분으로 이동
    
    # 메모리에 저장된 JPEG 데이터를 클라이언트에 전송
    return StreamingResponse(img_byte_arr, media_type="image/jpeg")  

