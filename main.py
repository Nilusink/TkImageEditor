"""
Author:
Nilusink
https://github.com/Nilusink/
"""
from PIL.ImageEnhance import Color, Sharpness, Brightness, Contrast
from fractions import Fraction
from tkinter import filedialog
from PIL import Image, ImageTk
import customtkinter as ctk
from sys import platform
import tkinter as tk
import typing as tp

ctk.set_appearance_mode("system")
if platform == "linux":  # since for now ctk will set linux always to light
    ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


def from_rgb(rgb):
    """translates a rgb tuple of int to a tkinter friendly color code
    """
    r, g, b = rgb
    return f'#{r:02x}{g:02x}{b:02x}'


class SliderValue(tp.TypedDict):
    enhancer: tp.Type[Color] | tp.Type[Sharpness] | tp.Type[Brightness] | tp.Type[Contrast]
    slider: ctk.CTkSlider
    entry: ctk.CTkEntry
    func: tp.Callable
    value: float


class Window(ctk.CTk):
    p1 = ...
    p2 = ...
    __p1x: float = 0
    __p1y: float = 0
    __p1lat: float = 0
    __p1long: float = 0
    __p2x: float = 0
    __p2y: float = 0
    __p2lat: float = 0
    __p2long: float = 0
    point_size: int = 10
    world_bg: tuple = (100, 100, 200)
    now_frame: tk.Frame = ...
    icon_size: int = 128
    scale: float = 1

    image_path: str = "./images/globe_texture.jpg"
    currently_placing: ctk.CTkCanvas
    aspect_ratio: tuple[int, int]
    window_size: tuple[int, int]
    placed_objects: list
    images: list[Image]
    placeable: list

    def __init__(self) -> None:
        super().__init__()

        # mutable defaults
        self.currently_placing = ctk.CTkCanvas(self)

        self.original_image = Image.open(self.image_path)
        self.window_size = self.original_image.size
        tmp = Fraction(*self.original_image.size)
        self.aspect_ratio = tmp.numerator, tmp.denominator

        # set window options
        self.title("Image Editor")
        width, height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (width, height))

        # menu bar
        self.menu = tk.Menu(self)
        self.submenu = tk.Menu(self.menu, tearoff=0)
        self.submenu.add_command(label="Save", command=lambda: self.save())
        self.submenu.add_command(label="Open", command=lambda: self.open())
        self.submenu.add_separator()
        self.submenu.add_command(label="Quit...", command=self.end)
        self.submenu.add_command(label="Quit without saving", command=lambda: self.end(save=False))
        self.menu.add_cascade(label="File", menu=self.submenu)

        self.config(menu=self.menu)

        # bind
        self.bind("<F11>", lambda _event: self.attributes("-fullscreen", True))
        self.bind("<Configure>", self.on_resize)
        self.bind("<Alt-Key-F4>", self.end)
        self.bind("<F5>", self.update_game_frame)
        self.bind("<Escape>", self.end)

        # initialize tool window
        # configure grid
        self.object_settings = ctk.CTkFrame(self, corner_radius=20)

        self.object_settings.columnconfigure(tuple(range(4)), weight=1, pad=5)
        self.object_settings.rowconfigure(tuple(range(10)), weight=0, pad=5)

        # create dicts
        self.saturation: SliderValue = {}
        self.sharpness: SliderValue = {}
        self.contrast: SliderValue = {}
        self.brightness: SliderValue = {}

        # create objects for tool window
        t_f_1 = ctk.CTkFrame(self.object_settings)
        t_f_1.columnconfigure(0, weight=1)
        self.object_type = ctk.CTkLabel(
            t_f_1,
            text="Image Settings",
            justify=tk.CENTER,
            text_font=("Roboto Medium", -16)
        )
        self.object_type.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)

        lab1 = ctk.CTkLabel(self.object_settings, text="", justify="center")

        lab1_1 = ctk.CTkLabel(self.object_settings, text="Saturation", justify="center")
        slider = ctk.CTkSlider(
            self.object_settings, from_=-1, to=3, command=lambda v: self.update_value(self.saturation, v)
        )
        entry = ctk.CTkEntry(self.object_settings, justify="center")
        self.saturation.update({
            "slider": slider,
            "entry": entry,
            "value": 0,
            "enhancer": Color
        })

        lab1_2 = ctk.CTkLabel(self.object_settings, text="Sharpness", justify="center")
        slider = ctk.CTkSlider(
            self.object_settings, from_=-1, to=3, command=lambda v: self.update_value(self.sharpness, v)
        )

        entry = ctk.CTkEntry(self.object_settings, justify="center")
        self.sharpness.update({
            "slider": slider,
            "entry": entry,
            "value": 0,
            "enhancer": Sharpness
        })

        lab2_1 = ctk.CTkLabel(self.object_settings, text="Contrast", justify="center")
        slider = ctk.CTkSlider(
            self.object_settings, from_=-1, to=3,
            command=lambda v: self.update_value(self.contrast, v)
        )
        entry = ctk.CTkEntry(self.object_settings, justify="center")
        self.contrast.update({
            "slider": slider,
            "entry": entry,
            "value": 0,
            "enhancer": Contrast
        })

        lab2_2 = ctk.CTkLabel(self.object_settings, text="Brightness", justify="center")
        slider = ctk.CTkSlider(
            self.object_settings, from_=0, to=3,
            command=lambda v: self.update_value(self.brightness, v)
        )
        entry = ctk.CTkEntry(self.object_settings, justify="center")
        self.brightness.update({
            "slider": slider,
            "entry": entry,
            "value": 0,
            "enhancer": Brightness
        })

        reset_btn = ctk.CTkButton(
            self.object_settings, text="Reset Values", command=self.reset_values
        )

        # place on grid
        t_f_1.grid(row=0, column=0, columnspan=4, sticky="nsew", padx=20, pady=20)

        lab1.grid(row=2, column=1, columnspan=2, sticky=tk.NSEW)

        lab1_1.grid(row=3, column=0, sticky=tk.NSEW)
        self.saturation["slider"].grid(row=3, column=1, columnspan=2, sticky=tk.NSEW, pady=5)
        self.saturation["entry"].grid(row=3, column=3, sticky="we", padx=10)

        lab1_2.grid(row=4, column=0, sticky=tk.NSEW)
        self.sharpness["slider"].grid(row=4, column=1, columnspan=2, sticky=tk.NSEW, pady=5)
        self.sharpness["entry"].grid(row=4, column=3, sticky="we", padx=10)

        lab2_1.grid(row=7, column=0, sticky=tk.NSEW)
        self.contrast["slider"].grid(row=7, column=1, columnspan=2, sticky=tk.NSEW, pady=5)
        self.contrast["entry"].grid(row=7, column=3, sticky="we", padx=10)

        lab2_2.grid(row=8, column=0, sticky=tk.NSEW)
        self.brightness["slider"].grid(row=8, column=1, columnspan=2, sticky=tk.NSEW, pady=5)
        self.brightness["entry"].grid(row=8, column=3, sticky="we", padx=10)

        reset_btn.grid(row=10, column=1, columnspan=2, sticky=tk.NSEW, pady=30)

        # create canvases
        self.game_can_center = ctk.CTkFrame(self, highlightthickness=0)
        self.game_can = ctk.CTkCanvas(self.game_can_center, highlightthickness=0)

        # pack canvases
        self.object_settings.grid(column=0, row=0, sticky="nsew", padx=20, pady=20)
        self.game_can_center.grid(column=1, row=0, sticky="nsew", padx=10, pady=10)
        self.game_can_center.grid_columnconfigure(0, weight=1)
        self.game_can_center.grid_rowconfigure(0, weight=1)
        self.game_can.grid()

        # configure columns
        self.grid_rowconfigure(0, weight=1, pad=0)
        self.grid_columnconfigure(0, weight=0, pad=0)
        self.grid_columnconfigure(1, weight=1, pad=3)

        # initial functions
        self.update_game_frame()

        # draw world map
        self.resized_image = self.original_image.resize(self.game_window_size)
        self.enhanced_image: Image = ...
        self.tk_image = ImageTk.PhotoImage(self.resized_image)
        self.x_off, self.y_off = self.game_window_size
        self.x_off /= 2
        self.y_off /= 2
        self.game_can.create_image(self.x_off, self.y_off, image=self.tk_image)

        self.reset_values()

        self.focus_set()

    @property
    def game_window_size(self) -> tuple[int, int]:
        self.update_idletasks()

        max_val = max(self.aspect_ratio)
        max_ind = self.aspect_ratio.index(max_val)
        if max_ind == 0:
            val1 = self.game_can_center.winfo_width()
            val2 = val1 * (self.aspect_ratio[1] / self.aspect_ratio[0])

            return int(val1), int(val2)

        else:
            val2 = self.game_can_center.winfo_height()
            val1 = val2 * (self.aspect_ratio[0] / self.aspect_ratio[1])

            return int(val1), int(val2)

    def reset_values(self, *_trash) -> None:
        """
        update all entry values to 1
        """
        self.update_value(self.saturation, "1")
        self.update_value(self.sharpness, "1")
        self.update_value(self.contrast, "1")
        self.update_value(self.brightness, "1")
        self.saturation["slider"].set(1)
        self.sharpness["slider"].set(1)
        self.contrast["slider"].set(1)
        self.brightness["slider"].set(1)

    def update_value(self, to_update: SliderValue, value: str) -> None:
        value = round(float(value), 2)
        to_update["entry"].delete(0, tk.END)
        to_update["entry"].insert(0, str(value))
        to_update["value"] = value
        if "enhancer" in to_update:
            self.update_enhancement()

        if "func" in to_update:
            to_update["func"](value)

    def update_enhancement(self) -> None:
        saturation = self.saturation["enhancer"](self.resized_image)
        tmp = saturation.enhance(self.saturation["value"])

        sharpness = self.sharpness["enhancer"](tmp)
        tmp = sharpness.enhance(self.sharpness["value"])

        contrast = self.contrast["enhancer"](tmp)
        tmp = contrast.enhance(self.contrast["value"])

        brightness = self.brightness["enhancer"](tmp)
        self.enhanced_image = brightness.enhance(self.brightness["value"])

        self.tk_image = ImageTk.PhotoImage(self.enhanced_image.copy())
        self.game_can.create_image(self.x_off, self.y_off, image=self.tk_image)

    def show_frame(self, frame: tk.Frame) -> None:
        if self.now_frame is not ...:
            self.now_frame.pack_forget()

        frame.pack(fill=tk.BOTH, expand=True)
        self.now_frame = frame

    def update_game_frame(self, *_trash) -> None:
        width, height = self.game_window_size
        self.x_off, self.y_off = self.game_window_size
        self.x_off /= 2
        self.y_off /= 2

        self.resized_image = self.original_image.resize(self.game_window_size)
        self.game_can_center.config(width=width, height=height)
        self.game_can.config(width=width, height=height)
        self.reset_values()
        self.update_enhancement()

    def on_resize(self, _event=...) -> None:
        # self.update_game_frame()
        ...

    def save(self, filepath: str = ...) -> bool:
        if filepath is ...:
            filepath = filedialog.asksaveasfilename(
                title="Save Image as",
                parent=self,
                confirmoverwrite=True,
                initialdir="./",
                filetypes=[
                    ("Joint Photographic Expert Group image", ".jpg"),
                    ("Portable Network Graphic", ".png"),
                    ("Icon", ".ico"),
                    ("Graphics Interchange Format", ".gif"),
                    ("All Files", "*")
                ]
            )

            if not filepath:
                return False

        extension = filepath.split(".")[1]
        self.resized_image = self.original_image
        self.update_enhancement()
        self.enhanced_image.save(fp=filepath, format=extension)

        self.open(filepath)
        return True

    def open(self, filepath: str = ...) -> None:
        if filepath is ...:
            filepath = filedialog.askopenfilename(
                title="Open Image",
                parent=self,
                initialdir="./",
                filetypes=[
                    ("Joint Photographic Expert Group image", ".jpg"),
                    ("Portable Network Graphic", ".png"),
                    ("Icon", ".ico"),
                    ("Graphics Interchange Format", ".gif"),
                    ("All Files", "*")
                ]
            )

            if not filepath:
                return

        self.image_path = filepath

        self.original_image = Image.open(filepath)
        self.window_size = self.original_image.size[0], self.original_image.size[1]
        tmp = Fraction(*self.window_size)
        self.aspect_ratio = tmp.numerator, tmp.denominator

        self.update_game_frame()

    def end(self, *_trash, save: bool = True) -> None:
        if save:
            if not self.save():
                return

        self.destroy()


if __name__ == "__main__":
    w = Window()
    w.mainloop()
