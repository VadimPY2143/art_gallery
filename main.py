from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import shutil
import io
import aiofiles
from starlette.testclient import TestClient
from PIL import Image
app = FastAPI()

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_FILE_TYPES = ["image/jpeg", "image/png"]


@app.get('/')
def welcome():
    return {'message': 'Welcome to Art Gallery!'}


def resize_image(image_data: bytes, max_size: tuple = (800, 600)) -> bytes:
    with io.BytesIO(image_data) as img_byte_stream:
        with Image.open(img_byte_stream) as img:
            img.thumbnail(max_size)
            img_byte_array = io.BytesIO()
            img.save(img_byte_array, format=img.format if img.format else 'JPEG')
            return img_byte_array.getvalue()

async def process_image(file_path: str):
    async with aiofiles.open(file_path, "rb") as file:
        data = await file.read()
        resized_image = resize_image(data)

    async with aiofiles.open(file_path, "wb") as file:
        await file.write(resized_image)


@app.post("/upload-image/")
async def upload_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_location = f'photos/{file.filename}'
    print(file.content_type)
    if file.file.__sizeof__() > MAX_FILE_SIZE:
        background_tasks.add_task(process_image, file_location)
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail="Недопустимий формат файлу")
    else:
        with open(f"photos/{file.filename}", "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            return {'message': 'Файл успішно завантажено'}


client = TestClient(app)


def test_upload_photo():
    with open("photos/29_main-v1616786484.jpeg", "rb") as file:
        response = client.post(
            "/upload-image/",
            files={"file": file}
        )
    assert response.status_code == 200, response.status_code
    assert response.json().get("message") == "Файл успішно завантажено"


