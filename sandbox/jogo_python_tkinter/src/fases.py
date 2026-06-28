import tkinter as tk

class Game(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jogo em Python com Tkinter")
        self.geometry("800x600")
        self.resizable(False, False)
        
        self.current_phase = 1
        self.phase_label = tk.Label(self, text=f"Fase {self.current_phase}", font=("Helvetica", 24))
        self.phase_label.pack(pady=20)

        self.canvas = tk.Canvas(self, width=800, height=600)
        self.canvas.pack()

        self.player = self.canvas.create_oval(395, 295, 405, 305, fill="blue")
        self.canvas.bind("<KeyPress>", self.move_player)
        self.canvas.focus_set()
        
        self.show_menu()

    def show_menu(self):
        self.phase_label.config(text="Menu Inicial", font=("Helvetica", 24))
        self.canvas.delete("all")

        menu_text = "Bem-vindo ao Jogo!\n\nInstruções:\nUse as setas do teclado para mover o jogador.\nExistem 3 fases com dificuldade crescente."
        self.menu_label = tk.Label(self, text=menu_text, font=("Helvetica", 18))
        self.menu_label.pack(pady=20)

        start_button = tk.Button(self, text="Iniciar Jogo", command=self.start_game)
        start_button.pack(pady=10)

    def start_game(self):
        self.phase_label.config(text=f"Fase {self.current_phase}", font=("Helvetica", 24))
        self.canvas.delete("all")
        self.player = self.canvas.create_oval(395, 295, 405, 305, fill="blue")

    def move_player(self, event):
        x, y = 0, 0
        if event.keysym == "Left":
            x -= 10
        elif event.keysym == "Right":
            x += 10
        elif event.keysym == "Up":
            y -= 10
        elif event.keysym == "Down":
            y += 10
        
        self.canvas.move(self.player, x, y)
        
        # Checar se a fase foi concluída (exemplo simples)
        if self.current_phase == 3:
            self.phase_label.config(text="Parabéns! Você completou todas as fases!", font=("Helvetica", 24))
            self.canvas.delete("all")
        else:
            player_coords = self.canvas.coords(self.player)
            if player_coords[0] > 780 or player_coords[1] > 580 or player_coords[2] < 20 or player_coords[3] < 20:
                self.current_phase += 1
                self.start_game()

if __name__ == "__main__":
    game = Game()
    game.mainloop()