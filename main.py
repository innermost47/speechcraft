from pydub import AudioSegment
from io import BytesIO
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import whisper
import torch
from fastapi import UploadFile
from fastapi import FastAPI, APIRouter
from fastapi.responses import FileResponse
import uvicorn
import os
import uuid
import shutil
import time
import yt_dlp
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

app = FastAPI()
router = APIRouter()

OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "./outputs"))
OUTPUT_DIR.mkdir(exist_ok=True)

model = whisper.load_model(
    os.environ.get("WHISPER_MODEL"),
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu"),
)
executor = ThreadPoolExecutor()


class TranscribeRequest(BaseModel):
    output_format: str = "text"
    task: str = "transcribe"
    save_file: bool = True


class YouTubeRequest(BaseModel):
    url: str
    output_format: str = "text"
    save_file: bool = True


class YouTubeTranslateRequest(BaseModel):
    url: str
    output_format: str = "text"
    save_file: bool = True


class TranslateRequest(BaseModel):
    output_format: str = "text"
    save_file: bool = True


async def convert_audio_to_wav(file: UploadFile, file_format: str):
    try:
        file_data = await file.read()
        audio_file = BytesIO(file_data)
        audio_file.seek(0)
        if file_format == "webm" or file_format == "mp3":
            audio = (
                AudioSegment.from_file(audio_file).set_frame_rate(16000).set_channels(1)
            )
        elif file_format == "wav":
            audio = (
                AudioSegment.from_file(audio_file, format="wav")
                .set_frame_rate(16000)
                .set_channels(1)
            )
        else:
            raise ValueError("Format audio non supporté")

        wav_file = BytesIO()
        audio.export(wav_file, format="wav")
        wav_file.seek(0)
        return wav_file

    except Exception as e:
        print(f"An error occurred while trying to convert audio to wav: {e}")
        raise e


def transcribe_audio_sync(
    wav_file: BytesIO, output_format: str = "text", task: str = "transcribe"
):
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav_file:
            temp_wav_file.write(wav_file.read())
            temp_wav_file.flush()

            result = model.transcribe(
                temp_wav_file.name, word_timestamps=True, task=task
            )

            if output_format == "srt":
                content = generate_srt(result["segments"])
            elif output_format == "vtt":
                content = generate_vtt(result["segments"])
            elif output_format == "sbv":
                content = generate_sbv(result["segments"])
            else:
                content = result["text"]

            return {"content": content, "segments": result.get("segments", [])}

        os.unlink(temp_wav_file.name)

    except Exception as e:
        print(f"An error occurred while trying to transcribe audio: {e}")
        raise e


async def transcribe_audio(
    file: UploadFile,
    file_format: str,
    output_format: str = "text",
    task: str = "transcribe",
):
    async with asyncio.Lock():
        loop = asyncio.get_event_loop()
        wav_file = await convert_audio_to_wav(file, file_format)
        return await loop.run_in_executor(
            executor, transcribe_audio_sync, wav_file, output_format, task
        )


def save_content_to_file(content: str, filename: str, output_format: str) -> str:
    if output_format in ["srt", "vtt", "sbv"]:
        file_path = OUTPUT_DIR / f"{filename}.{output_format}"
    else:
        file_path = OUTPUT_DIR / f"{filename}.txt"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return str(file_path)


def generate_filename(
    original_name: str = None, url: str = None, task: str = "transcribe"
) -> str:
    timestamp = int(time.time())

    if url:
        video_id = extract_youtube_id(url)
        if video_id:
            return f"youtube_{video_id}_{task}_{timestamp}"
        else:
            return f"youtube_{task}_{timestamp}"
    elif original_name:
        clean_name = "".join(c for c in original_name if c.isalnum() or c in "._-")
        name_without_ext = (
            clean_name.rsplit(".", 1)[0] if "." in clean_name else clean_name
        )
        return f"{name_without_ext}_{task}_{timestamp}"
    else:
        return f"audio_{task}_{timestamp}"


def extract_youtube_id(url: str) -> str:
    try:
        if "youtube.com" in url:
            if "v=" in url:
                return url.split("v=")[1].split("&")[0]
        elif "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
    except:
        pass
    return None


def generate_srt(segments):
    srt_content = ""
    for i, segment in enumerate(segments, 1):
        start_time = format_timestamp_srt(segment["start"])
        end_time = format_timestamp_srt(segment["end"])
        text = segment["text"].strip()

        srt_content += f"{i}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"

    return srt_content


