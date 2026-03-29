import tkinter as tk
import resources as r


JEOPARDY_BLUE = "#060CE9"
JEOPARDY_GOLD = "#DBAB51"


class StartScreen:
    def __init__(self, root):
        self.root = root
        self.root.configure(bg=JEOPARDY_BLUE)
        self.root.attributes("-fullscreen", True)

        self.w = root.winfo_screenwidth()
        self.h = root.winfo_screenheight()

        self.canvas = tk.Canvas(
            root, bg=JEOPARDY_BLUE, highlightthickness=0,
            width=self.w, height=self.h
        )
        self.canvas.pack(fill="both", expand=True)

        # Title text (typewriter animation)
        self.title_text = self.canvas.create_text(
            self.w // 2, self.h // 2 - 60,
            text="", font=(r.FONT, 100, "bold"),
            fill=JEOPARDY_GOLD
        )

        # Decorative gold line below title
        cy = self.h // 2 + 40
        self.line = self.canvas.create_line(
            self.w // 2, cy, self.w // 2, cy,
            fill=JEOPARDY_GOLD, width=4
        )

        # "Press ENTER" text (pulsing)
        self.enter_text = self.canvas.create_text(
            self.w // 2, self.h // 2 + 120,
            text="", font=(r.FONT, 28),
            fill=JEOPARDY_GOLD
        )

        self.root.bind("<Return>", lambda e: self.root.destroy())
        self.root.bind("<KP_Enter>", lambda e: self.root.destroy())
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.animate_title("JEOPARDY!", 0)

    def animate_title(self, full_text, idx):
        try:
            if idx <= len(full_text):
                self.canvas.itemconfig(self.title_text, text=full_text[:idx])
                self.root.after(120, lambda: self.animate_title(full_text, idx + 1))
            else:
                self.animate_line(0)
        except tk.TclError:
            pass

    def animate_line(self, progress):
        try:
            cx = self.w // 2
            cy = self.h // 2 + 40
            max_width = 350
            if progress <= max_width:
                self.canvas.coords(self.line, cx - progress, cy, cx + progress, cy)
                self.root.after(3, lambda: self.animate_line(progress + 4))
            else:
                self.pulse_enter(True)
        except tk.TclError:
            pass

    def pulse_enter(self, show):
        try:
            text = "Press ENTER to start" if show else ""
            self.canvas.itemconfig(self.enter_text, text=text)
            self.root.after(700, lambda: self.pulse_enter(not show))
        except tk.TclError:
            pass


def run():
    root = tk.Tk()
    r.detect_font()  # detect best font now that Tk exists
    root.title("Jeopardy!")
    StartScreen(root)
    root.mainloop()


if __name__ == "__main__":
    run()
