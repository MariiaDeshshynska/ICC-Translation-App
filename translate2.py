import customtkinter as ctk
from tkinter import Menu
import tkinter as tk
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
import torch
import os
import sys
import threading
import gc  

# Функція для шляху PyInstaller
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

stop_translation = False

# Завантаження моделі 
def load_models():
    global m2m_tokenizer, m2m_model, device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # завантаження моделі
    m2m_tokenizer = M2M100Tokenizer.from_pretrained(m2m_model_dir)
    m2m_model = M2M100ForConditionalGeneration.from_pretrained(m2m_model_dir).to(device)

    if device.type == "cuda":
        m2m_model = m2m_model.half()

    # Для прогрівання моделі
    dummy_input = "Hello"
    model_inputs = m2m_tokenizer(dummy_input, return_tensors="pt").to(device)
    _ = m2m_model.generate(**model_inputs)

    # Очистка кешу GPU 
    if device.type == "cuda":
        torch.cuda.empty_cache()

    # Оновити GUI
    root.after(0, finish_loading)

# Завершення завантаження
def finish_loading():
    progress_bar.grid_forget()  
    main_app()  

# Переклад тексту 
def translate_text():
    global stop_translation
    stop_translation = False
    translate_button.configure(state="disabled", text="Переклад виконується...")
    stop_button.configure(state="normal")  # Працює кнопка зупнити
    text_input.configure(state="disabled")  # Заборона вставлення в input

    def translate():
        try:
            text_output.delete("1.0", ctk.END)  #Очистити output

            result = []
            gc.collect()  

            source_lang = language_map_display.get(lang_from.get())
            target_lang = language_map_display.get(lang_to.get())

            language_map = {
                        "English": "en",
                        "Ukrainian": "uk",
                        "French": "fr",
                        "German": "de",
                        "Spanish": "es",
                        "Italian": "it",
                        "Portuguese": "pt",
                        "Russian": "ru",
                        "Chinese": "zh",
                        "Japanese": "ja",
                        "Korean": "ko",
                        "Hindi": "hi",
                        "Arabic": "ar",
                        "Persian": "fa",
                        "Hebrew": "he",
                        "Polish": "pl",
                        "Czech": "cs",
                        "Slovak": "sk",
                        "Romanian": "ro"
                        }


            src_lang_code = language_map.get(source_lang, "en")
            tgt_lang_code = language_map.get(target_lang, "uk")

            model = m2m_model
            tokenizer = m2m_tokenizer

            input_text = text_input.get("1.0", ctk.END).strip()
            text_chunks = split_text(input_text, chunk_size=256)

            for chunk in text_chunks:
                if stop_translation:
                    break  

                model_inputs = tokenizer(chunk, return_tensors="pt", max_length=512, truncation=True).to(device)

                if device.type == "cuda":
                    model_inputs = {key: value.half() for key, value in model_inputs.items()}

                tokenizer.src_lang = src_lang_code
                translated_tokens = model.generate(
                    **model_inputs,
                    forced_bos_token_id=tokenizer.get_lang_id(tgt_lang_code),
                    num_beams=2,
                    early_stopping=True
                )

                translated_text = tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]
                result.append(translated_text)

                gc.collect()  

            if not stop_translation:
                full_translation = " ".join(result)
                root.after(0, lambda: text_output.insert(ctk.END, full_translation))
        finally:
            root.after(0, lambda: translate_button.configure(state="normal", text="Перекласти"))
            root.after(0, lambda: stop_button.configure(state="disabled"))  # Не працює кнопка зупинити
            root.after(0, lambda: text_input.configure(state="normal"))  # Відновлюємо input 

    threading.Thread(target=translate).start()

# Зупинка перекладу
def stop_translation_process():
    global stop_translation
    stop_translation = True  # Для зупинки перекладу
    stop_button.configure(state="disabled")  # Кнопка стоп неактивна
    text_input.configure(state="normal")  # input працює

# Очищення перекладу, якщо очищений input
def monitor_text_input(event=None):
    if not text_input.get("1.0", ctk.END).strip():
        text_output.delete("1.0", ctk.END)

