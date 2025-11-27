import pyttsx3
import os

def test_pyttsx3():
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    print("Available voices:")
    for voice in voices:
        print(f" - {voice.name} ({voice.id})")
        
    # Try to find a male voice (Alex is standard on Mac)
    male_voice = None
    for voice in voices:
        if 'Alex' in voice.name:
            male_voice = voice.id
            break
            
    if male_voice:
        print(f"Testing male voice: {male_voice}")
        engine.setProperty('voice', male_voice)
        engine.save_to_file('Hello, this is a male voice test.', 'test_male.aiff')
        engine.runAndWait()
        
        if os.path.exists('test_male.aiff'):
            print(f"Success! Generated test_male.aiff ({os.path.getsize('test_male.aiff')} bytes)")
        else:
            print("Failed to generate file.")
    else:
        print("Could not find 'Alex' voice.")

if __name__ == "__main__":
    test_pyttsx3()
