import pvporcupine
import pyaudio
import struct

# Replace "YOUR_ACCESS_KEY" with your actual Picovoice access key
ACCESS_KEY = "YOUR_ACCESS_KEY"

# Path to your custom wake-word model file
WAKE_WORD_PATH = "Project_Software/wake_word/hey_tars.ppn"

# Initialize Porcupine with the custom wake word
porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_PATH])  

# Set up the audio stream
pa = pyaudio.PyAudio()
audio_stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length
)

print("Listening for 'Hey TARS'...")

try:
    while True:
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print("Wake word detected! Activating TARS...")

except KeyboardInterrupt:
    print("\nStopping wake-word detection.")

finally:
    audio_stream.close()
    pa.terminate()
    porcupine.delete()
