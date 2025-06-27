# SpeechCraft

A FastAPI service for audio transcription and translation using OpenAI's Whisper model with CUDA support.

## Features

- **Audio transcription** from uploaded files (MP3, WAV, WebM)
- **Direct YouTube audio processing** with automatic download
- **Real-time translation** to English using Whisper's built-in translation
- **SRT subtitle generation** with precise timestamps
- **CUDA acceleration** for faster processing
- **Multiple output formats** (text, SRT)

## Installation

### Prerequisites

- Python 3.8-3.11 (not 3.12)
- NVIDIA GPU with CUDA support
- FFmpeg installed and in PATH

### Quick Setup

1. **Clone and setup environment:**

```bash
git clone https://github.com/innermost47/speechcraft.git
cd whisper-api
python -m venv env
```

2. **Run installation script:**

```bash
# Windows
install.bat

# Linux/Mac
./install.sh
```

3. **Configure environment:**

```bash
cp env.example.txt .env
# Edit .env with your settings
```

4. **Start the server:**

```bash
python main.py
```

## Configuration

Create a `.env` file from `env.example.txt`:

```env
WHISPER_MODEL=large-v2
WHISPER_API_PORT=8001
WHISPER_API_HOST=127.0.0.1
```

### Available Models

- `tiny` - Fastest, lowest quality
- `base` - Good balance for testing
- `small` - Better quality
- `medium` - High quality
- `large-v2` - Best quality (recommended for production)

## API Endpoints

### 1. Transcribe Audio File

**POST** `/transcribe`

Upload an audio file and get transcription.

```bash
curl -X POST "http://127.0.0.1:8001/transcribe" \
  -F "file=@audio.mp3" \
  -F "file_format=mp3" \
  -F 'request={"output_format":"srt","task":"transcribe"}'
```

### 2. Translate Audio File

**POST** `/translate`

Upload an audio file and get English translation.

```bash
curl -X POST "http://127.0.0.1:8001/translate" \
  -F "file=@audio.mp3" \
  -F "file_format=mp3" \
  -F 'request={"output_format":"srt"}'
```

### 3. Transcribe YouTube Video

**POST** `/transcribe-youtube`

Process YouTube video directly from URL.

```bash
curl -X POST "http://127.0.0.1:8001/transcribe-youtube" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "output_format": "srt"}'
```

### 4. Translate YouTube Video

**POST** `/translate-youtube`

Download and translate YouTube video to English.

```bash
curl -X POST "http://127.0.0.1:8001/translate-youtube" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "output_format": "srt"}'
```

## Request Parameters

### File Endpoints

- `file`: Audio file (required)
- `file_format`: `mp3`, `wav`, or `webm` (required)
- `request`: JSON object with options

### YouTube Endpoints

- `url`: YouTube video URL (required)
- `output_format`: `text` or `srt` (default: `text`)

### Request Options

- `output_format`:
  - `text` - Plain text transcription
  - `srt` - Subtitle file format with timestamps
- `task` (transcribe endpoint only):
  - `transcribe` - Original language transcription
  - `translate` - Translate to English

## Response Format

### Text Output

```json
{
  "transcription": "Your transcribed text here..."
}
```

### SRT Output

```json
{
  "transcription": "1\n00:00:00,000 --> 00:00:03,000\nFirst subtitle line\n\n2\n00:00:03,000 --> 00:00:06,000\nSecond subtitle line\n\n"
}
```

## File Storage

All generated transcriptions and translations are automatically saved to the `outputs/` directory:

- **Text files**: `outputs/filename_transcribe_timestamp.txt`
- **SRT files**: `outputs/filename_transcribe_timestamp.srt`
- **YouTube files**: `outputs/youtube_videoid_transcribe_timestamp.srt`

### File Management Endpoints

**GET** `/files` - List all saved files

```bash
curl "http://127.0.0.1:8001/files"
```

**GET** `/download/{filename}` - Download a saved file

```bash
curl "http://127.0.0.1:8001/download/filename.srt" -O
```

### Response Format with File Saving

```json
{
  "transcription": "Your transcribed text here...",
  "file_saved": "./outputs/audio_transcribe_1234567890.srt"
}
```

## Supported Formats

### Input Audio Formats

- MP3
- WAV
- WebM
- Any format supported by FFmpeg

### Output Formats

- Plain text
- SRT (SubRip Subtitle format)

## Performance Tips

- Use `large-v2` model for best quality
- Enable CUDA for GPU acceleration
- For long videos, consider using smaller models (`medium`, `small`) for faster processing
- SRT generation includes word-level timestamps for precise subtitle timing

## Troubleshooting

### CUDA Issues

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

### FFmpeg Missing

- **Windows**: Download from https://ffmpeg.org/ and add to PATH
- **Linux**: `sudo apt install ffmpeg`
- **Mac**: `brew install ffmpeg`

### YouTube Download Failures

- Some videos may have DRM protection (warnings are normal)
- Try different video URLs if one fails
- Check internet connection for download issues

## License

MIT License
