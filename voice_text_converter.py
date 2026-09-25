"""
Voice-Text Converter Pro
------------------------
A professional mini AI tool built in pure Python that does two things:

1. TEXT -> VOICE   : Type or paste text, and the app speaks it out loud
                      and can save it as an .mp3 / .wav audio file.
2. VOICE -> TEXT   : Speak into your microphone (or load an audio file)
                      and the app converts your speech into text.

Libraries used (all Python):
    - tkinter                -> GUI (comes built-in with Python)
    - pyttsx3                -> offline Text-to-Speech engine
    - SpeechRecognition      -> Speech-to-Text engine
    - pyaudio                -> microphone access (needed by SpeechRecognition)

Author: Built for Muhammad Ayzaz Aslam
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

import pyttsx3
import speech_recognition as sr


# ----------------------------------------------------------------------
# Core engine wrapper class
# ----------------------------------------------------------------------
class VoiceTextEngine:
    """Wraps the TTS and STT engines so the GUI code stays clean."""

    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()

        # Default voice settings (can be changed from the GUI)
        self.set_rate(170)
        self.set_volume(1.0)

    # ---------------- TEXT -> VOICE ----------------
    def get_voices(self):
        return self.tts_engine.getProperty("voices")

    def set_voice(self, voice_id):
        self.tts_engine.setProperty("voice", voice_id)

    def set_rate(self, rate):
        self.tts_engine.setProperty("rate", rate)

    def set_volume(self, volume):
        self.tts_engine.setProperty("volume", volume)

    def speak(self, text):
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def save_to_file(self, text, filepath):
        self.tts_engine.save_to_file(text, filepath)
        self.tts_engine.runAndWait()

    # ---------------- VOICE -> TEXT ----------------
    def listen_from_microphone(self, timeout=6, phrase_time_limit=30):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
            audio = self.recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        return self._recognize(audio)

    def transcribe_file(self, filepath):
        with sr.AudioFile(filepath) as source:
            audio = self.recognizer.record(source)
        return self._recognize(audio)

    def _recognize(self, audio_data):
        # Uses Google's free Web Speech API (needs internet connection).
        return self.recognizer.recognize_google(audio_data)


# ----------------------------------------------------------------------
# GUI Application
# ----------------------------------------------------------------------
class VoiceTextApp:
    def __init__(self, root):
        self.root = root
        self.engine = VoiceTextEngine()

        root.title("Voice-Text Converter Pro")
        root.geometry("640x560")
        root.minsize(560, 480)
        root.configure(bg="#0f172a")

        self._build_style()
        self._build_header()

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.text_to_voice_tab = ttk.Frame(self.tabs)
        self.voice_to_text_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.text_to_voice_tab, text="  Text ➜ Voice  ")
        self.tabs.add(self.voice_to_text_tab, text="  Voice ➜ Text  ")

        self._build_text_to_voice_tab()
        self._build_voice_to_text_tab()

    # ---------------- Styling ----------------
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background="#0f172a", borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 10, "bold"),
            padding=(16, 8),
        )
        style.configure("TFrame", background="#111827")
        style.configure(
            "TButton", font=("Segoe UI", 10, "bold"), padding=8
        )
        style.configure("TLabel", background="#111827", foreground="#e5e7eb")

    def _build_header(self):
        header = tk.Frame(self.root, bg="#0f172a")
        header.pack(fill="x", padx=14, pady=14)
        tk.Label(
            header,
            text="🎙️  Voice-Text Converter Pro",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#38bdf8",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Convert text to speech, or speech to text — 100% Python.",
            font=("Segoe UI", 9),
            bg="#0f172a",
            fg="#94a3b8",
        ).pack(anchor="w")

    # ---------------- TAB 1: Text -> Voice ----------------
    def _build_text_to_voice_tab(self):
        frame = self.text_to_voice_tab

        ttk.Label(frame, text="Enter text below:").pack(
            anchor="w", padx=14, pady=(14, 4)
        )
        self.text_input = scrolledtext.ScrolledText(
            frame, height=10, font=("Segoe UI", 11), wrap="word"
        )
        self.text_input.pack(fill="both", expand=True, padx=14, pady=4)

        controls = ttk.Frame(frame)
        controls.pack(fill="x", padx=14, pady=8)

        ttk.Label(controls, text="Speed:").grid(row=0, column=0, padx=(0, 6))
        self.rate_slider = ttk.Scale(
            controls, from_=80, to=300, value=170, command=self._on_rate_change
        )
        self.rate_slider.grid(row=0, column=1, sticky="ew", padx=(0, 14))

        ttk.Label(controls, text="Voice:").grid(row=0, column=2, padx=(0, 6))
        self.voice_choice = ttk.Combobox(controls, state="readonly", width=22)
        voices = self.engine.get_voices()
        self.voice_choice["values"] = [v.name for v in voices]
        if voices:
            self.voice_choice.current(0)
        self.voice_choice.bind("<<ComboboxSelected>>", self._on_voice_change)
        self.voice_choice.grid(row=0, column=3, sticky="ew")

        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(3, weight=1)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", padx=14, pady=(4, 14))

        ttk.Button(btn_row, text="▶ Speak", command=self._speak_text).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(
            btn_row, text="💾 Save as Audio File", command=self._save_audio
        ).pack(side="left")

        self.tts_status = ttk.Label(frame, text="", foreground="#22c55e")
        self.tts_status.pack(anchor="w", padx=14, pady=(0, 10))

    def _on_rate_change(self, value):
        self.engine.set_rate(int(float(value)))

    def _on_voice_change(self, event):
        idx = self.voice_choice.current()
        voices = self.engine.get_voices()
        if 0 <= idx < len(voices):
            self.engine.set_voice(voices[idx].id)

    def _speak_text(self):
        text = self.text_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Text", "Pehle kuch text likhen.")
            return
        self.tts_status.config(text="Speaking...")
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            self.engine.speak(text)
            self.tts_status.config(text="✔ Done speaking.")
        except Exception as exc:
            self.tts_status.config(text=f"Error: {exc}")

    def _save_audio(self):
        text = self.text_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Empty Text", "Pehle kuch text likhen.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 Audio", "*.mp3"), ("WAV Audio", "*.wav")],
            title="Save Audio As",
        )
        if not filepath:
            return
        self.tts_status.config(text="Saving audio...")
        threading.Thread(
            target=self._save_audio_thread, args=(text, filepath), daemon=True
        ).start()

    def _save_audio_thread(self, text, filepath):
        try:
            self.engine.save_to_file(text, filepath)
            self.tts_status.config(text=f"✔ Saved to {os.path.basename(filepath)}")
        except Exception as exc:
            self.tts_status.config(text=f"Error: {exc}")

    # ---------------- TAB 2: Voice -> Text ----------------
    def _build_voice_to_text_tab(self):
        frame = self.voice_to_text_tab

        ttk.Label(
            frame, text="Recognized text will appear below:"
        ).pack(anchor="w", padx=14, pady=(14, 4))

        self.stt_output = scrolledtext.ScrolledText(
            frame, height=12, font=("Segoe UI", 11), wrap="word"
        )
        self.stt_output.pack(fill="both", expand=True, padx=14, pady=4)

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", padx=14, pady=8)

        ttk.Button(
            btn_row, text="🎤 Record from Microphone", command=self._record_mic
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_row, text="📂 Transcribe Audio File", command=self._transcribe_file
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            btn_row, text="🗑 Clear", command=self._clear_stt_output
        ).pack(side="left")

        self.stt_status = ttk.Label(frame, text="", foreground="#22c55e")
        self.stt_status.pack(anchor="w", padx=14, pady=(0, 10))

    def _clear_stt_output(self):
        self.stt_output.delete("1.0", "end")
        self.stt_status.config(text="")

    def _record_mic(self):
        self.stt_status.config(text="🎙 Listening... bolna shuru karen.")
        threading.Thread(target=self._record_mic_thread, daemon=True).start()

    def _record_mic_thread(self):
        try:
            text = self.engine.listen_from_microphone()
            self.stt_output.insert("end", text + "\n")
            self.stt_status.config(text="✔ Recognized successfully.")
        except sr.WaitTimeoutError:
            self.stt_status.config(text="⏱ Timeout — koi awaz nahi mili.")
        except sr.UnknownValueError:
            self.stt_status.config(text="❌ Awaz samajh nahi aayi, dobara koshish karen.")
        except sr.RequestError as exc:
            self.stt_status.config(text=f"Network/API error: {exc}")
        except Exception as exc:
            self.stt_status.config(text=f"Error: {exc}")

    def _transcribe_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.aiff *.aif *.flac")],
            title="Select an Audio File",
        )
        if not filepath:
            return
        self.stt_status.config(text="Transcribing file...")
        threading.Thread(
            target=self._transcribe_file_thread, args=(filepath,), daemon=True
        ).start()

    def _transcribe_file_thread(self, filepath):
        try:
            text = self.engine.transcribe_file(filepath)
            self.stt_output.insert("end", text + "\n")
            self.stt_status.config(text="✔ Transcription complete.")
        except sr.UnknownValueError:
            self.stt_status.config(text="❌ Awaz samajh nahi aayi.")
        except sr.RequestError as exc:
            self.stt_status.config(text=f"Network/API error: {exc}")
        except Exception as exc:
            self.stt_status.config(text=f"Error: {exc}")


# ----------------------------------------------------------------------
def main():
    root = tk.Tk()
    app = VoiceTextApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
