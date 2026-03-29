import tkinter as tk
import resources as r
import math


class BLabel(tk.Label):
    def __init__(self, master, team_name, p_width, p_height, p_y, p_x, **kwargs):
        self.y = p_y
        self.x = p_x
        super().__init__(master, **kwargs)
        self.place(width=p_width, height=p_height, x=self.x, y=self.y)

        self.team_label = tk.Label(
            master, text=team_name,
            font=(r.FONT, 20, "bold")
        )
        self.team_label.place(x=self.x + p_width // 2, y=self.y + p_height + 5, anchor="n")

    def animation(self, n):
        def go(n):
            y = self.y
            self.y = self.y - 2
            if n > 0:
                self.place(height=self.winfo_height() + 2, y=y - 2)
                self.master.after(50, lambda: go(n - 1))

        go(n * 2)


def run():
    root = tk.Tk()
    root.title("Jeopardy! - Scores")
    root.attributes("-fullscreen", True)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    num_teams = len(r.teams)
    block_width = min(250, (screen_w - 100) // max(num_teams, 1))
    block_height = 2
    allpoints = sum(r.values) * len(r.categories)

    total_width = block_width * num_teams
    start_x = (screen_w - total_width) / 2
    base_y = (screen_h / 2) + 150

    labels = []
    for i, team in enumerate(r.teams):
        team_text = f"{team['name']}\nwith {r.team_points[i]} points"
        lbl = BLabel(
            root, team_text,
            p_width=block_width, p_height=block_height,
            p_x=start_x + block_width * i, p_y=base_y - block_height,
            background=team["color"], borderwidth=2, relief="solid",
            font=(r.FONT, 20, "bold")
        )
        labels.append(lbl)

    for i, lbl in enumerate(labels):
        if allpoints > 0:
            points_pct = math.ceil(100 * (r.team_points[i] / allpoints))
        else:
            points_pct = 0
        lbl.animation(points_pct)

    root.bind("<Return>", lambda event: root.destroy())
    root.bind("<Escape>", lambda event: root.destroy())

    root.mainloop()


if __name__ == '__main__':
    run()
