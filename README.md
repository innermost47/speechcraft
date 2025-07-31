# SpeechCraft

A FastAPI service for audio transcription and translation using OpenAI's Whisper model with CUDA support.

## Features

- **Audio transcription** from uploaded files (MP3, WAV, WebM)
- **Direct YouTube audio processing** with automatic download
- **Real-time translation** to English using Whisper's built-in translation
- **SRT subtitle generation** with precise timestamps
- **CUDA acceleration** for faster processing
- **Multiple output formats** (text, SRT)
- **WhatsApp audio transcription** for chat exports with advanced filtering options

## Installation

### Prerequisites

- Python 3.10
- NVIDIA GPU with CUDA support
- FFmpeg installed and in PATH

### Quick Setup

1. **Clone and setup environment:**

```bash
git clone https://github.com/innermost47/speechcraft.git
cd speechcraft
```

2. **Run installation script:**

```bash
# Windows
install.bat

# Linux/Mac
./install.sh
```

3. **Configure environment:**

Create a `.env` file from `env.example.txt`:

```env
WHISPER_MODEL=large-v2
WHISPER_API_PORT=8001
WHISPER_API_HOST=127.0.0.1
```

- Available Models
  - `tiny` - Fastest, lowest quality
  - `base` - Good balance for testing
  - `small` - Better quality
  - `medium` - High quality
  - `large-v2` - Best quality (recommended for production)

4. **Start the server:**

```bash
python main.py
```

## API Endpoints

### 1. Transcribe Audio File

**POST** `/transcribe`

Upload an audio file and get transcription.

```bash
curl -X POST "http://127.0.0.1:8001/transcribe" \
  -F "file=@audio.mp3" \
  -F "file_format=mp3" \
  -F "output_format=srt" \
  -F "task=transcribe" \
  -F "save_file=true"
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

## WhatsApp Chat Transcription

The `whatsapp_to_txt.py` script processes WhatsApp chat exports and transcribes all audio messages using Whisper. It supports both French and English WhatsApp exports.

### Basic Usage

```bash
# Basic usage
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio"

# With custom output file
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -o transcribed_chat.txt

# With specific Whisper model
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -m large
```

### Advanced Options

```bash
# Start from a specific line number
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -l 500

# Start from a specific date (DD/MM/YYYY or DD/MM/YY)
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -d "15/09/2024"

# Start from date with short year format
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -d "15/09/24"

# Combine multiple options
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -d "01/01/2024" -m large -o "from_january.txt"

# Using environment variable for model
export WHISPER_MODEL=medium
python whatsapp_to_txt.py whatsapp_export.txt "WhatsApp Audio" -l 1000
```

### Parameters

- `export_file`: WhatsApp chat export file (.txt)
- `audio_dir`: Directory containing the audio files (.opus)
- `-o, --output`: Output file (default: conversation_transcribed.txt)
- `-m, --model`: Whisper model to use (tiny/base/small/medium/large)
- `-l, --start-line`: Start transcription from specific line number
- `-d, --start-date`: Start transcription from specific date (DD/MM/YYYY or DD/MM/YY)

### How it works

1. **Export your WhatsApp chat** including media files
2. **Organize files**: Place the text export and audio folder in your project directory
3. **Run the script**: It will:
   - Keep all text messages unchanged
   - Find audio messages in the format: `PTT-YYYYMMDD-WA####.opus (file attached)` or `PTT-YYYYMMDD-WA####.opus (fichier joint)`
   - Transcribe each audio file using Whisper
   - Replace the filename with: `Transcription of audio file [filename]: [transcribed text]`
   - Skip lines before the specified start line or date (if provided)

### Use Cases for Start Options

- **Resume interrupted transcription**: Use `-l` to start from where it stopped
- **Process recent messages only**: Use `-d` to transcribe from a specific date
- **Partial conversation analysis**: Focus on specific time periods
- **Large chat optimization**: Process conversations in chunks

### File Structure

```
your_project/
├── whatsapp_to_txt.py
├── whatsapp_export.txt           # Your chat export
├── WhatsApp Audio/               # Audio files folder
│   ├── PTT-20240901-WA0000.opus
│   ├── PTT-20240901-WA0001.opus
│   └── ...
└── conversation_transcribed.txt  # Output file
```

### Supported Audio Formats

- `.opus` (WhatsApp default)
- `.m4a`, `.mp3`, `.wav`, `.ogg` (alternative formats)

### Language Support

The script automatically detects and handles:

- **French WhatsApp exports**: `PTT-YYYYMMDD-WA####.opus (fichier joint)`
- **English WhatsApp exports**: `PTT-YYYYMMDD-WA####.opus (file attached)`

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
- For WhatsApp transcription, `base` or `small` models are usually sufficient for voice messages
- Use start line/date options to process large conversations in manageable chunks

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

### WhatsApp Export Issues

- Ensure audio files are in the correct directory
- Check that the export format matches the expected pattern
- Verify file permissions for reading audio files
- For path issues on Windows, avoid trailing backslashes: use `"folder"` not `"folder\"`
- Use start line option to resume if transcription fails partway through

## License

MIT License