# Головний інтерфейс
def main_app():
    global lang_from, lang_to, translate_button, stop_button, text_input
    root.geometry("1000x600")
    root.title("Офлайн перекладач ICC")

    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)

    top_frame = ctk.CTkFrame(root)
    top_frame.grid(row=0, column=0, columnspan=2, pady=10)

    lang_from_label = ctk.CTkLabel(top_frame, text="Переклад з:")
    lang_from_label.grid(row=0, column=0, padx=10, pady=5)

    lang_from = ctk.CTkOptionMenu(top_frame, values=list(language_map_display.keys()))
    lang_from.set("Англійська")
    lang_from.grid(row=0, column=1, padx=10, pady=5)

    lang_to_label = ctk.CTkLabel(top_frame, text="Переклад на:")
    lang_to_label.grid(row=0, column=2, padx=10, pady=5)

    lang_to = ctk.CTkOptionMenu(top_frame, values=list(language_map_display.keys()))
    lang_to.set("Українська")
    lang_to.grid(row=0, column=3, padx=10, pady=5)

    input_frame = ctk.CTkFrame(root)
    input_frame.grid(row=1, column=0, padx=10, sticky="nsew")

    text_input = ctk.CTkTextbox(input_frame, wrap="word")
    text_input.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)
    text_input.bind("<KeyRelease>", monitor_text_input)
    text_input.focus_set()  # Додайте це після створення text_input

    input_scrollbar = ctk.CTkScrollbar(input_frame, command=text_input.yview)
    input_scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)
    text_input.configure(yscrollcommand=input_scrollbar.set)

    output_frame = ctk.CTkFrame(root)
    output_frame.grid(row=1, column=1, padx=10, sticky="nsew")

    global text_output
    text_output = ctk.CTkTextbox(output_frame, wrap="word")
    text_output.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

    output_scrollbar = ctk.CTkScrollbar(output_frame, command=text_output.yview)
    output_scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y)
    text_output.configure(yscrollcommand=output_scrollbar.set)

    add_context_menu(root, text_input, is_output=False)
    add_context_menu(root, text_output, is_output=True)

    translate_button = ctk.CTkButton(root, text="Перекласти", command=translate_text)
    translate_button.grid(row=2, column=0, pady=20, sticky="e")

    stop_button = ctk.CTkButton(root, text="Зупинити", command=stop_translation_process, state="disabled")
    stop_button.grid(row=2, column=1, pady=20, sticky="w")

def add_context_menu(root, text_widget, is_output=False):
    menu = Menu(root, tearoff=0)

    def custom_paste(event=None):
        try:
            clipboard_text = root.clipboard_get()
            text_widget.insert(ctk.INSERT, clipboard_text)
        except Exception as e:
            print(f"Помилка вставки тексту: {e}")
            
    def custom_copy(event=None):
        try:
            selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            root.clipboard_clear()
            root.clipboard_append(selected_text)
            root.update()  
        except tk.TclError:
            print("Немає виділеного тексту для копіювання")

    if not is_output:
        menu.add_command(label="Вирізати", command=lambda: text_widget.event_generate("<<Cut>>"))
        menu.add_command(label="Вставити", command=custom_paste)

    menu.add_command(label="Копіювати", command=custom_copy)


    # Відображення меню
    def show_menu(event):
        menu.post(event.x_root, event.y_root)

    text_widget.bind("<Button-3>", show_menu)

    if not is_output:
        text_widget.bind("<Control-v>", custom_paste)
        text_widget.bind("<Control-V>", custom_paste)


    text_widget.bind("<Control-c>", custom_copy)
    text_widget.bind("<Control-C>", custom_copy)


# Розподіл тексту 
def split_text(text, chunk_size=512):
    words = text.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 <= chunk_size:
            current_chunk += (word + " ") if current_chunk else word
        else:
            chunks.append(current_chunk)
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks


# Основне вікно і прогрес-бар
root = ctk.CTk()
root.title("Завантаження...")

progress_bar = ctk.CTkProgressBar(root, orientation="horizontal", mode="indeterminate")
progress_bar.grid(row=0, column=0, padx=20, pady=20)
progress_bar.start()

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Відносний шлях до M2M100 model 
m2m_model_dir = resource_path("m2m100_model")
language_map_display = {
    "Англійська": "English",
    "Українська": "Ukrainian",
    "Французька": "French",
    "Німецька": "German",
    "Іспанська": "Spanish",
    "Італійська": "Italian",
    "Португальська": "Portuguese",
    "Російська": "Russian",
    "Китайська": "Chinese",
    "Японська": "Japanese",
    "Корейська": "Korean",
    "Хінді": "Hindi",
    "Арабська": "Arabic",
    "Перська": "Persian",
    "Іврит": "Hebrew",
    "Польська": "Polish",
    "Чеська": "Czech",
    "Словацька": "Slovak",
    "Румунська": "Romanian"
}


loading_thread = threading.Thread(target=load_models)
loading_thread.start()

root.mainloop()
