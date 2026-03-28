import tkinter as tk
import tkinter.font
import resources as r
import math

grid = []


class LButton(tk.Label):
    def __init__(self, master, p_width, p_height, **kwargs):
        self._text = ""
        self.wertigkeit = 0
        self.gedreht = False
        super().__init__(master, **kwargs)
        self.place(width=p_width, height=p_height)

    def set_org(self, org, richtung, schnelligkeit):
        tmp_x = self.winfo_x()
        if richtung:
            if self.winfo_width() > 3:
                self.place(width=self.winfo_width() - (schnelligkeit * 20), x=tmp_x + schnelligkeit * 10)
                self.master.after(10, lambda: self.set_org(org, True, schnelligkeit))
            else:
                self.lower()
                self.place(x=org[2], y=org[3], width=0, height=org[1])
                self.master.after(10, lambda: self.set_org(org, False, schnelligkeit))
        else:
            if r.to_be_switched_int == 0:
                self.master.after(1000, self.master.destroy)

    def keyboard_input(self, event, org, schnelligkeit):
        num_teams = len(r.teams)
        for i in range(num_teams):
            if event.char == str(i + 1):
                self.config(foreground=r.teams[i]["color"])
                self.update()
                r.team_points[i] += self.wertigkeit
                self.set_org(org, True, schnelligkeit)
                self.master.after(10, lambda: self.master.unbind("<KeyPress>"))
                return
        if event.char == str(num_teams + 1):
            self.config(foreground="black")
            self.update()
            self.set_org(org, True, schnelligkeit)
            self.master.after(10, lambda: self.master.unbind("<KeyPress>"))

    def set_text(self, text):
        font = tk.font.Font(font=self.cget("font"))

        def split_string(s):
            return s.split()

        def join_string(str1, str2):
            return str1 + " " + str2

        def get_text_width(text):
            return self.master.winfo_fpixels(f"{font.measure(text)}p")

        split_list = split_string(text)
        erg_string = ""
        tmp_ergebnis = ""
        for i in split_list:
            if i == "!":
                erg_string += tmp_ergebnis + "\n" + "\n"
                tmp_ergebnis = ""
            else:
                tmp = join_string(tmp_ergebnis, i)
                if get_text_width(tmp) + 100 > self.master.winfo_screenwidth():
                    erg_string += tmp_ergebnis + "\n"
                    tmp_ergebnis = i
                else:
                    tmp_ergebnis = tmp

        erg_string += tmp_ergebnis
        self._text = erg_string

    def get_text(self):
        return self._text

    def visible_text(self):
        self.config(text=self._text)

    def flip(self, org, richtung, schnelligkeit):
        tmp_x = self.winfo_x()
        if richtung:
            if self.winfo_width() > 3:
                self.place(width=self.winfo_width() - (schnelligkeit * 2), x=tmp_x + schnelligkeit)
                self.master.after(10, lambda: self.flip(org, True, schnelligkeit))
            else:
                self.visible_text()
                self.lift()
                self.place(
                    x=self.master.winfo_screenwidth() / 2,
                    y=self.master.winfo_screenheight() / 2,
                    width=0, height=0
                )
                self.master.after(10, lambda: self.flip(org, False, schnelligkeit))
        else:
            if self.winfo_width() < self.master.winfo_screenwidth():
                self.place(width=self.winfo_width() + (schnelligkeit * 20), x=tmp_x - schnelligkeit * 10)
                if self.winfo_height() < self.master.winfo_screenheight():
                    self.place(height=self.winfo_height() + (schnelligkeit * 20), y=self.winfo_y() - schnelligkeit * 10)
                self.master.after(10, lambda: self.flip(org, False, schnelligkeit))

    def start_flip(self):
        if not self.gedreht:
            org = [self.winfo_width(), self.winfo_height(), self.winfo_x(), self.winfo_y()]
            schnelligkeit = int(math.ceil(self.winfo_width() / 100))
            self.flip(org, True, schnelligkeit)
            self.gedreht = True
            self.master.bind("<KeyPress>", lambda event: self.keyboard_input(event, org, schnelligkeit))
        else:
            print("schon gedreht")


def create_grid(root):
    grid.clear()
    for i in range(len(r.categories)):
        grid.append([])
        for j in range(len(r.values) + 1):
            if j == 0:
                tmp = tk.Label(
                    root, text=r.categories[i],
                    font=("Arial Rounded MT Bold", 32, "bold"),
                    background="blue", foreground="#dbab51"
                )
                tmp.place(
                    y=10,
                    x=root.winfo_screenwidth() // len(r.categories) * i + 5,
                    width=root.winfo_screenwidth() // len(r.categories) - 10,
                    height=130
                )
                grid[i].append(tmp)
            else:
                col_width = root.winfo_screenwidth() // len(r.categories)
                tmp_b = LButton(
                    root,
                    font=("Arial Rounded MT Bold", 64, "bold"),
                    background="blue", foreground="#dbab51",
                    p_width=col_width, p_height=150,
                    cursor="hand2"
                )
                tmp_b.place(y=150 * j, x=col_width * i)
                tmp_b.bind("<Button-1>", button_click)
                tmp_b.set_text(r.questions[i][j - 1])
                tmp_b.config(text=f"{r.values[j - 1]}")
                tmp_b.wertigkeit = r.values[j - 1]
                grid[i].append(tmp_b)


def button_click(event):
    r.to_be_switched_int -= 1
    event.widget.unbind("<Button-1>")
    event.widget.config(cursor="")
    event.widget.start_flip()


def run():
    root = tk.Tk()
    root.title("Jeopardy!")
    root.attributes("-fullscreen", True)
    root.configure(bg="blue")
    create_grid(root)
    root.mainloop()


if __name__ == "__main__":
    run()
