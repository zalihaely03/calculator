import ast
import math
import operator
import re
import tkinter as tk
from fractions import Fraction

# ---------- Tema ----------
BG, PANEL, TEKS_INFO = "#0B1220", "#131C31", "#7C8BA8"
NUM = ("#1E293B", "#2C3B58")     # (normal, hover)
FUNGSI = ("#334155", "#475773")
OPERATOR = ("#F59E0B", "#FBBF24")
SAMADENGAN = ("#10B981", "#34D399")

TOMBOL = ["AC", "⌫", "%", "÷",
          "√", "^", "()", "×",
          "7", "8", "9", "-",
          "4", "5", "6", "+",
          "1", "2", "3",
          "±", "0", ".", "="]
LABEL = {"^": "xʸ", "()": "( )"}
KEYMAP = {"Return": "=", "KP_Enter": "=", "BackSpace": "⌫", "Escape": "AC", "F9": "±",
          "*": "×", "x": "×", "/": "÷", ",": ".", "(": "()", ")": "()"}
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}


# ---------- Matematika ----------
def akar(x):
    x = Fraction(x)
    if x < 0:
        raise ValueError("Akar negatif")
    n, d = math.isqrt(x.numerator), math.isqrt(x.denominator)
    return Fraction(n, d) if n * n == x.numerator and d * d == x.denominator else math.sqrt(x)


def pangkat(a, b):
    a, b = Fraction(a), Fraction(b)
    if b.denominator == 1:  # pangkat bulat -> hasil eksak
        besar = max(a.numerator.bit_length(), a.denominator.bit_length())
        if abs(a) not in (0, 1) and abs(b) * besar > 4000:
            raise ValueError("Terlalu besar")
        return a ** int(b)
    if a < 0:
        raise ValueError("Error")
    return float(a) ** float(b)  # pangkat pecahan, mis. 4^0.5


def format_hasil(x):
    if isinstance(x, Fraction) and x.denominator == 1:
        s = str(abs(x.numerator))
        if len(s) > 15:  # bilangan sangat besar -> notasi ilmiah
            m = (s[0] + "." + s[1:7]).rstrip("0").rstrip(".")
            return f"{'-' if x < 0 else ''}{m}e+{len(s) - 1}"
        return str(x.numerator)
    s = f"{float(x):.10f}".rstrip("0").rstrip(".")
    return s if s.strip("-0") or x == 0 else f"{float(x):.3e}"


class Persen(Fraction):
    """Angka berakhiran %. Di kanan + atau -, dihitung dari nilai di kirinya:
    200+10% = 220, 200-10% = 180. Selain itu 10% = 0.1 (200×10% = 20)."""

    def __radd__(self, a):
        return a + a * Fraction(self)

    def __rsub__(self, a):
        return a - a * Fraction(self)


def nilai(n):
    """Evaluator aman berbasis AST (tanpa eval)."""
    if isinstance(n, ast.Call):
        nama = n.func.id
        if nama == "S":
            return akar(nilai(n.args[0]))
        x = Fraction(n.args[0].value)
        return Persen(x / 100) if nama == "P" else x
    if isinstance(n, ast.UnaryOp):
        v = nilai(n.operand)
        return -v if isinstance(n.op, ast.USub) else v
    if isinstance(n, ast.BinOp):
        a, b = nilai(n.left), nilai(n.right)
        return pangkat(a, b) if isinstance(n.op, ast.Pow) else OPS[type(n.op)](a, b)
    raise ValueError("Error")


# ---------- Tombol membulat ----------
def bulat(c, x1, y1, x2, y2, r, **kw):
    p = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
         x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
         x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]
    return c.create_polygon(p, smooth=True, **kw)


