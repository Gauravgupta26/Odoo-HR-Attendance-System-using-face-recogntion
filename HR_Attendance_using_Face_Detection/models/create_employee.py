from odoo import models
import cv2
import base64
import tkinter as tk
from tkinter import Button
from PIL import Image, ImageTk
from odoo.exceptions import UserError

class Employee(models.Model):
    _inherit = 'hr.employee'

    def new_employee_image(self):
        self.start_camera_gui()

    def start_camera_gui(self):
        class CameraApp:
            def __init__(self, window, odoo_record):
                self.window = window
                self.window.title("Create Employee")
                self.odoo_record = odoo_record
                self.frame = tk.Frame(window)
                self.frame.pack(fill=tk.BOTH, expand=True)
                self.video_source = 0
                self.vid = cv2.VideoCapture(self.video_source)
                self.canvas = tk.Canvas(self.frame, width=int(self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
                                       height=int(self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
                self.canvas.grid(row=0, column=0)
                self.capture_button = Button(self.frame, text="Click", command=self.capture_image)
                self.capture_button.grid(row=1, column=0, pady=10)
                self.update()
                self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

            def update(self):
                ret, frame = self.vid.read()
                if ret:
                    self.current_frame = frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(frame_rgb)
                    self.photo = ImageTk.PhotoImage(image=image)
                    self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
                self.window.after(10, self.update)

            def capture_image(self):
                if hasattr(self, 'current_frame'):
                    _, buffer = cv2.imencode('.jpg', self.current_frame)
                    image_base64 = base64.b64encode(buffer)
                    self.odoo_record.write({'image_1920': image_base64})
                    print("Image captured and saved successfully.")
                    self.vid.release()
                    self.window.destroy()

            def on_closing(self):
                if self.vid.isOpened():
                    self.vid.release()
                self.window.destroy()
        root = tk.Tk()
        CameraApp(root, self)
        root.mainloop()
