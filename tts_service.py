import os
import re
import asyncio
from pathlib import Path
import edge_tts

TEMP_DIR = Path("temp_audio")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Default natural voices:
# "en-US-JennyNeural", "en-US-GuyNeural", "en-IN-NeerjaNeural", "en-GB-SoniaNeural"
DEFAULT_VOICE = "en-US-JennyNeural"

def split_text_into_chunks(text: str, max_chars: int = 1500) -> list[str]:
    """
    Splits long text into manageable chunks respecting paragraph and sentence boundaries.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 1 <= max_chars:
            current_chunk = f"{current_chunk}\n{paragraph}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If a single paragraph is excessively long, split by sentences
            if len(paragraph) > max_chars:
                sentences = re.split(r'(?<=[.!?]) +', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= max_chars:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = sentence.strip()
            else:
                current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

async def convert_text_to_audio_long(
    text: str,
    output_filepath: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
    pitch: str = "+0Hz"
) -> str:
    """
    Synthesizes long text chunk-by-chunk and merges the MP3 frames directly
    without relying on pydub or audioop (fully compatible with Python 3.13+).
    """
    chunks = split_text_into_chunks(text, max_chars=1800)
    
    # Direct single-pass stream if the text is short
    if len(chunks) == 1:
        communicate = edge_tts.Communicate(
            text=chunks[0],
            voice=voice,
            rate=rate,
            pitch=pitch
        )
        await communicate.save(output_filepath)
        return output_filepath

    # Multi-chunk synthesis for long text (~30 mins)
    temp_chunk_paths = []
    try:
        for i, chunk in enumerate(chunks):
            chunk_file = f"{output_filepath}_part{i}.mp3"
            communicate = edge_tts.Communicate(
                text=chunk,
                voice=voice,
                rate=rate,
                pitch=pitch
            )
            await communicate.save(chunk_file)
            temp_chunk_paths.append(chunk_file)

        # Concatenate raw MP3 bitstreams directly
        with open(output_filepath, "wb") as outfile:
            for part in temp_chunk_paths:
                with open(part, "rb") as infile:
                    outfile.write(infile.read())

        return output_filepath

    finally:
        # Clean up chunk fragments
        for cf in temp_chunk_paths:
            if os.path.exists(cf):
                try:
                    os.remove(cf)
                except OSError:
                    pass