def generate_vtt(segments):
    vtt_content = "WEBVTT\n\n"

    for segment in segments:
        start_time = format_timestamp_vtt(segment["start"])
        end_time = format_timestamp_vtt(segment["end"])
        text = segment["text"].strip()

        vtt_content += f"{start_time} --> {end_time}\n"
        vtt_content += f"{text}\n\n"

    return vtt_content


def generate_sbv(segments):
    sbv_content = ""

    for segment in segments:
        start_time = format_timestamp_sbv(segment["start"])
        end_time = format_timestamp_sbv(segment["end"])
        text = segment["text"].strip()

        sbv_content += f"{start_time},{end_time}\n"
        sbv_content += f"{text}\n\n"

    return sbv_content


def format_timestamp_srt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"


def format_timestamp_vtt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


def format_timestamp_sbv(seconds):
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"


async def download_youtube_audio(url: str):
    try:
        temp_dir = tempfile.mkdtemp()
        temp_filename = f"yt_audio_{uuid.uuid4().hex}"

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(temp_dir, f"{temp_filename}.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        wav_path = os.path.join(temp_dir, f"{temp_filename}.wav")

        time.sleep(0.5)

        audio = AudioSegment.from_wav(wav_path)
        audio = audio.set_frame_rate(16000).set_channels(1)

        wav_file = BytesIO()
        audio.export(wav_file, format="wav")
        wav_file.seek(0)

        shutil.rmtree(temp_dir, ignore_errors=True)

        return wav_file

    except Exception as e:
        print(f"YouTube download error: {e}")
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass
        raise e


@app.post("/main")
async def main(file: UploadFile, file_format: str):
    result = await transcribe_audio(file, file_format)

    filename = generate_filename(file.filename)
    file_path = save_content_to_file(result["content"], filename, "text")

    return {"transcription": result["content"], "file_saved": file_path}


@app.post("/transcribe")
async def transcribe_endpoint(
    file: UploadFile, file_format: str, request: TranscribeRequest
):
    result = await transcribe_audio(
        file, file_format, request.output_format, request.task
    )

    response = {"transcription": result["content"]}

    if request.save_file:
        filename = generate_filename(file.filename, task=request.task)
        file_path = save_content_to_file(
            result["content"], filename, request.output_format
        )
        response["file_saved"] = file_path

    return response


@app.post("/transcribe-youtube")
async def transcribe_youtube(request: YouTubeRequest):
    async with asyncio.Lock():
        loop = asyncio.get_event_loop()
        wav_file = await download_youtube_audio(request.url)
        result = await loop.run_in_executor(
            executor,
            transcribe_audio_sync,
            wav_file,
            request.output_format,
            "transcribe",
        )

    response = {"transcription": result["content"]}

    if request.save_file:
        filename = generate_filename(url=request.url, task="transcribe")
        file_path = save_content_to_file(
            result["content"], filename, request.output_format
        )
        response["file_saved"] = file_path

    return response


@app.post("/translate")
async def translate_endpoint(
    file: UploadFile, file_format: str, request: TranslateRequest
):
    result = await transcribe_audio(
        file, file_format, request.output_format, task="translate"
    )

    response = {"translation": result["content"]}

    if request.save_file:
        filename = generate_filename(file.filename, task="translate")
        file_path = save_content_to_file(
            result["content"], filename, request.output_format
        )
        response["file_saved"] = file_path

    return response


@app.post("/translate-youtube")
async def translate_youtube(request: YouTubeTranslateRequest):
    async with asyncio.Lock():
        loop = asyncio.get_event_loop()
        wav_file = await download_youtube_audio(request.url)
        result = await loop.run_in_executor(
            executor,
            transcribe_audio_sync,
            wav_file,
            request.output_format,
            "translate",
        )

    response = {"translation": result["content"]}

    if request.save_file:
        filename = generate_filename(url=request.url, task="translate")
        file_path = save_content_to_file(
            result["content"], filename, request.output_format
        )
        response["file_saved"] = file_path

    return response


@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUT_DIR / filename
    if file_path.exists():
        return FileResponse(file_path, filename=filename)
    else:
        return {"error": "File not found"}


@app.get("/files")
async def list_files():
    files = []
    for file_path in OUTPUT_DIR.iterdir():
        if file_path.is_file():
            files.append(
                {
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created": file_path.stat().st_ctime,
                }
            )
    return {"files": files}


def main():
    uvicorn.run(
        app,
        host=os.environ.get("WHISPER_API_HOST"),
        port=int(os.environ.get("WHISPER_API_PORT")),
    )


if __name__ == "__main__":
    main()
