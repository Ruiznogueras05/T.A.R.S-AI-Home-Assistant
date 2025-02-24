import openai
import pyaudio
import wave
import webrtcvad
import struct
import os

# OpenAI API Key
API_KEY = "OPEN API KEY GOES HERE"

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Lower rate works better with voice detection
CHUNK = 1024
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the script's directory
WAVE_OUTPUT_FILENAME = os.path.join(SCRIPT_DIR, "recorded_audio.wav")

# Initialize WebRTC Voice Activity Detection (VAD)
vad = webrtcvad.Vad()
vad.set_mode(2)  # Sensitivity: 0 (least aggressive) to 3 (most aggressive)

def is_speech(frame, sample_rate):
    """Checks if a frame contains speech using WebRTC VAD."""
    return vad.is_speech(frame, sample_rate)

def record_audio():
    """Records audio until silence is detected using WebRTC VAD."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print("Listening for speech...")
    frames = []
    silence_threshold = 40  # Lower value stops recording faster
    silence_count = 0

    # Ensure frame size is 30ms
    frame_duration = 30  # in ms
    frame_size = int(RATE * (frame_duration / 1000))  # Number of samples per frame

    # Adjust VAD Sensitivity (0 = least aggressive, 3 = most aggressive)
    vad.set_mode(1)

    while True:
        data = stream.read(frame_size, exception_on_overflow=False)
        frames.append(data)

        # Check if speech is detected
        if vad.is_speech(data, RATE):
            silence_count = 0  # Reset silence counter
        else:
            silence_count += 1  # Increase silence counter

        # Stop recording if silence persists for a while
        if silence_count > silence_threshold:
            break

    print("Silence detected. Stopping recording.")

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded audio
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return WAVE_OUTPUT_FILENAME


def transcribe_audio(filename):
    """Sends the recorded audio file to Whisper API for transcription and deletes it after."""
    client = openai.OpenAI(api_key=API_KEY)

    with open(filename, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    # Delete the audio file after successful transcription
    os.remove(filename)
    print(f"Deleted {filename} after transcription.")

    return transcript.text

if __name__ == "__main__":
    # Start recording and transcribing
    audio_file = record_audio()
    print("Transcribing...")
    text = transcribe_audio(audio_file)
    print(f"Transcription: {text}")
