import edge_tts
import asyncio
import io

async def test_tts():
    text = "Hello, this is a test of the audio system."
    voice = "en-US-AriaNeural"
    communicate = edge_tts.Communicate(text, voice)
    
    print(f"Generating audio for: '{text}' with voice: {voice}")
    
    try:
        mp3_fp = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_fp.write(chunk["data"])
        
        size = mp3_fp.tell()
        print(f"Success! Generated {size} bytes of audio.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tts())
