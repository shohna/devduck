# import tkinter as tk
# from tkinter import scrolledtext, ttk
# import speech_recognition as sr
# import threading
# import queue
# from openai import OpenAI

# class AudioTranscriptionGUI:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("DevDuck Audio Transcription")
        
#         # Initialize audio components
#         self.text_chunks = []
#         self.audio_queue = queue.Queue()
#         self.is_recording = False
#         self.history = []
        
#         # Initialize speech recognizer
#         self.recognizer = sr.Recognizer()
#         self.llm_client = OpenAI(api_key="lm-studio", base_url="http://localhost:1234/v1")
#         self.system_prompt = '''You are a helpful assistant. Your job is to filter the user's text (which is a transcript of a conversation) and remove all filler, unnecessary and unrelated text. You must output text directly, such that it can be fed to another llm model. Fix incorrect transcripts to preserve technical knowledge. Just output '''
#         self.llm_model_name = "llama-3.2-3b-qnn"
#         self.create_gui()
        
#     def create_gui(self):
#         main_frame = ttk.Frame(self.root, padding="10")
#         main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
#         self.text_area = scrolledtext.ScrolledText(main_frame, width=50, height=20)
#         self.text_area.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        
#         self.start_button = ttk.Button(main_frame, text="Start Recording", 
#                                      command=self.start_recording)
#         self.start_button.grid(row=1, column=0, padx=5, pady=5)
        
#         self.stop_button = ttk.Button(main_frame, text="Stop Recording", 
#                                     command=self.stop_recording, state=tk.DISABLED)
#         self.stop_button.grid(row=1, column=1, padx=5, pady=5)
        
#     def process_audio(self):
#         with sr.Microphone() as source:
#             self.recognizer.adjust_for_ambient_noise(source)
#             while self.is_recording:
#                 try:
#                     audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
#                     text = self.recognizer.recognize_google(audio)
#                     if text.strip():
#                         self.log_message(text)
#                         self.text_chunks.append(text)
#                 except sr.WaitTimeoutError:
#                     continue
#                 except sr.UnknownValueError:
#                     self.log_message("Speech not recognized")
#                 except sr.RequestError as e:
#                     self.log_message(f"Could not request results; {e}")
#                 except Exception as e:
#                     self.log_message(f"Error in processing: {e}")
                
#     def start_recording(self):
#         self.is_recording = True
#         self.processing_thread = threading.Thread(target=self.process_audio, 
#                                                daemon=True)
#         self.processing_thread.start()
        
#         self.start_button.config(state=tk.DISABLED)
#         self.stop_button.config(state=tk.NORMAL)
        
#         self.log_message("Recording started...")
            
#     def stop_recording(self):
#         self.is_recording = False
        
#         self.start_button.config(state=tk.NORMAL)
#         self.stop_button.config(state=tk.DISABLED)
#         self.process_text()
        
#         self.log_message("Recording stopped.")
        
#     def log_message(self, message):
#         self.text_area.insert(tk.END, f"{message}\n")
#         self.text_area.see(tk.END)
        
#     def process_text(self):
#         transcription = " ".join(self.text_chunks)
#         self.log_message(transcription)
#         history = " ".join(self.history)
#         user_prompt = f'''Here's the transcription, clean it up and preserve technical knowledge and return first person text: "{transcription}"'''

#         response1 = self.llm_client.chat.completions.create(
#         model=self.llm_model_name,
#         messages=[
#             {"role": "system", "content": self.system_prompt + f''' Here is out conversation till now: "{history}" '''},
#             {"role": "user", "content": user_prompt},
#         ],
#         )
#         cleaned_idea = response1.choices[0].message.content
#         system_prompt2 = '''You are a helpful assistant whose job is to guide the user in ideating a project or code approach. do not supply the answer but ask questions to guide the user. '''

#         user_prompt2 = f'''Here's the user's idea, filtered: "{cleaned_idea}
#         If you ask followup questions, make the questions normal and conversational. Do not ask all the questions at once.'''

#         response2 = self.llm_client.chat.completions.create(
#         model=self.llm_model_name,
#         messages=[
#             {"role": "system", "content": system_prompt2},
#             {"role": "user", "content": user_prompt2},
#         ],
#         )
#         duck_response = response2.choices[0].message.content

#         cleaned_idea = response1.choices[0].message.content
#         self.history.append(duck_response)
#         self.log_message(duck_response)
#         self.text_chunks = []
        
# def main():
#     root = tk.Tk()
#     app = AudioTranscriptionGUI(root)
#     root.mainloop()

# if __name__ == "__main__":
#     main() 


import tkinter as tk
import speech_recognition as sr
from openai import OpenAI
import os

class ChatbotGUI:
    def __init__(self, master):
        self.master = master
        master.title("Voice Chatbot with OpenAI")
        master.geometry("500x600")

        self.chat_display = tk.Text(master, height=25, width=60)
        self.chat_display.pack(pady=10)

        self.voice_button = tk.Button(master, text="Speak", command=self.get_voice_input)
        self.voice_button.pack(pady=5)

        self.recognizer = sr.Recognizer()
        self.client = OpenAI(api_key="lm-studio", base_url="http://localhost:1234/v1")
        self.messages = [{"role": "system", "content": "You are a helpful assistant."}]

    def get_voice_input(self):
        with sr.Microphone() as source:
            self.chat_display.insert(tk.END, "Listening...\n")
            self.master.update()
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)
            self.chat_display.insert(tk.END, f"You: {text}\n")
            self.process_input(text)
        except sr.UnknownValueError:
            self.chat_display.insert(tk.END, "Sorry, I didn't catch that.\n")
        except sr.RequestError:
            self.chat_display.insert(tk.END, "Sorry, there was an error processing your request.\n")

    def process_input(self, text):
        self.messages.append({"role": "user", "content": text})
        
        response = self.client.chat.completions.create(
            model="llama-3.2-3b-qnn",
            messages=self.messages
        )

        assistant_response = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_response})
        
        self.chat_display.insert(tk.END, f"Bot: {assistant_response}\n")
        self.chat_display.see(tk.END)

root = tk.Tk()
chatbot_gui = ChatbotGUI(root)
root.mainloop()