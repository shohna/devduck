import customtkinter as ctk
import speech_recognition as sr
import threading
import pyaudio
import wave
import os
from main import ToolHandler, ClientManager
import pyttsx3

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

        # Session selection
        self.session_label = ctk.CTkLabel(self.sidebar_frame, text="Select Session:", anchor="w")
        self.session_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        
        self.session_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=[], command=self.change_session)
        self.session_menu.grid(row=2, column=0, padx=20, pady=(10, 10))

        self.new_session_button = ctk.CTkButton(self.sidebar_frame, text="New Session", command=self.new_session)
        self.new_session_button.grid(row=3, column=0, padx=20, pady=(10, 10))

        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.mode_label.grid(row=4, column=0, padx=20, pady=(10, 0))
        
        self.mode_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["System", "Light", "Dark"],
                                                       command=self.change_appearance_mode)
        self.mode_menu.grid(row=5, column=0, padx=20, pady=(10, 10))

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
        
        self.start_button = ctk.CTkButton(self.button_frame, text="Start Recording", command=self.start_recording)
        self.start_button.grid(row=0, column=0, padx=(0, 10), pady=10)

        self.stop_button = ctk.CTkButton(self.button_frame, text="Stop Recording", command=self.stop_recording,
                                          state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(10, 0), pady=10)

        # Initialize speech recognition and audio components
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.audio = pyaudio.PyAudio()
        self.speech_engine = pyttsx3.init()
        
        # Initialize ToolHandler and session management
        self.tool_handler = ToolHandler()
        
        # Dictionary to hold chat sessions
        self.sessions = {}
        self.new_session()
        
    def new_session(self):
        session_name = f"Session {len(self.sessions) + 1}"
        if session_name not in self.sessions:
            self.sessions[session_name] = []
            
            # Get current values and add the new session
            current_values = self.session_menu.cget("values")
            new_values = list(current_values) + [session_name]
            
            # Update the option menu with new values
            self.session_menu.configure(values=new_values)
            
            # Set the newly created session as current
            self.session_menu.set(session_name)
        
    def change_session(self, session_name):
        if session_name in self.sessions:
            # Load the selected session's chat history into the display
            chat_history = "\n".join(self.sessions[session_name])
            self.chat_display.delete("1.0", ctk.END)  # Clear current display
            if chat_history:
                self.chat_display.insert(ctk.END, chat_history)

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
    
    def start_recording(self):
        self.is_recording = True
        self.frames = []
        self.start_button.configure(state=ctk.DISABLED)
        self.stop_button.configure(state=ctk.NORMAL)
        self.chat_display.insert(ctk.END, "\nRecording started...\n")
        
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
        self.chat_display.insert(ctk.END, "\nRecording stopped.\n")
        
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
            self.chat_display.insert(ctk.END, f"\nYou: {text}\n")
            self.process_input(text)
        except sr.UnknownValueError:
            self.chat_display.insert(ctk.END, "\nSorry, I didn't catch that.\n")
        except sr.RequestError:
            self.chat_display.insert(ctk.END, "\nSorry, there was an error processing your request.\n")

    def process_input(self, text):
        self.chat_display.insert("end", "\nAI: ")
        threading.Thread(target=self.stream_response, args=(text,)).start()

    def stream_response(self, text):
        history = "".join(self.sessions[self.session_menu.get()])
        print(history)
        tool, response = self.tool_handler.tool_selection(text, history)
        self.chat_display.insert(ctk.END, f"Using {tool} tool:")
        full_response = ""
        for chunk in response:
            if chunk is not None:
                full_response += chunk
                self.chat_display.insert(ctk.END, chunk)
                self.chat_display.see(ctk.END)
        
        # Speak the full response
        self.speech_engine.say(full_response)
        self.speech_engine.runAndWait()
        
        self.chat_display.see(ctk.END)
        self.sessions[self.session_menu.get()].append((f"prompt:{text}, response:{full_response}"))


if __name__ == "__main__":
    app = VoiceChatApp()
    app.mainloop()