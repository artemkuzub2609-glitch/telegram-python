import base64
import io
import os
import threading
from socket import socket, AF_INET, SOCK_STREAM
from customtkinter import *
from tkinter import filedialog
from PIL import Image
import sounddevice as sd
import soundfile as sf

# ==== Налаштування теми ====
set_appearance_mode("Dark")
set_default_color_theme("dark-blue")

MENU_WIDTH_COLLAPSED = 50
MENU_WIDTH_EXPANDED = 200
ANIMATION_STEP = 10
VOICE_DURATION = 3  # секунд для запису

class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("900x650")
        self.title("Chat Client")
        self.username = "Artem"
        self.menu_width = MENU_WIDTH_COLLAPSED
        self.is_show_menu = False

        # ==== Меню ====
        self.menu_frame = CTkFrame(self, width=self.menu_width, height=650, fg_color="#2c2f3b")
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        # Кнопка меню (lambda щоб уникнути AttributeError)
        self.menu_button = CTkButton(self.menu_frame, text='▶️', width=MENU_WIDTH_COLLAPSED,
                                     command=lambda: self.toggle_show_menu())
        self.menu_button.place(x=0, y=0)

        # ==== Чат ====
        self.chat_field = CTkScrollableFrame(self, width=700, height=500, fg_color="#1e1f29")
        self.chat_field.place(x=self.menu_width + 10, y=10)

        # ==== Поле введення ====
        self.message_entry = CTkEntry(self, width=500, height=40, placeholder_text="Введіть повідомлення...")
        self.message_entry.place(x=self.menu_width + 10, y=520)
        self.send_button = CTkButton(self, text='➡️', width=80, height=40, command=self.send_message, fg_color="#5a4fff")
        self.send_button.place(x=720, y=520)
        self.open_img_button = CTkButton(self, text='📂', width=80, height=40, command=self.open_image, fg_color="#5a4fff")
        self.open_img_button.place(x=810, y=520)
        self.voice_button = CTkButton(self, text='🎤', width=50, height=40, command=self.send_voice_thread, fg_color="#5a4fff")
        self.voice_button.place(x=self.menu_width + 520, y=520)

        # ==== Підключення до сервера ====
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(("localhost", 8080))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.send(hello.encode("utf-8"))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"[SYSTEM] Не вдалося підключитися до сервера: {e}")

        self.bind("<Return>", lambda e: self.send_message())
        self.after(50, self.adaptive_ui)

    # ==== Адаптивний UI ====
    def adaptive_ui(self):
        self.chat_field.place(x=self.menu_width + 10, y=10,
                              width=self.winfo_width() - self.menu_width - 30,
                              height=self.winfo_height() - 150)
        self.message_entry.place(x=self.menu_width + 10, y=self.winfo_height() - 100,
                                 width=self.winfo_width() - self.menu_width - 200)
        self.send_button.place(x=self.winfo_width() - 170, y=self.winfo_height() - 100)
        self.open_img_button.place(x=self.winfo_width() - 90, y=self.winfo_height() - 100)
        self.voice_button.place(x=self.menu_width + 520, y=self.winfo_height() - 100)
        self.after(50, self.adaptive_ui)

    # ==== Меню ====
    def toggle_show_menu(self):
        self.is_show_menu = not self.is_show_menu
        if self.is_show_menu:
            self.menu_button.configure(text='◀️')
            self.animate_menu(True)
        else:
            self.menu_button.configure(text='▶️')
            self.animate_menu(False)

    def animate_menu(self, opening):
        if opening:
            if self.menu_width < MENU_WIDTH_EXPANDED:
                self.menu_width += ANIMATION_STEP
                if self.menu_width > MENU_WIDTH_EXPANDED:
                    self.menu_width = MENU_WIDTH_EXPANDED
                self.menu_frame.configure(width=self.menu_width)
                self.chat_field.place(x=self.menu_width + 10)
                self.message_entry.place(x=self.menu_width + 10)
                self.voice_button.place(x=self.menu_width + 520)
                self.after(10, lambda: self.animate_menu(True))
            else:
                self.show_menu_elements()
        else:
            if self.menu_width > MENU_WIDTH_COLLAPSED:
                self.menu_width -= ANIMATION_STEP
                if self.menu_width < MENU_WIDTH_COLLAPSED:
                    self.menu_width = MENU_WIDTH_COLLAPSED
                self.menu_frame.configure(width=self.menu_width)
                self.chat_field.place(x=self.menu_width + 10)
                self.message_entry.place(x=self.menu_width + 10)
                self.voice_button.place(x=self.menu_width + 520)
                self.after(10, lambda: self.animate_menu(False))
            else:
                self.hide_menu_elements()

    def show_menu_elements(self):
        self.label = CTkLabel(self.menu_frame, text="Ваш нік:", text_color="white")
        self.label.pack(pady=20)
        self.entry = CTkEntry(self.menu_frame, placeholder_text=self.username)
        self.entry.pack(pady=10)
        self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name, fg_color="#5a4fff")
        self.save_button.pack(pady=10)

    def hide_menu_elements(self):
        if hasattr(self, "label"):
            self.label.destroy()
        if hasattr(self, "entry"):
            self.entry.destroy()
        if hasattr(self, "save_button"):
            self.save_button.destroy()

    def save_name(self):
        new_name = self.entry.get().strip()
        if new_name:
            self.username = new_name
            self.add_message(f"[SYSTEM] Ваш новий нік: {self.username}")

    # ==== Відображення повідомлень ====
    def add_message(self, message, img=None, voice_data=None):
        msg_frame = CTkFrame(self.chat_field, fg_color="#2c2f3b", corner_radius=10)
        msg_frame.pack(pady=5, anchor='w')
        wrap_len = self.winfo_width() - self.menu_width - 60

        if img:
            CTkLabel(msg_frame, text=message, image=img, compound="top", text_color="white", wraplength=wrap_len).pack(padx=10, pady=5)
        elif voice_data:
            CTkLabel(msg_frame, text=message, text_color="white", wraplength=wrap_len, justify="left").pack(padx=10, pady=5)
            play_button = CTkButton(msg_frame, text="▶ Відтворити",
                                    command=lambda: threading.Thread(target=self.play_voice, args=(voice_data,), daemon=True).start())
            play_button.pack(pady=5)
        else:
            CTkLabel(msg_frame, text=message, text_color="white", wraplength=wrap_len, justify="left").pack(padx=10, pady=5)

    # ==== Відправка тексту ====
    def send_message(self):
        msg = self.message_entry.get().strip()
        if msg:
            self.add_message(f"{self.username}: {msg}")
            data = f"TEXT@{self.username}@{msg}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                self.add_message("[SYSTEM] Помилка відправки повідомлення.")
        self.message_entry.delete(0, END)

    # ==== Відправка голосу ====
    def send_voice_thread(self):
        threading.Thread(target=self.send_voice, daemon=True).start()

    def send_voice(self):
        try:
            self.add_message(f"[VOICE] {self.username} записує голосове повідомлення...")
            audio_data = sd.rec(int(VOICE_DURATION * 44100), samplerate=44100, channels=1, dtype='int16')
            sd.wait()
            buf = io.BytesIO()
            sf.write(buf, audio_data, 44100, format='WAV')
            buf.seek(0)
            b64_audio = base64.b64encode(buf.read()).decode("utf-8")
            data = f"VOICE@{self.username}@{VOICE_DURATION}@{b64_audio}\n"
            self.sock.sendall(data.encode())
            self.add_message(f"[VOICE] {self.username} надіслав голосове повідомлення", voice_data=b64_audio)
        except Exception as e:
            self.add_message(f"[SYSTEM] Помилка запису голосового повідомлення: {e}")

    # ==== Отримання повідомлень ====
    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]

        if msg_type == "TEXT" and len(parts) >= 3:
            author = parts[1]
            message = parts[2]
            self.add_message(f"{author}: {message}")

        elif msg_type == "IMAGE" and len(parts) >= 4:
            author, filename, b64_img = parts[1], parts[2], parts[3]
            try:
                img_data = base64.b64decode(b64_img)
                pil_img = Image.open(io.BytesIO(img_data))
                ctk_img = CTkImage(pil_img, size=(300,300))
                self.add_message(f"{author} надіслав(ла) зображення: {filename}", img=ctk_img)
            except Exception as e:
                self.add_message(f"[SYSTEM] Помилка відображення зображення: {e}")

        elif msg_type == "VOICE" and len(parts) >= 4:
            author, duration, b64_audio = parts[1], parts[2], parts[3]
            self.add_message(f"[VOICE] {author} надіслав голосове повідомлення", voice_data=b64_audio)

    # ==== Відтворення голосу ====
    def play_voice(self, b64_audio):
        try:
            audio_data = base64.b64decode(b64_audio)
            buf = io.BytesIO(audio_data)
            data, samplerate = sf.read(buf, dtype="int16")
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            self.add_message(f"[SYSTEM] Помилка відтворення голосового повідомлення: {e}")

    # ==== Відправка зображення ====
    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as f:
                raw = f.read()
            b64_data = base64.b64encode(raw).decode()
            short_name = os.path.basename(file_name)
            data = f"IMAGE@{self.username}@{short_name}@{b64_data}\n"
            self.sock.sendall(data.encode())
            self.add_message("", img=CTkImage(Image.open(file_name), size=(300,300)))
        except Exception as e:
            self.add_message(f"[SYSTEM] Не вдалося надіслати зображення: {e}")


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()
