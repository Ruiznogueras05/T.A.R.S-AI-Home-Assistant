import openai
import pyaudio
import wave

# Set your OpenAI API Key
API_KEY = "YOUR_OPENAI_API_KEY"

# Audio recording settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100  # Whisper API works best with 16kHz or 44.1kHz audio
CHUNK = 1024
RECORD_SECONDS = 5  # Adjust as needed
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

def record_audio():
    """Records audio and saves it to a .wav file."""
    audio = pyaudio.PyAudio()
    
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    print("Recording...")
    frames = []
    
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    print("Recording complete.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio to a file
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return WAVE_OUTPUT_FILENAME

def transcribe_audio(filename):
    """Sends the recorded audio file to Whisper API for transcription."""
    with open(filename, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file, api_key=API_KEY)
    return transcript["text"]

if __name__ == "__main__":
    # Step 1: Record audio after wake-word detection
    audio_file = record_audio()

    # Step 2: Send it to Whisper for transcription
    print("Transcribing...")
    text = transcribe_audio(audio_file)

    # Step 3: Print the transcribed text
    print(f"Transcription: {text}")
