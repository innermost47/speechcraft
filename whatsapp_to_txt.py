import os
import re
import whisper
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def parse_whatsapp_date(date_str):
    try:
        if len(date_str.split("/")[2]) == 2:
            return datetime.strptime(date_str, "%d/%m/%y")
        else:
            return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return None


def extract_date_from_line(line):
    date_patterns = [
        r"\[(\d{1,2}/\d{1,2}/\d{2,4}),",
        r"^(\d{1,2}/\d{1,2}/\d{2,4}),",
    ]

    for pattern in date_patterns:
        match = re.search(pattern, line)
        if match:
            return parse_whatsapp_date(match.group(1))
    return None


def should_start_processing(line_num, line_content, start_line, start_date):
    if start_line and line_num >= start_line:
        return True

    if start_date:
        line_date = extract_date_from_line(line_content)
        if line_date and line_date >= start_date:
            return True

    if not start_line and not start_date:
        return True

    return False


def load_whisper_model(model_size="base"):
    print(f"Loading whisper model '{model_size}'...")
    return whisper.load_model(model_size)


def find_audio_file(audio_filename, audio_dir):
    audio_path = Path(audio_dir) / audio_filename
    if audio_path.exists():
        return str(audio_path)

    base_name = audio_path.stem
    for ext in [".opus", ".m4a", ".mp3", ".wav", ".ogg"]:
        alt_path = Path(audio_dir) / f"{base_name}{ext}"
        if alt_path.exists():
            return str(alt_path)

    return None


def transcribe_audio(model, audio_path):
    try:
        print(f"Transcripting: {Path(audio_path).name}...")
        result = model.transcribe(audio_path, language="fr")
        return result["text"].strip()
    except Exception as e:
        return f"[Transcription error: {str(e)}]"


def process_whatsapp_export(
    export_file,
    audio_dir,
    output_file,
    model_size="base",
    start_line=None,
    start_date=None,
):
    model = load_whisper_model(model_size)

    audio_pattern = r"(PTT-\d+-WA\d+\.opus \([^)]+\))"

    with open(export_file, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    processed_lines = []
    processing_started = False
    skipped_lines = 0

    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            if processing_started:
                processed_lines.append(line)
            continue

        if not processing_started:
            if should_start_processing(line_num, line, start_line, start_date):
                processing_started = True
                if start_line:
                    print(f"Starting transcription from line {line_num}")
                elif start_date:
                    line_date = extract_date_from_line(line)
                    print(
                        f"Starting transcription from date {line_date.strftime('%d/%m/%Y') if line_date else 'unknown'}"
                    )
            else:
                skipped_lines += 1
                continue

        audio_match = re.search(audio_pattern, line)

        if audio_match:
            audio_filename = audio_match.group(1).replace(" (file attached)", "")
            audio_path = find_audio_file(audio_filename, audio_dir)

            if audio_path:
                transcription = transcribe_audio(model, audio_path)
                new_line = line.replace(
                    audio_match.group(1),
                    f"Transcription of audio file {audio_filename} (file attached): {transcription}",
                )
                processed_lines.append(new_line)
                print(f"✓ Transcribed: {audio_filename}")
            else:
                new_line = line.replace(
                    audio_match.group(1),
                    f"Transcription of audio file {audio_filename} (file attached): [Audio file not found]",
                )
                processed_lines.append(new_line)
                print(f"✗ Not found: {audio_filename}")
        else:
            processed_lines.append(line)

    if skipped_lines > 0:
        print(f"Skipped {skipped_lines} lines before starting transcription")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(processed_lines))

    print(f"\n✓ Processed export saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transcribe WhatsApp audio messages with Whisper"
    )

    parser.add_argument("export_file", help="WhatsApp export file (.txt)")

    parser.add_argument("audio_dir", help="Directory containing audio files")

    parser.add_argument(
        "-o",
        "--output",
        default="conversation_transcribed.txt",
        help="Output file (default: conversation_transcribed.txt)",
    )

    parser.add_argument(
        "-m",
        "--model",
        default=os.environ.get("WHISPER_MODEL", "base"),
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model to use (default: WHISPER_MODEL env var or 'base')",
    )

    parser.add_argument(
        "-l", "--start-line", type=int, help="Start transcription from this line number"
    )

    parser.add_argument(
        "-d",
        "--start-date",
        help="Start transcription from this date (format: DD/MM/YYYY or DD/MM/YY)",
    )

    args = parser.parse_args()

    if not os.path.exists(args.export_file):
        print(f"Error: {args.export_file} not found")
        exit(1)

    if not os.path.exists(args.audio_dir):
        print(f"Error: {args.audio_dir} not found")
        exit(1)

    start_date = None
    if args.start_date:
        start_date = parse_whatsapp_date(args.start_date)
        if not start_date:
            print(
                f"Error: Invalid date format '{args.start_date}'. Use DD/MM/YYYY or DD/MM/YY"
            )
            exit(1)
        print(f"Will start from date: {start_date.strftime('%d/%m/%Y')}")

    if args.start_line:
        print(f"Will start from line: {args.start_line}")

    print("Starting...")
    process_whatsapp_export(
        args.export_file,
        args.audio_dir,
        args.output,
        args.model,
        args.start_line,
        start_date,
    )
    print("Done!")
