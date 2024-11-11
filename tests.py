import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import os
import customtkinter as ctk
from translate2 import resource_path, split_text, add_context_menu, monitor_text_input

class TestTranslatorApp(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.text_input = ctk.CTkTextbox(self.root)
        self.text_widget = ctk.CTkTextbox(self.root)
        self.text_widget.insert("1.0", "Тестовий текст")
        self.text_widget.tag_add("sel", "1.0", "1.5")  

    def tearDown(self):
        self.root.destroy()

    @patch('os.path.abspath')
    def test_resource_path(self, mock_abspath):
        mock_abspath.return_value = "/mock/base/path"
        result = resource_path("m2m100_model")
        self.assertEqual(os.path.normpath(result), os.path.normpath("/mock/base/path/m2m100_model"))

    def test_chunk_size_limit(self):
        text = " ".join(["word"] * 200)  # текст з 200 слів
        chunk_size = 50
        chunks = split_text(text, chunk_size)
        
        # жоден фрагмент не перевищує розміру chunk_size
        for chunk in chunks:
            self.assertTrue(len(chunk) <= chunk_size)
    
    def test_no_word_split(self):
        text = "Це простий тест, щоб переконатися, що слова не розділяються частинами."
        chunk_size = 20
        chunks = split_text(text, chunk_size)
        
        # слова не розділяються у фрагментах
        for chunk in chunks:
            words = chunk.split()
            for word in words:
                self.assertFalse(" " in word)

    def test_correct_number_of_chunks(self):
        text = " ".join(["word"] * 100)  # текст зі 100 слів
        chunk_size = 15  
        chunks = split_text(text, chunk_size)
        
        expected_number_of_chunks = len(text) // chunk_size + (1 if len(text) % chunk_size else 0)
        self.assertTrue(len(chunks) == expected_number_of_chunks)

    def setUp(self):
        self.root = tk.Tk()
        self.text_widget = ctk.CTkTextbox(self.root)
        self.text_widget.insert("1.0", "Тестовий текст")
        self.text_widget.tag_add("sel", "1.0", "1.5")  
        self.root.clipboard_clear()  
        self.after_ids = []  

    def tearDown(self):
        for after_id in self.after_ids:
            try:
                self.root.after_cancel(after_id)
            except Exception as e:
                print(f"Помилка під час скасування виклику after: {e}")

        try:
            self.root.destroy()
        except Exception as e:
            print(f"Помилка під час знищення root: {e}")

    @patch('tkinter.Menu')
    def test_add_context_menu_creation(self, mock_menu):
        menu_mock = MagicMock()
        mock_menu.return_value = menu_mock
        add_context_menu(self.root, self.text_widget, is_output=False)

        self.assertTrue(menu_mock.add_command.called, "Команда не була додана до меню")
        menu_mock.add_command.assert_any_call(label="Копіювати", command=unittest.mock.ANY)
        menu_mock.add_command.assert_any_call(label="Вставити", command=unittest.mock.ANY)

    def test_custom_copy_function(self):
        add_context_menu(self.root, self.text_widget, is_output=False)
        self.text_widget.event_generate("<Control-c>")
        self.root.update()  
        clipboard_text = self.root.clipboard_get().strip()  
        self.assertEqual(clipboard_text, "Тестов", "Текст у буфері обміну не відповідає очікуваному")

    def test_custom_paste_function(self):
        add_context_menu(self.root, self.text_widget, is_output=False)
        self.root.clipboard_clear()
        self.root.clipboard_append("Вставлений текст")
        self.root.update()  
        self.text_widget.event_generate("<Control-v>")
        self.root.update()  
        inserted_text = self.text_widget.get("1.0", ctk.END).strip()
        self.assertTrue("Вставлений текст" in inserted_text, "Текст не вставлений у віджет")

    def test_no_copy_when_no_selection(self):
        self.text_widget.tag_remove("sel", "1.0", "end")  
        add_context_menu(self.root, self.text_widget, is_output=True)
        with patch.object(self.root, 'clipboard_append') as mock_clipboard:
            self.text_widget.event_generate("<Control-c>")
            mock_clipboard.assert_not_called()
            
            
if __name__ == "__main__":
    unittest.main()
