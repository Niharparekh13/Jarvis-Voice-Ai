import tkinter as tk
from tkinter import messagebox, simpledialog
from core.utils import load_memory, save_memory

def show_memory_editor():
    memory = load_memory()

    def refresh_display():
        listbox.delete(0, tk.END)
        for key, value in memory.items():
            listbox.insert(tk.END, f"{key}: {value}")

    def edit_selected():
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Edit", "Please select a memory item to edit.")
            return
        item = listbox.get(selection[0])
        key = item.split(":")[0].strip()
        new_value = simpledialog.askstring("Edit Memory", f"Enter new value for '{key}':", initialvalue=memory[key])
        if new_value is not None:
            memory[key] = new_value
            save_memory(memory)
            refresh_display()

    def delete_selected():
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Delete", "Please select a memory item to delete.")
            return
        item = listbox.get(selection[0])
        key = item.split(":")[0].strip()
        if messagebox.askyesno("Confirm", f"Delete '{key}' from memory?"):
            del memory[key]
            save_memory(memory)
            refresh_display()

    window = tk.Tk()
    window.title("Jarvis Memory Viewer")
    window.geometry("600x400")

    listbox = tk.Listbox(window, font=("Arial", 12), selectmode=tk.SINGLE)
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    btn_frame = tk.Frame(window)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="Edit", command=edit_selected).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Delete", command=delete_selected).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Close", command=window.destroy).pack(side=tk.LEFT, padx=5)

    refresh_display()
    window.mainloop()