class Tombol(tk.Canvas):
    def __init__(self, master, label, warna, fg, perintah):
        super().__init__(master, bg=BG, highlightthickness=0, bd=0, cursor="hand2")
        self.label, (self.warna, self.hover), self.fg, self.perintah = label, warna, fg, perintah
        self.sorot = self.ditekan = False
        self.bind("<Configure>", lambda e: self.gambar())
        self.bind("<Enter>", lambda e: self.atur(sorot=True))
        self.bind("<Leave>", lambda e: self.atur(sorot=False, ditekan=False))
        self.bind("<ButtonPress-1>", lambda e: self.atur(ditekan=True))
        self.bind("<ButtonRelease-1>", self.lepas)

    def atur(self, **kw):
        self.__dict__.update(kw)
        self.gambar()

    def lepas(self, ev):
        aktif = self.ditekan
        self.atur(ditekan=False)
        if aktif and 0 <= ev.x <= self.winfo_width() and 0 <= ev.y <= self.winfo_height():
            self.perintah()

    def gambar(self):
        self.delete("all")
        w, h, m = self.winfo_width(), self.winfo_height(), 5 if self.ditekan else 2
        bulat(self, m, m, w - m, h - m, 18, fill=self.hover if self.sorot else self.warna, outline="")
        self.create_text(w / 2, h / 2, text=self.label, fill=self.fg, font=("Helvetica", 20, "bold"))


