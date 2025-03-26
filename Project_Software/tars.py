import pvporcupine
import pyaudio
import struct
import wave
import webrtcvad
import openai
import requests
import os
import re
import warnings
from datetime import datetime

# == CONFIG ==
# ACCESS_KEY = "picovoice api key"
OPENAI_API_KEY = "openai api key"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# WAKE_WORD_PATH = os.path.join(SCRIPT_DIR, "wake_word", "mac_hey_tars.ppn") # Swap to raspberry pi version later
AUDIO_PATH = os.path.join(SCRIPT_DIR, "recorded_audio.wav")
WEATHER_API_KEY = "openweather api key"

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

def get_weather(city="New York"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=imperial"

    try:
        response = requests.get(url)
        data = response.json()

        if data["cod"] != 200:
            return f"Weather info unavailable for {city} right now."

        weather = data["weather"][0]["description"].capitalize()
        temperature = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])

        return f"{weather}, {temperature}°F (feels like {feels_like}°F)"
    except Exception:
        return "Sorry, I'm unable to retrieve the weather right now."
    
# def extract_city(user_input):
#     """Extracts city name from user input, defaults to NYC."""
#     match = re.search(r"in ([A-Za-z\s]+)", user_input, re.IGNORECASE)
#     if match:
#         return match.group(1).strip()
#     return "New York"

def classify_weather_intent(user_input):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    classification_prompt = (
        "Your job is to detect if the user's input is a request for weather information.\n"
        "Keep your responses concise (1-2 short sentences).\n\n"
        "Respond ONLY with one of the following:\n\n"
        "- WEATHER_REQUEST(city_name)\n"
        "- NOT_WEATHER\n\n"
        "Examples:\n"
        "Input: 'What's the weather in New York?'\n"
        "Output: WEATHER_REQUEST(New York)\n\n"
        "Input: 'Can you tell me the temperature in San Juan?'\n"
        "Output: WEATHER_REQUEST(San Juan)\n\n"
        "Input: 'Tell me a joke'\n"
        "Output: NOT_WEATHER\n\n"
        "Now classify this:\n"
        f"{user_input}"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": classification_prompt}]
    )

    return response.choices[0].message.content.strip()

def get_tars_response(user_input):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    now = datetime.now()
    readable_time = now.strftime("%I:%M %p")
    readable_date = now.strftime("%A, %B %d, %Y")

    system_prompt = (
        f"You are TARS, the witty and intelligent robot from the movie Interstellar. "
        f"You respond in-character using dry humor and helpful insights.\n\n"
        f"Keep your responses concise (1-3 short sentences), while still maintaining your witty, in-character tone.\n\n"
        f"Here is the current date and time for your reference:\n"
        f"- Time: {readable_time}\n"
        f"- Date: {readable_date}\n\n"
        "If the user says something that involves controlling a smart home device, "
        "you must ONLY respond with the string: SMART_HOME. Do not say anything else.\n\n"
        "These are the smart devices the user has:\n"
        "- A lamp named 'Mesita' (controlled with eWeLink)\n"
        "- LED light strips (controlled with the Lotus Lantern app)\n\n"
        "Examples of valid smart home commands include:\n"
        "- 'Turn on Mesita'\n"
        "- 'Turn off Mesita'\n"
        "- 'Switch off the lamp'\n"
        "- 'Make Mesita brighter'\n"
        "- 'Dim the lamp'\n"
        "- 'Turn on the LEDs'\n"
        "- 'Set the LED lights to red'\n"
        "- 'Make the room blue'\n"
        "- 'Change the LED color to purple'\n"
        "- 'Turn off the Lotus lights'\n"
        "- 'Set the LEDs to white'\n"
        "- 'Activate the lights in the room'\n"
        "- 'Switch off everything'\n"
        "- 'Turn off all the lights in my room'\n"
        "- 'Set the mood lighting'\n\n"
        "If the user says anything else — like a question, joke, philosophical musing, or request "
        "that isn't related to controlling Mesita or the LED strips — respond in character as TARS "
        "using your signature dry humor and logic."
    )

    chat_completion = client.chat.completions.create(
        model="gpt-4", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )

    return chat_completion.choices[0].message.content.strip()

# == MAIN WAKE WORD LOOP == (temporarily without wake word)

# porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_PATH])
# pa = pyaudio.PyAudio()
# stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)

print("\nTARS is online.\n")

try: 
    while True:

        input("Press Enter to activate TARS...\n")

        audio_file = record_audio()
        print("Transcribing...")
        text = transcribe_audio(audio_file)
        print("\n==============================\n")
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

        weather_classification = classify_weather_intent(text)

        if weather_classification.startswith("WEATHER_REQUEST("):
            city = weather_classification[len("WEATHER_REQUEST("):-1].strip() or "New York"
            weather_info = get_weather(city)

            weather_prompt = (
                f"You are TARS from Interstellar. A witty, intelligent robot with a dry sense of humor. "
                f"Respond in character using the following weather data for {city}:\n"
                f"{weather_info}\n\n"
                "Do NOT explain where you got the weather data from. Do NOT mention APIs or errors. "
                "If weather info is unavailable, make a clever joke or excuse about being a spaceship, not a weather station."
            )

            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": weather_prompt},
                    {"role": "user", "content": f"What's the weather like in {city}?"}
                ]
            )
            print("TARS:", response.choices[0].message.content.strip())
            print("\n==============================\n")

        else:
            response = get_tars_response(text)

            if response == "SMART_HOME":
                print("SMART_HOME command detected. (Control logic coming soon...)")
                print("TARS: I've asked CASE to do that for you.")
            else:
                print(f"TARS: {response}")

            print("\n==============================\n")
            

except KeyboardInterrupt:
    print("\n TARS interrupted (Ctrl+C).")
# finally:
#     stream.close()
#     pa.terminate()
#     porcupine.delete()