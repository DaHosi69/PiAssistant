import whisper
import pyaudio
import wave
import os
import speech_recognition as sr
import requests
import time
import subprocess

# === Konfiguration ===
WAKE_WORD = "hey alex"
LLM_ENDPOINT = "http://localhost:5000/ask"  # Lokaler Server mit LLM (z. B. DeepSeek/Mistral)
RECORD_SECONDS = 5
AUDIO_FILE = "input.wav"

# === Wake Word-Erkennung (einfach) ===
def wait_for_wake_word():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    print(">> Warte auf Wake Word...")

    while True:
        with mic as source:
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio).lower()
            print(f"[Erkannt]: {text}")
            if WAKE_WORD in text:
                print(">> Wake Word erkannt!")
                return
        except:
            pass

# === Sprache aufnehmen ===
def record_audio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                    input=True, frames_per_buffer=CHUNK)

    print(">> Aufnahme läuft...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print(">> Aufnahme beendet.")
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(AUDIO_FILE, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

# === Sprache → Text (ASR via Whisper) ===
def transcribe_audio():
    model = whisper.load_model("base")
    result = model.transcribe(AUDIO_FILE)
    print(f">> Transkribiert: {result['text']}")
    return result["text"]

# === Anfrage an LLM senden ===
def ask_llm(prompt):
    try:
        response = requests.post(LLM_ENDPOINT, json={"prompt": prompt})
        answer = response.json().get("answer", "")
        print(f">> KI-Antwort: {answer}")
        return answer
    except Exception as e:
        print("Fehler bei LLM-Anfrage:", e)
        return "Entschuldigung, ich konnte keine Antwort erhalten."

# === Text in Sprache umwandeln ===
def speak(text):
    subprocess.run(["espeak", text])

# === Hauptablauf ===
def main():
    while True:
        wait_for_wake_word()
        record_audio()
        user_text = transcribe_audio()
        reply = ask_llm(user_text)
        speak(reply)

if __name__ == "__main__":
    main()