# ---------- Aplikasi ----------
class Kalkulator:
    def __init__(self):
        self.e = self.riwayat = self.pesan = self.lanjut = ""
        self.baru = False  # True tepat setelah "="

        self.root = root = tk.Tk()
        root.title("Kalkulator")
        root.geometry("360x560")
        root.configure(bg=BG)
        root.resizable(False, False)

        atas = tk.Frame(root, bg=PANEL)
        atas.pack(padx=14, pady=(16, 8), fill="x")
        self.info = tk.Label(atas, bg=PANEL, fg=TEKS_INFO, font=("Helvetica", 12), anchor="e")
        self.info.pack(fill="x", padx=16, pady=(14, 0))
        self.layar = tk.Label(atas, bg=PANEL, fg="white", anchor="e", height=2)
        self.layar.pack(fill="x", padx=16, pady=(0, 12))
        tk.Frame(atas, bg=OPERATOR[0], height=3).pack(fill="x")  # garis aksen

        grid = tk.Frame(root, bg=BG)
        grid.pack(expand=True, fill="both", padx=9, pady=(0, 10))
        for i, t in enumerate(TOMBOL):
            if t == "=":
                warna, fg = SAMADENGAN, "white"
            elif t in ("÷", "×", "-", "+"):
                warna, fg = OPERATOR, "white"
            elif t.isdigit() or t in (".", "±"):
                warna, fg = NUM, "white"
            else:
                warna, fg = FUNGSI, "#F87171" if t == "AC" else "#7DD3FC"
            Tombol(grid, LABEL.get(t, t), warna, fg, lambda t=t: self.tekan(t)).grid(
                row=i // 4, column=i % 4, sticky="nsew", padx=3, pady=3)
        for i in range(6):
            grid.rowconfigure(i, weight=1)
        for i in range(4):
            grid.columnconfigure(i, weight=1)

        root.bind("<Key>", self.tombol_keyboard)
        self.tampil()
        root.mainloop()

    def tampil(self):
        teks = self.pesan or self.e or "0"
        if len(teks) > 28:
            teks = "…" + teks[-27:]
        ukuran = 32 if len(teks) <= 11 else 24 if len(teks) <= 18 else 16
        self.layar.config(text=teks, font=("Helvetica", ukuran, "bold"))
        self.info.config(text=self.riwayat[-40:])

    def tombol_keyboard(self, ev):
        t = KEYMAP.get(ev.keysym) or KEYMAP.get(ev.char, ev.char)
        if t in TOMBOL:
            self.tekan(t)

    def tekan(self, t):
        if t == "=":
            return self.hitung()
        e, baru, self.baru = self.e, self.baru, False
        op = t in ("+", "-", "×", "÷", "^")
        if baru:  # setelah "=": operator melanjutkan hasil, ± membalik hasil, input lain mulai baru
            e = self.lanjut if op else self.e if t == "±" else ""
        self.pesan = self.riwayat = ""
        kali = "×" if e[-1:].isdigit() or e[-1:] in (")", ".", "%") else ""  # perkalian implisit
        sambung = "×" if e.endswith((")", "%")) else ""
        angka = re.search(r"\d*\.?\d*$", e).group()  # angka yang sedang diketik

        if t == "AC":
            e = ""
        elif t == "⌫":
            e = e[:-2] if e.endswith(("√(", "(-")) else e[:-1]
        elif op:
            if t == "-" and e.endswith(("×", "÷", "^")):  # 5×-3, 2^-1
                e += t
            else:  # ganti operator terakhir, cegah "5++3"
                e = re.sub(r"[+\-×÷^]+$", "", e)
                if e and not e.endswith("(") or t == "-":
                    e += t
        elif t == "±":
            if re.fullmatch(r"-?[\d.]+%?", e):  # seluruh isi layar hanya satu angka
                e = e[1:] if e[0] == "-" else "-" + e
            elif m := re.search(r"\(-([\d.]*%?)$", e):  # angka terakhir sudah negatif -> positifkan
                e = e[:m.start()] + m.group(1)
            elif m := re.search(r"[\d.]+%?$", e):  # negatifkan angka terakhir
                e = e[:m.start()] + "(-" + m.group()
            elif not e or e[-1] in "+-×÷^(":
                e += "(-"
        elif t.isdigit():
            if angka == "0":  # cegah "007"
                e = e[:-1] + t
            elif len(angka) < 15:
                e += sambung + t
        elif t == ".":
            if "." not in angka:  # cegah "1.2.3"
                e += "." if angka else sambung + "0."
        elif t == "%":
            if e[-1:].isdigit():  # % hanya setelah angka
                e += t
        elif t == "()":
            tutup = e.count("(") > e.count(")") and (e[-1:].isdigit() or e[-1:] in (")", "."))
            e += ")" if tutup else kali + "("
        elif t == "√":
            e += kali + "√("

        if len(e) <= 60:
            self.e = e
        self.tampil()

    def hitung(self):
        e = re.sub(r"[+\-×÷^(√]+$", "", self.e)  # buang operator yang menggantung
        if not e or self.baru:
            return
        e += ")" * (e.count("(") - e.count(")"))  # tutup kurung otomatis
        try:
            if not re.fullmatch(r"[\d.+\-×÷^()√%]+", e):
                raise ValueError("Error")
            # Angka jadi Fraction agar eksak (0.1+0.2=0.3, 1÷3×3=1)
            kode = re.sub(r"(\d+\.?\d*)(%?)", lambda m: f'{"P" if m[2] else "F"}("{m[1].rstrip(".")}")', e)
            kode = kode.replace("×", "*").replace("÷", "/").replace("√", "S").replace("^", "**")
            hasil = nilai(ast.parse(kode, mode="eval").body)
            teks = format_hasil(hasil)
        except ZeroDivisionError:
            return self.galat("Tidak bisa dibagi 0")
        except ValueError as ex:
            return self.galat(str(ex) if str(ex).startswith(("Akar", "Terlalu")) else "Error")
        except Exception:
            return self.galat("Error")

        # Jika dilanjutkan dengan operator, pakai pecahan eksak (bukan desimal bulat)
        pecahan = isinstance(hasil, Fraction) and hasil.denominator != 1
        self.lanjut = f"({hasil.numerator}÷{hasil.denominator})" if pecahan else teks
        self.riwayat, self.e, self.baru = e + " =", teks, True
        self.tampil()

    def galat(self, pesan):
        self.e = self.riwayat = self.lanjut = ""
        self.pesan, self.baru = pesan, False
        self.tampil()


if __name__ == "__main__":
    Kalkulator()