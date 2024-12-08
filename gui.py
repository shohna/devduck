# import tkinter as tk
# from tkinter import scrolledtext
# import whisper
# import sounddevice as sd
# import soundfile as sf
# import numpy as np
# import threading
# import time
# import queue


# class VoiceChatApp:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("Voice Chat App")
#         self.root.geometry("600x800")
        
#         # Initialize whisper model
#         self.model = whisper.load_model("base")
        
#         # Recording state
#         self.is_recording = False
#         self.audio_data = []
#         self.sample_rate = 16000
#         self.channels = 1
#         self.setup_ui()
        
#     def setup_ui(self):
#         # Chat history display
#         self.history_area = scrolledtext.ScrolledText(
#             self.root, 
#             wrap=tk.WORD, 
#             width=50, 
#             height=30
#         )
#         self.history_area.pack(padx=10, pady=10, expand=True, fill='both')
        
#         # Record button - removed the command parameter
#         self.record_button = tk.Button(
#             self.root,
#             text="🎤 Hold to Record"
#         )
#         self.record_button.pack(pady=20)
        
#         # Bind button press and release
#         self.record_button.bind('<ButtonPress-1>', self.start_recording)
#         self.record_button.bind('<ButtonRelease-1>', self.stop_recording)
        
#         # Status label
#         self.status_label = tk.Label(self.root, text="Ready")
#         self.status_label.pack(pady=5)
        
#     def audio_callback(self, indata, frames, time, status):
#         if self.is_recording:
#             self.audio_data.append(indata.copy())
            
#     def start_recording(self, event):
#         self.is_recording = True
#         self.audio_data = []
#         self.record_button.config(text="🔴 Recording...")
#         self.status_label.config(text="Recording...")
        
#         # Start recording in a separate thread
#         self.recording_thread = threading.Thread(target=self.record_audio)
#         self.recording_thread.start()
        
#     def record_audio(self):
#         with sd.InputStream(callback=self.audio_callback,
#                           channels=1,
#                           samplerate=self.sample_rate):
#             while self.is_recording:
#                 sd.sleep(100)
                
#     def stop_recording(self, event):
#         self.is_recording = False
#         self.record_button.config(text="🎤 Hold to Record")
#         self.status_label.config(text="Processing...")
        
#         # Process the recording in a separate thread
#         processing_thread = threading.Thread(target=self.process_audio)
#         processing_thread.start()
        
#     def process_audio(self):
#         if len(self.audio_data) > 0:
#             # Combine all audio chunks
#             audio = np.concatenate(self.audio_data, axis=0)
            
#             # Save temporary file
#             sf.write("temp_recording.wav", audio, self.sample_rate)
            
#             # Transcribe with Whisper
#             result = self.model.transcribe("temp_recording.wav")
#             transcribed_text = result["text"]
            
#             # Add to chat history
#             timestamp = time.strftime("%H:%M:%S")
#             self.history_area.insert(tk.END, f"[{timestamp}] You: {transcribed_text}\n\n")
#             self.history_area.see(tk.END)
            
#             self.status_label.config(text="Ready")

# if __name__ == "__main__":
#     root = tk.Tk()
#     app = VoiceChatApp(root)
#     root.mainloop()



import tkinter as tk
from tkinter import scrolledtext, ttk
import whisper
import sounddevice as sd
import numpy as np
import threading
import queue
import time
from openai import OpenAI


class AudioTranscriptionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DevDuck Audio Transcription")
        
        # Initialize audio components
        self.SAMPLE_RATE = 16000
        self.CHANNELS = 1
        self.CHUNK_DURATION = 3
        self.text_chunks = []
        self.CHUNK_SIZE = int(self.SAMPLE_RATE * self.CHUNK_DURATION)
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.history = []
        
        # Initialize Whisper model
        print("Loading Whisper model...")
        self.model = whisper.load_model("base")
        self.llm_client = OpenAI(api_key="lm-studio", base_url="http://localhost:1234/v1")
        self.system_prompt = '''You are a helpful assistant. Your job is to filter the user's text (which is a transcript of a conversation) and remove all filler, unnecessary and unrelated text. You must output text directly, such that it can be fed to another llm model. Fix incorrect transcripts to preserve technical knowledge. Just output '''
        self.llm_model_name = "llama-3.2-3b-qnn"
        self.create_gui()
        
    def create_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create text display area
        self.text_area = scrolledtext.ScrolledText(main_frame, width=50, height=20)
        self.text_area.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        
        # Create buttons
        self.start_button = ttk.Button(main_frame, text="Start Recording", 
                                     command=self.start_recording)
        self.start_button.grid(row=1, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(main_frame, text="Stop Recording", 
                                    command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.grid(row=1, column=1, padx=5, pady=5)
        
    def audio_callback(self, indata, frames, time, status):
        if status:
            self.log_message(f'Status: {status}')
        self.audio_queue.put(indata.copy())
        
    def process_audio(self):
        while self.is_recording:
            try:
                audio_data = self.audio_queue.get(timeout=1)
                audio_data = audio_data.flatten().astype(np.float32)
                result = self.model.transcribe(audio_data)
                
                if result["text"].strip():
                    self.log_message(result["text"])
                    self.text_chunks.append(result["text"])
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.log_message(f"Error in processing: {e}")
                continue
                
    def start_recording(self):
        try:
            self.is_recording = True
            self.stream = sd.InputStream(
                device=None,
                channels=self.CHANNELS,
                samplerate=self.SAMPLE_RATE,
                callback=self.audio_callback,
                blocksize=self.CHUNK_SIZE,
                dtype=np.float32
            )
            
            # Start the stream and processing thread
            self.stream.start()
            self.processing_thread = threading.Thread(target=self.process_audio, 
                                                   daemon=True)
            self.processing_thread.start()
            
            # Update button states
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.log_message("Recording started...")
            
        except Exception as e:
            self.log_message(f"Error starting recording: {e}")
            
    def stop_recording(self):
        self.is_recording = False
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            
        # Update button states
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.process_text()
        
        self.log_message("Recording stopped.")
        
    def log_message(self, message):
        self.text_area.insert(tk.END, f"{message}\n")
        self.text_area.see(tk.END)
        
    def process_text(self):
        transcription = "".join(self.text_chunks)
        self.log_message(transcription)
        history = " ".join(self.history)
        user_prompt = f'''Here's the transcription, clean it up and preserve technical knowledge and return first person text: "{transcription}"'''

        response1 = self.llm_client.chat.completions.create(
        model=self.llm_model_name,
        messages=[
            {"role": "system", "content": self.system_prompt + f''' Here is out conversation till now: "{history}" '''},
            {"role": "user", "content": user_prompt},
        ],
        )
        cleaned_idea = response1.choices[0].message.content
        system_prompt2 = '''You are a helpful assistant whose job is to guide the user in ideating a project or code approach. do not supply the answer but ask questions to guide the user. '''

        user_prompt2 = f'''Here's the user's idea, filtered: "{cleaned_idea}
        If you ask followup questions, make the questions normal and conversational. Do not ask all the questions at once.'''

        response2 = self.llm_client.chat.completions.create(
        model=self.llm_model_name,
        messages=[
            {"role": "system", "content": system_prompt2},
            {"role": "user", "content": user_prompt2},
        ],
        )
        duck_response = response2.choices[0].message.content

        cleaned_idea = response1.choices[0].message.content
        self.history.append(duck_response)
        self.log_message(duck_response)
        self.text_chunks = []
        
def main():
    root = tk.Tk()
    app = AudioTranscriptionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()