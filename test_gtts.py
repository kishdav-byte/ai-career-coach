from gtts import gTTS
import io

def test_gtts():
    text = "Hello, this is a test of the Google Text to Speech system."
    try:
        tts = gTTS(text, lang='en')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        
        size = mp3_fp.tell()
        print(f"Success! Generated {size} bytes of audio.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gtts()
