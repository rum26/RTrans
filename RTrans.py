from deep_translator.exceptions import RequestError, TooManyRequests
from requests.exceptions import ConnectionError, Timeout
from deep_translator import GoogleTranslator
import tkinter as tk
import threading
import pyperclip
import keyboard
import json
import time
import os


last_copy_time = 0
current_label = None
copy_handler = None


patch_documents = os.path.join(os.environ["USERPROFILE"], "Documents")


if os.path.exists(f"{patch_documents}/pdict.json"):
    with open(f"{patch_documents}/pdict.json", 'r', encoding='UTF-8') as fb:
        Pdict = json.load(fb)
else:
    Pdict = {}


def save_pdict():
    with open(f"{patch_documents}/pdict.json", "w", encoding="UTF-8") as file:
        json.dump(Pdict, file, ensure_ascii=False, indent=2)


def translate_word_auto(word):
    try:
        # пытаемся перевести на русский
        translation = GoogleTranslator(source='auto', target='ru').translate(word)
        # если слово переведено идентично (значит, оно уже русское), переводим на английский
        if translation.lower() == word.lower():
            translation = GoogleTranslator(source='auto', target='en').translate(word)
            # наверное я хочу так назвать переменную
            translation = translation.lower()
        return translation
    except RequestError:
        return "❌ ошибка: RequestError"
    except TooManyRequests:
        return "❌ ошибка: TooManyRequests"
    except ConnectionError:
        return "❌ ошибка: ConnectionError"
    except Timeout:
        return "❌ ошибка: Timeout"


def text_processing(text):
    if '_' in text:
        text = text.replace('_', ' ')
    text = text.lower()

    if Pdict.get(text):
        answer = Pdict[text]
        clr = "#40E0D0"  # фраза из словаря
    else:
        answer = translate_word_auto(text)
        Pdict[text] = answer
        Pdict[answer] = text
        save_pdict()
        clr = 'yellow'  # фраза из интернета.
    if ',' not in answer:
        answer = answer.replace(' ', '_')
    return answer, clr


def copy_and_paste(text):
    if copy_handler:
        pyperclip.copy(text)
        time.sleep(0.2)
        keyboard.send('alt+tab')
        time.sleep(0.2)
        keyboard.press_and_release('ctrl+v')
        time.sleep(0.2)


root = tk.Tk()


def close_window(_):
    root.destroy()


root.overrideredirect(True)
root.attributes("-alpha", 0.1)
screen_width = root.winfo_screenwidth()
window_width = int(screen_width / 2)
x_position = int((screen_width - window_width) / 2)
root.geometry(f"{window_width}x30+{x_position}+0")
root.configure(bg="black")
bottom_line = tk.Frame(root, bg="#40E0D0", height=1)
bottom_line.pack(side="bottom", fill="x")


def update_label_text(text, clr):
    global current_label
    if current_label:
        current_label.destroy()

    current_label = tk.Label(
        root,
        text=text,
        bg="black",
        fg=clr,
        font=("Consolas", 16, "bold"),
        justify="center",
        anchor="center"
    )
    current_label.pack(expand=True, fill='both')
    current_label.after(6000, current_label.destroy)


def main(text):
    root.attributes("-alpha", 0.85)
    global copy_handler
    copy_handler = True
    answer, clr = text_processing(text)
    root.attributes('-topmost', True)
    root.lift()
    update_label_text(answer, clr)
    root.bind('<Button-1>', lambda event: copy_and_paste(answer))

    def disable_copy():
        global copy_handler
        copy_handler = None
        root.attributes('-topmost', False)
        root.attributes("-alpha", 0.1)
        root.lower()

    root.after(6000, disable_copy)


def on_copy():
    global last_copy_time
    now = time.time()
    if now - last_copy_time < 0.5:
        text = pyperclip.paste().strip()
        if len(text.split()) > 5:
            return
        main(text)
    last_copy_time = now


def keep_hooks_alive():
    while True:
        time.sleep(300)
        try:
            keyboard.unhook_all()
            keyboard.add_hotkey("ctrl+c", on_copy)
        except:
            pass


threading.Thread(target=keep_hooks_alive, daemon=True).start()


keyboard.add_hotkey("ctrl+c", on_copy)

root.bind('<Button-3>', close_window)
root.mainloop()
