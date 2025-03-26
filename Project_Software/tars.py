import pvporcupine
import pyaudio
import struct
import wave
import webrtcvad
import openai
import os

# == CONFIG ==
# ACCESS_KEY = "picovoice api key"
OPENAI_API_KEY = "open ai api key"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# WAKE_WORD_PATH = os.path.join(SCRIPT_DIR, "wake_word", "mac_hey_tars.ppn") # Swap to raspberry pi version later
AUDIO_PATH = os.path.join(SCRIPT_DIR, "recorded_audio.wav")

# == AUDIO CONFIG ==
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024    

# == SETUP == 
vad = webrtcvad.Vad()
vad.set_mode(1) # Sensitivity: 0 (least aggressive) to 3 (most aggressive)

def is_speech(frame, sample_rate):
    """Check if a frame contains speech using WebRTC VAD."""
    return vad.is_speech(frame, sample_rate)

def record_audio():
    """Records audio until silence is detected using WebRTC VAD."""
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    print("Listening for speech...")
    frames = []
    silence_threshold = 40 # Lower value stops recording faster
    silence_count = 0
    frame_duration = 30 # ms
    frame_size = int(RATE * (frame_duration / 1000))

    while True:
        data = stream.read(frame_size, exception_on_overflow=False)
        frames.append(data)
        if is_speech(data, RATE):
            silence_count = 0
        else:
            silence_count += 1
        if silence_count > silence_threshold:
            break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    with wave.open(AUDIO_PATH, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return AUDIO_PATH

def transcribe_audio(file_path):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    with open(file_path, "rb") as f:
        transcription = client.audio.transcriptions.create(model="whisper-1", file=f)
    os.remove(file_path)
    print("Audio file detected.")
    return transcription.text

# == MAIN WAKE WORD LOOP == (temporarily without wake word)
# porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_PATH])
# pa = pyaudio.PyAudio()
# stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)

print("TARS is online. Press ENTER to speak...")

try: 
    while True:

        input("Press Enter to activate TARS...")

        audio_file = record_audio()
        print("Transcribing...")
        text = transcribe_audio(audio_file)
        print(f"You said: {text}")
        # pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        # pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        # keyword_index = porcupine.process(pcm)
        # if keyword_index >= 0:
        #     print("Wake word detected.")
        #     audio_file = record_audio()
        #     print("Transcribing...")
        #     text = transcribe_audio(audio_file)
        #     print(f"You said: {text}")

except KeyboardInterrupt:
    print("\n TARS interrupted (Ctrl+C).")
# finally:
#     stream.close()
#     pa.terminate()
#     porcupine.delete()