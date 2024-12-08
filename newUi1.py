import customtkinter as ctk
import speech_recognition as sr
from openai import OpenAI
import threading
import pyaudio
import wave
import os

# Set your OpenAI API key as an environment variable

class VoiceChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Voice Chat AI")
        self.geometry("800x600")

        # Set the initial theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar frame with widgets
        self.sidebar_frame = ctk.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Voice Chat AI", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                       command=self.change_appearance_mode)
        self.mode_menu.grid(row=6, column=0, padx=20, pady=(10, 10))

        # Create main frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Chat display
        self.chat_display = ctk.CTkTextbox(self.main_frame, width=500, height=400)
        self.chat_display.grid(row=1, column=0, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # Buttons frame
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.grid(row=2, column=0, padx=(20, 20), pady=(0, 20), sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.start_button = ctk.CTkButton(self.button_frame, text="Start Recording", command=self.start_recording)
        self.start_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")

        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop Recording", command=self.stop_recording, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="ew")

        # Initialize speech recognition and OpenAI client
        self.recognizer = sr.Recognizer()
        self.client = OpenAI(api_key="lm-studio", base_url="http://localhost:1234/v1")
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.stream = None
        self.is_recording = False
        
        self.messages = [{"role": "system", "content": "You are a helpful assistant whose job is to guide the user in ideating a project or code approach. do not supply the answer but ask questions to guide the user. Keep the conversation going until reaching a concrete implementation plan. do not ask all questions at once, solve iteratively as if its a natural conversation. Keep the output brief. Limit the response to 400 words."}]


    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.start_button.configure(state=ctk.DISABLED)
        self.stop_button.configure(state=ctk.NORMAL)
        self.chat_display.insert(ctk.END, "Recording started...\n")
        
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        threading.Thread(target=self.record_audio).start()
        
    def record_audio(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.frames.append(data)

        

    def stop_recording(self):
        self.is_recording = False
        self.start_button.configure(state=ctk.NORMAL)
        self.stop_button.configure(state=ctk.DISABLED)
        self.chat_display.insert(ctk.END, "Recording stopped.\n")
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        wf = wave.open("temp_audio.wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        self.transcribe_audio()

    def transcribe_audio(self):
        with sr.AudioFile("temp_audio.wav") as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio)
            self.chat_display.insert(ctk.END, f"You: {text}\n")
            
        except sr.UnknownValueError:
            self.chat_display.insert(ctk.END, "Sorry, I didn't catch that.\n")
        except sr.RequestError:
            self.chat_display.insert(ctk.END, "Sorry, there was an error processing your request.\n")

        if text:
            self.process_input(text)
            
    def process_input(self, text):
        self.chat_display.insert("end", "AI: ")
        threading.Thread(target=self.stream_response, args=(text,)).start()

    def stream_response(self, text):
        self.messages.append({"role": "user", "content": text})
        stream = self.client.chat.completions.create(
            model="llama-3.2-3b-qnn",
            messages=self.messages,
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                self.chat_display.insert(ctk.END, chunk.choices[0].delta.content)
                self.chat_display.see(ctk.END)

        self.chat_display.insert(ctk.END, "\n")
        self.chat_display.see(ctk.END)

if __name__ == "__main__":
    app = VoiceChatApp()
    app.mainloop()