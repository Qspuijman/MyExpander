import re
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import csv
import keyboard
import argparse
import sys


def main():
    filename = get_args()
    filename = process_filename(filename)
    if not filename_isvalid(filename):
        sys.exit("Not a valid file")
    root = Tk()
    Gui(root, filename)
    root.mainloop()


class Gui:

    # Draws the main application window. Sets shortcuts.
    def __init__(self, root, filename) -> None:
        self.filename = filename
        self.dictionary = self.get_dictionary()
        self.temp_keys = [key for key in self.dictionary]
        self.loaded = []
        root.title("MyExpander")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        root.bind("<FocusIn>", self.remove_listener)
        root.bind("<FocusOut>", self.add_listener)
        root.bind("<Control-Return>", self.save_entry)
        root.bind("<Control-Delete>", self.delete_entry)

        # Main window inside root
        main = ttk.Frame(
            root,
            padding=5,
        )
        main.grid(column=0, row=0, sticky="NESW")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # first row of main: combobox, save and delete Button
        savebutton = ttk.Button(main, command=self.save_entry, text="Save")
        savebutton.grid(row=0, column=2, sticky="E")

        # Deletes entries
        deletebutton = ttk.Button(main, command=self.delete_entry, text="Delete")
        deletebutton.grid(row=0, column=3, sticky="E")

        # Combobox for the entries in the dict
        self.selected_entry_name = StringVar()
        self.entries_box = ttk.Combobox(
            main,
            textvariable=self.selected_entry_name,
        )
        self.entries_box["values"] = [key for key in sorted(self.temp_keys)]
        self.selected_entry_name.trace_add("write", callback=self.select_entry)
        self.entries_box.grid(row=0, column=0, columnspan=2, sticky="WE")
        self.entries_box.focus()

        # Text field
        self.entries_text = Text(main, height=40, width=80, wrap="word")
        self.entries_text.grid(row=1, column=0, columnspan=4, sticky="NESW")
        self.entries_text.bind("<Shift-Tab>", lambda *args: self.entries_box.focus())

        # scrollbar for text field
        entries_scrollbar = ttk.Scrollbar(
            main, orient=VERTICAL, command=self.entries_text.yview
        )
        self.entries_text.configure(yscrollcommand=entries_scrollbar.set)
        entries_scrollbar.grid(column=4, row=1, sticky="NSEW")

    # Loads existing dictionary into app as "self.dictionary"
    def get_dictionary(self, *args) -> dict:
        dict = {}
        try:
            with open(self.filename, newline="") as csvfile:
                reader = csv.reader(csvfile)
                dict = {row[0]: row[1] for row in reader}
        except FileNotFoundError:
            pass
        return dict

    # function that updates the dropdown list of the select entry box. Is called on every keystroke
    def select_entry(self, *args):
        temp = []
        if self.selected_entry_name.get() in self.temp_keys:
            self.update_textbox(self.dictionary[self.selected_entry_name.get()])
        else:
            self.update_textbox("")
            for key in self.temp_keys:
                if key.startswith(self.selected_entry_name.get()):
                    temp.append(key)
            self.entries_box["values"] = [key for key in sorted(temp)]

    # This works as well.
    def update_textbox(self, entry: str) -> None:
        self.entries_text.delete("1.0", "end")
        self.entries_text.insert("1.0", entry)

    # Saves new csv dict with updated/appended entry.
    # Updates the temp var. to allow for usage without re-reading file.
    # Displays an info message to confirm that entry has been updated.
    def save_entry(
        self,
        *args,
    ):
        entry = self.selected_entry_name.get().strip()
        content = self.entries_text.get("1.0", "end").strip()
        if (
            len(entry) > 0
            and len(content) > 0
            and (re.search(r"[\S][\s|_|\-]+[\S]", entry) == None)
        ):
            self.dictionary[entry] = content
            self.temp_keys = [key for key in self.dictionary]
            with open(self.filename, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                for key in self.dictionary:
                    writer.writerow([key, self.dictionary[key]])
            messagebox.showinfo(
                title=f"Update '{entry}'", message=f"Entry: '{entry}' has been updated"
            )
        else:
            messagebox.showwarning(
                title="Invalid entry",
                message="You tried to save an invalid entry.",
            )

    # Deletes entry from both self.dict as well as dict.csv
    def delete_entry(
        self,
        *args,
    ) -> None:
        entry = self.selected_entry_name.get().strip()
        if entry in self.dictionary:
            if messagebox.askokcancel(
                title=f"Delete entry: '{entry}'",
                message=f"Are you sure you want to permanently delete entry: '{entry}'?",
            ):
                del self.dictionary[entry]
                self.temp_keys = [key for key in self.dictionary]
                with open(self.filename, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    for key in self.dictionary:
                        writer.writerow([key, self.dictionary[key]])
                messagebox.showinfo(
                    title=f"Deleted '{entry}'",
                    message=f"Entry '{entry}' has been successfully deleted from the dictionary.",
                )
        else:
            messagebox.showinfo(title="Not Found", message=f"Entry '{entry}' not found")

    # adds expander function. Is called when window out of focus
    def add_listener(
        self,
        *args,
    ):
        if not self.loaded:
            for key in self.dictionary:
                handler = keyboard.add_abbreviation(
                    key, f"{self.dictionary[key]} ", timeout=5
                )
                self.loaded.append(handler)

    # removes expander function. Is called when window in focus.
    def remove_listener(self, *args):
        if self.loaded:
            for handler in self.loaded:
                keyboard.remove_word_listener(handler)
                self.loaded.remove(handler)


# These are not being used yet. For specifying other dictionaries to use. Maybe in future release
def get_args():
    parser = argparse.ArgumentParser(
        description="While running, this program adds a text expander that expands text in 'dictionary.csv' in the same folder. If no such file exists, it is created. The text is expanded while the program is not in focus. Text expanding stops when the program is in focus or closed"
    )
    parser.add_argument(
        "-f",
        help="The name of the dictionary you want to initialize; if not present in the current directory this program will create it. Must be a .csv file",
        default="dictionary.csv",
        type=str,
    )
    return parser.parse_args().f


# These are not being used yet. For specifying other dictionaries to use. Maybe in future release
def process_filename(filename):
    filename = filename.strip()
    if not filename.endswith("csv") and not "." in filename:
        filename = f"{filename + '.csv'}"
    return filename


# These are not being used yet. For specifying other dictionaries to use. Maybe in future release
def filename_isvalid(filename):
    return filename.endswith(".csv")


def stats(filename):
    rowcount = 0
    with open(filename, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            rowcount += 1
    return rowcount


if __name__ == "__main__":
    main()
