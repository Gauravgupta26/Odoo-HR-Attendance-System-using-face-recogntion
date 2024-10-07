from odoo import models
import numpy as np
import base64
from odoo.exceptions import UserError
import face_recognition
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import cv2
import threading
import time

class Employee(models.Model):
    _inherit = 'hr.employee'
    def attendance_manual(self, next_action, entered_pin=None):
        self.ensure_one()
        face_recognized = self.capture_image()
        if not face_recognized:
            return {'warning': ('Face not recognized or attendance cancelled.')}
        
        attendance_user_and_no_pin = self.user_has_groups(
            'hr_attendance.group_hr_attendance_user,'
            '!hr_attendance.group_hr_attendance_use_pin')
        can_check_without_pin = attendance_user_and_no_pin or (self.user_id == self.env.user and entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
            return self._attendance_action(next_action)
        if not self.user_has_groups('hr_attendance.group_hr_attendance_user'):
            return {'warning': ('To activate Kiosk mode without pin code, you must have access right as an Officer or above in the Attendance app. Please contact your administrator.')}
        return {'warning': ('Wrong PIN')}

    def capture_image(self):
        class CameraApp:
            def __init__(self, root, employee):
                self.root = root
                self.employee = employee
                self.face_recognized = False
                self.cap = cv2.VideoCapture(0)
                self.classNames = [employee.name]
                self.encodeListKnown = self.findEncodings([cv2.imdecode(np.frombuffer(base64.b64decode(employee.image_1920), np.uint8), cv2.IMREAD_COLOR)])
                self.canvas = tk.Canvas(root, width=640, height=480)
                self.canvas.pack()
                self.start_time = time.time()
                self.update_frame()


            def findEncodings(self, images):
                encodeList = []
                for img in images:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    face_encodings = face_recognition.face_encodings(img)
                    if len(face_encodings) == 0:
                        print("No faces found in image.")
                        continue
                    encode = face_encodings[0]
                    encodeList.append(encode)
                return encodeList

            def update_frame(self):
                if self.cap.isOpened():
                    ret, frame = self.cap.read()
                    if ret:
                        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(img_rgb)
                        img_tk = ImageTk.PhotoImage(image=img_pil)
                        self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                        self.canvas.img_tk = img_tk
                        
                        facesCurFrame = face_recognition.face_locations(img_rgb)
                        encodesCurFrame = face_recognition.face_encodings(img_rgb, facesCurFrame)
                        
                        if encodesCurFrame:
                            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                                matches = face_recognition.compare_faces(self.encodeListKnown, encodeFace)
                                faceDis = face_recognition.face_distance(self.encodeListKnown, encodeFace)
                                
                                if len(faceDis) > 0:
                                    matchIndex = np.argmin(faceDis)
                                    
                                    if matches[matchIndex] and faceDis[matchIndex] < 0.45:
                                        # y1, x2, y2, x1 = faceLoc
                                        # y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                                        # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                        # cv2.putText(frame, self.classNames[matchIndex].upper(), (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
                                        self.face_recognized = True
                                        break
                        
                        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        img_pil = Image.fromarray(img_rgb)
                        img_tk = ImageTk.PhotoImage(image=img_pil)
                        self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
                        self.canvas.img_tk = img_tk
                        
                        current_time = time.time()
                        
                        if self.face_recognized or current_time - self.start_time >= 5:
                            self.root.after(1000, self.close_app)
                        else:
                            self.root.after(30, self.update_frame)


            def close_app(self):
                self.cap.release()
                self.root.destroy()

        root = tk.Tk()
        app = CameraApp(root, self)
        root.mainloop()

        return app.face_recognized

