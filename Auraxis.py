import customtkinter as ctk
from tkinter import Toplevel, Label, PhotoImage, messagebox, filedialog
import io
import contextlib
import hashlib
import os
import re

# La notification Windows (plyer). Si non installé, tu peux 'pip install plyer'
try:
    from plyer import notification
    PLYER_AVAILABLE = True
except Exception:
    PLYER_AVAILABLE = False

# ---------------- CONFIG -----------------
FILE_EXTENSION = ".auraxis"
SPLASH_IMAGE_PATH = r"YOUR_FILE_LAUNCH.PNG"
SPLASH_DURATION = 3000  # millisecondes

# --------- Verification key (à personnaliser avant publication) ----------
# EMBEDDED_KEY : ta clé alphanumérique de 17 caractères (ex : "A1B2C3D4E5F6G7H8I")
EMBEDDED_KEY = "A1B2C3D4E5F6G7H8I"

# EXPECTED_KEY_HASH : le SHA256 hex digest de la clé ci-dessus (calcule-le localement et colle la valeur ici)
# Exemple : hashlib.sha256(EMBEDDED_KEY.encode()).hexdigest()
EXPECTED_KEY_HASH = "PLACEHOLDER_SHA256_HASH_OF_THE_KEY_REPLACE_ME"

# ---------------- APP -----------------
class AuraxisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="black")
        self.after(0, self.show_splash)

    # -------- Splash screen --------
    def show_splash(self):
        splash = Toplevel(self)
        splash.overrideredirect(True)
        try:
            self.splash_img = PhotoImage(file=SPLASH_IMAGE_PATH)
        except Exception as e:
            # Si image introuvable, on débogue proprement et on continue
            messagebox.showwarning("Avertissement", f"Impossible de charger l'image du splash: {e}")
            self.deiconify()
            self.start_expand()
            return

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        img_width = self.splash_img.width()
        img_height = self.splash_img.height()
        x = (screen_width - img_width) // 2
        y = (screen_height - img_height) // 2
        splash.geometry(f"{img_width}x{img_height}+{x}+{y}")

        label = Label(splash, image=self.splash_img, bg="black")
        label.pack()
        splash.protocol("WM_DELETE_WINDOW", lambda: None)

        self.after(SPLASH_DURATION, lambda: [splash.destroy(), self.deiconify(), self.start_expand()])

    # -------- Effet agrandissement --------
    def start_expand(self):
        target_width, target_height = 800, 600
        steps = 30
        # taille initiale visible
        current_width = 500
        current_height = 300
        width_step = (target_width - current_width) / steps
        height_step = (target_height - current_height) / steps

        self.geometry(f"{current_width}x{current_height}")
        self.main_frame = ctk.CTkFrame(self, fg_color="black")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.title_label = ctk.CTkLabel(
            self.main_frame, text="Auraxis",
            font=("Orbitron", 26, "bold"), text_color="#00aaff"
        )
        self.text_area = ctk.CTkTextbox(
            self.main_frame, width=760, height=400,
            fg_color="#111111", text_color="#00ff88", font=("Consolas", 13)
        )
        self.button_frame = ctk.CTkFrame(self.main_frame, fg_color="black")

        # Bouton de liaison (🔗) — il vérifie la clé
        self.link_btn = ctk.CTkButton(
            self.button_frame, text="🔗 Lier",
            command=self.verify_key_and_unlock,
            fg_color="#ffaa00", hover_color="#cc8800",
            text_color="black", corner_radius=12, width=100
        )
        self.link_btn.grid(row=0, column=0, padx=10)

        # Boutons éditeur (initialement désactivés)
        self.save_btn = ctk.CTkButton(
            self.button_frame, text="💾", command=self.save_file, width=60,
            state="disabled", fg_color="#444444"
        )
        self.save_btn.grid(row=0, column=1, padx=10)

        self.open_btn = ctk.CTkButton(
            self.button_frame, text="📂", command=self.open_file, width=60,
            state="disabled", fg_color="#444444"
        )
        self.open_btn.grid(row=0, column=2, padx=10)

        self.run_btn = ctk.CTkButton(
            self.button_frame, text="▶️", command=self.run_code, width=60,
            state="disabled", fg_color="#444444"
        )
        self.run_btn.grid(row=0, column=3, padx=10)

        step_counter = 0
        def expand_step():
            nonlocal current_width, current_height, step_counter
            if step_counter < steps:
                current_width += width_step
                current_height += height_step
                self.geometry(f"{int(current_width)}x{int(current_height)}")
                step_counter += 1
                self.after(15, expand_step)
            else:
                self.show_main_elements()

        expand_step()

    def show_main_elements(self):
        self.title_label.pack(pady=10, padx=20, anchor='w')
        self.text_area.pack(pady=0, padx=20)
        self.button_frame.pack(pady=10)

    # -------- Extraction et vérification de la clé intégrée --------
    def extract_embedded_key_from_file(self, path):
        """
        Lit le fichier et récupère la valeur de EMBEDDED_KEY (entre quotes).
        Renvoie None si non trouvée.
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return None

        # On cherche la ligne EMBEDDED_KEY = "...." (gère simples/doubles quotes)
        m = re.search(r'EMBEDDED_KEY\s*=\s*[\'"]([A-Za-z0-9]{17})[\'"]', content)
        if m:
            return m.group(1)
        return None

    def verify_key_and_unlock(self):
        """
        Vérifie la clé intégrée en extrayant la clé du fichier et en comparant
        le SHA256 avec EXPECTED_KEY_HASH. Si ok -> active les boutons et notifie.
        """
        try:
            file_path = os.path.abspath(__file__)
        except NameError:
            # En cas d'exécution dans certains environnements où __file__ n'existe pas
            messagebox.showerror("Erreur", "Impossible de déterminer le chemin du script (__file__ non défini).")
            return

        embedded = self.extract_embedded_key_from_file(file_path)
        if not embedded:
            messagebox.showerror("Erreur", "Clé intégrée introuvable dans le fichier.")
            return

        # calculer sha256 de la clé extraite
        h = hashlib.sha256(embedded.encode()).hexdigest()

        if h == EXPECTED_KEY_HASH:
            # Déverrouiller UI
            self.save_btn.configure(state="normal", fg_color="#00aaff", hover_color="#005577", text_color="white")
            self.open_btn.configure(state="normal", fg_color="#00aaff", hover_color="#005577", text_color="white")
            self.run_btn.configure(state="normal", fg_color="#00aaff", hover_color="#005577", text_color="white")

            # change l'apparence du bouton lié pour indiquer succès
            self.link_btn.configure(text="🔗 Lié", fg_color="#44cc44", hover_color="#33aa33", state="disabled")

            # notification desktop (si plyer dispo), sinon messagebox
            if PLYER_AVAILABLE:
                try:
                    notification.notify(
                        title="Auraxis",
                        message="Auraxis est bien lié et pas modifié ✅",
                        timeout=5
                    )
                except Exception:
                    messagebox.showinfo("Info", "Auraxis est bien lié et pas modifié ✅")
            else:
                messagebox.showinfo("Info", "Auraxis est bien lié et pas modifié ✅\n(Installe 'plyer' pour notification native)")

        else:
            messagebox.showerror("Erreur", "La clé a été modifiée ou incorrecte — le programme ne sera pas lié.")

    # -------- Fichiers --------
    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=FILE_EXTENSION,
                                            filetypes=[("Auraxis Files", f"*{FILE_EXTENSION}")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_area.get("1.0", "end-1c"))

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Auraxis Files", f"*{FILE_EXTENSION}")])
        if path and path.endswith(FILE_EXTENSION):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.text_area.delete("1.0", "end")
            self.text_area.insert("1.0", content)
        else:
            messagebox.showerror("Erreur", f"Seuls les fichiers {FILE_EXTENSION} sont supportés.")

    # -------- Run code --------
    def run_code(self):
        code = self.text_area.get("1.0", "end-1c")
        try:
            output_buffer = io.StringIO()
            with contextlib.redirect_stdout(output_buffer):
                exec(code, {})
            output = output_buffer.getvalue().strip()
            messagebox.showinfo("Résultat", output if output else "Le code s'est exécuté sans sortie.")
        except Exception as e:
            messagebox.showerror("Erreur d'exécution", str(e))


if __name__ == "__main__":
    app = AuraxisApp()
    app.mainloop()
