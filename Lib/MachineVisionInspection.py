import json
import os
import socket
import sys
import time
import tkinter as tk
from templates.API import API
from templates.checksetting import createsettingparamiter, createsettingcamera, checksetting
from templates.ImageProcessing import Image_Processing
from templates.readfile import readfile
from templates.savedata import savedata, packing
from threading import Timer
import threading
from tkinter import *
from tkinter import messagebox
import customtkinter
import cv2 as cv
from PIL import Image
from PIL import ImageTk
import pyvisa
import pyvisa_py
from time import strftime
import numpy as np
from pygame import mixer

def close():
    try:
        os.system('TASKKILL /F /IM MachineVisionInspection_cobot.exe')
    except:
        pass
#close()

class Board():
    def __init__(self,board):
        super().__init__()
        self.rm = pyvisa.ResourceManager('@py')
        self.inst = self.rm.open_resource(board)
        self.inst.write("@1 I0")

    def ReadBoard(self):
        self.inst.query("*IDN?")
        self.data = self.inst.read()[:3]

Machinename, camera, quantitycamera, resolutioncamera, mode, communication, Details = readfile.read_SettingParamiter()
BRIGHTNESS, EXPOSURE, CONTRAST, SATURATION, FOCUS, SHARPNESS, HUE, GAIN, ZOOM = readfile.read_CameraAttributeSettings()
API.Information()
if communication == "NumericKey":
    key = Details[0]
elif communication == "TcpIP":
    host = Details[0]
    port = int(Details[1])
elif communication == "Board":
    board = Details[0]

frame = []
frameset = []
startapp = True
if camera == "USBcamera":
    font_scale = 1.2
    widget = 1480
    height = 780
    framex = 10
elif camera == "Industrial":
    font_scale = 1.5
    widget = 860
    height = 645
    framex = 0

try:
    for i in range(quantitycamera):
        frame.append(cv.VideoCapture(i, cv.CAP_DSHOW))
    for i in range(quantitycamera):
        frame[i].set(cv.CAP_PROP_FRAME_WIDTH, int(resolutioncamera[0]))
        frame[i].set(cv.CAP_PROP_FRAME_HEIGHT, int(resolutioncamera[1]))
        frame[i].set(cv.CAP_PROP_AUTO_EXPOSURE, 0)
        frame[i].set(cv.CAP_PROP_AUTOFOCUS, 0)
        frame[i].set(cv.CAP_PROP_BRIGHTNESS, BRIGHTNESS[i])
        frame[i].set(cv.CAP_PROP_EXPOSURE, EXPOSURE[i])
        frame[i].set(cv.CAP_PROP_CONTRAST, CONTRAST[i])
        frame[i].set(cv.CAP_PROP_SATURATION, SATURATION[i])
        frame[i].set(cv.CAP_PROP_FOCUS, FOCUS[i])
        frame[i].set(cv.CAP_PROP_SHARPNESS, SHARPNESS[i])
        frame[i].set(cv.CAP_PROP_HUE, HUE[i])
        frame[i].set(cv.CAP_PROP_GAIN, GAIN[i])
        frame[i].set(cv.CAP_PROP_ZOOM, ZOOM[i])
except:
    startapp = False


class InfiniteTimer():
    def __init__(self, seconds, target):
        self._should_continue = False
        self.is_running = False
        self.seconds = seconds
        self.target = target
        self.thread = None

    def _handle_target(self):
        self.is_running = True
        self.target()
        self.is_running = False
        self._start_timer()

    def _start_timer(self):
        if self._should_continue:
            self.thread = Timer(self.seconds, self._handle_target)
            self.thread.start()

    def start(self):
        if not self._should_continue and not self.is_running:
            self._should_continue = True
            self._start_timer()
        else:
            pass

    def cancel(self):
        if self.thread is not None:
            self._should_continue = False
            self.thread.cancel()
        else:
            pass


class App(customtkinter.CTk):
    customtkinter.set_appearance_mode("Dark")
    customtkinter.set_default_color_theme("green")

    def __init__(self):
        super().__init__()
        self.Login = None

        self.title('Machine Vision Inspection 1.1.0')
        self.geometry("1920x1020+0+0")
        self.attributes('-fullscreen', True)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        Fullscreen_width = 1920
        Fullscreen_height = 1080
        self.new_scaling_float = screen_width / Fullscreen_width
        customtkinter.set_widget_scaling(self.new_scaling_float)
        #self.overrideredirect(True)
        self.Camerarun = False

        self.flag_result = []
        self.flag_score_ares = []
        self.flag_score_outline = []
        self.flag_imagesave = []
        self.flag_color = []
        self.flag_left = []
        self.flag_top = []
        self.flag_right = []
        self.flag_bottom = []
        self.flag_image_model = []

        self.CouterPoint = 0
        self.CouterNG = 0
        self.CouterOK = 0
        self.Comfrim_Data = 0
        self.CouterPacking = 0
        self.reture_robot = False
        self.SaveDataBoard00 = True
        self.SaveDataBoard_IO = False
        self.SaveDataBoard = True
        self.Reorderflag = False
        self.BKFImage, self.ExitImage = readfile.Image()
        customtkinter.CTkLabel(master=self, text="Vision Inspection", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=50, weight="bold"), corner_radius=10).place(x=140, y=10)

        self.ProcessP = customtkinter.CTkLabel(master=self, text="Ready", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=40, weight="bold"), fg_color=("#353535"), corner_radius=10)
        self.ProcessP.place(x=1100, y=10)

        self.Clocktime = customtkinter.CTkLabel(master=self, text="Ready", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=40, weight="bold"), fg_color=("#353535"), corner_radius=10)
        self.Clocktime.place(x=650, y=10)

        customtkinter.CTkLabel(master=self, text="v 1.1.0 build02", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=15, weight="bold"), corner_radius=10).place(x=490, y=10)
        customtkinter.CTkButton(master=self, text="Setup", text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=45, weight="bold"), corner_radius=10, fg_color=("#353535"), height=190, width=200, command=self.SaveMasterNewWindow).place(x=1720, y=80)
        customtkinter.CTkButton(master=self, text="Reorder", command=lambda: self.Reorder(),text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=45, weight="bold"), corner_radius=10, fg_color=("#353535"), height=85,width=200).place(x=1510, y=80)
        customtkinter.CTkButton(master=self, text="Initiate", command=lambda: self.Initiate(), text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=45, weight="bold"), corner_radius=10, fg_color=("#353535"), height=85,width=200).place(x=1510, y=180)


        self.Exit = customtkinter.CTkButton(master=self, image=self.BKFImage, text="", fg_color="#353535", hover_color="#353535", command=self.Destory)
        self.Exit.place(x=1755, y=10)
        self.Exit.bind("<Enter>", self.on_enter)
        self.Exit.bind("<Leave>", self.on_leave)
        self.combobox_cam()
        self.camera_value = customtkinter.StringVar()
        self.camera_value.set("Camera1")
        self.camera_combobox = customtkinter.CTkComboBox(master=self, width=180, height=50, variable=self.camera_value, values=self.camera, corner_radius=10, border_color="#C5C5C5", text_color="#00B400", border_width=5, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold"),
                                                         button_hover_color="#B4F0B4",
                                                         button_color="#C5C5C5", dropdown_hover_color="#B4F0B4", dropdown_text_color="#00B400", dropdown_font=("Microsoft PhagsPa", 20))
        self.camera_combobox['state'] = 'readonly'
        self.camera_combobox.place(x=1320, y=10)
        self.Clock()
        self.frame = customtkinter.CTkLabel(master=self, text="")
        self.frame.place(x=880, y=350)
        self.mastershow = customtkinter.CTkLabel(master=self, text="")
        self.mastershow.place(x=framex, y=350)
        self.Camera()
        named_tuple = time.localtime()
        self.Time = time.strftime("%Y%m%d%H%M%S", named_tuple)
        customtkinter.CTkLabel(master=self, text="Master", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=45, weight="bold"), corner_radius=10, fg_color=("#353535"), height=50, width=200).place(x=0, y=285)
        customtkinter.CTkLabel(master=self, text="Actual", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=45, weight="bold"), corner_radius=10, fg_color=("#353535"), height=50, width=200).place(x=880, y=285)
        """try:
            self.frame = customtkinter.CTkLabel(master=self, text="")
            self.frame.place(x=framex, y=280)
            self.Camera()
        except:
            yes = messagebox.showerror("Camera", "No camera connection, please close the program to check camera")
            if yes == "yes":
                self.destroy()"""
        if communication == "TcpIP":
            self.Communication = customtkinter.CTkButton(master=self, text="Connect", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color="#353535", hover_color="#B4F0B4", command=lambda: [self.connectingTCP()])
            self.Communication.place(x=1520, y=10)
        elif communication == "Board":
            self.showboard = customtkinter.CTkLabel(master=self, text="IO Board", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=45, weight="bold"))
            self.showboard.place(x=1530, y=10)
            try:
                self.runboard = Board(board)
                self.LoopBoard = InfiniteTimer(0.1, self.BoardIO)
                self.LoopBoard.start()
            except:
                messagebox.askquestion("Board", "Board does not have this port", icon='warning')
        if mode == "MultiPoint":
            if communication == "NumericKey":
                customtkinter.CTkLabel(master=self, text="Numeric Key " + str(key), text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=30, weight="bold"), fg_color="#353535", corner_radius=10).place(x=1510, y=20)
                self.LabelKeyBoard = tk.Label(self)
                self.LabelKeyBoard.bind_all('<KeyRelease>', self.NumericKey)
        #self.Reorder()
        Machinename = readfile.read_SettingParamiter_machine()
        self.PartNumber, self.BatchNumber, self.PartNameId, self.CustomerPartNumberId, self.MachineName, self.MoldId, self.Sever, self.Packing = API.PCB_data(Machinename)
        self.BatchNumberflag = self.BatchNumber
        self.Initiate()
        self.camera_value.trace("w", lambda *args: self.ViewImage())


    def combobox_cam(self):
        self.camera = []
        for i in range(quantitycamera):
            self.camera.append("Camera" + str(i + 1))

    def Clock(self):
        string = strftime("%Y/%m/%d  %H:%M:%S")
        self.Clocktime.configure(text=string)
        self.Clocktime.after(1000, self.Clock)

    def Keyboard(self):
        os.startfile("C:\Windows\system32/osk.exe")

    def View_details_Clear(self):
        self.Frame_details = customtkinter.CTkFrame(master=self, width=1080, height=200).place(x=10, y=70)

    def Reorder(self):
        Machinename = readfile.read_SettingParamiter_machine()
        self.PartNumber, self.BatchNumber, self.PartNameId, self.CustomerPartNumberId, self.MachineName, self.MoldId, self.Sever, self.Packing = API.PCB_data(Machinename)
        self.Reorderflag = True
        if self.BatchNumberflag != self.BatchNumber:
            self.Reorderflag = False
            self.BatchNumberflag = self.BatchNumber
        self.Initiate()


    def Initiate(self):
        if not self.Reorderflag:
            self.CouterNG = 0
            self.CouterOK = 0
            self.Comfrim_Data = 0
        self.Reorderflag = False
        self.View_details_Clear()
        self.CouterPoint = readfile.read_Master(self.PartNumber)
        self.PointMode, self.Searching, self.PointCamera, self.PointLeft, self.PointTop, self.PointRight, self.PointBottom, self.PointScoreOutline, self.PointScoreArea, self.PointColor, self.PointThreshold, self.PointBrightness ,self.PointColorDefault = readfile.read_Score(self.PartNumber, self.CouterPoint)
        self.imagepart_wi = "image/"+self.PartNumber+".png"
        try:
            image = cv.imread(self.imagepart_wi)
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            im = Image.fromarray(image)
            im = im.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float)))
            image = ImageTk.PhotoImage(image=im)
            self.mastershow.image = image
            self.mastershow.configure(image=image)
        except:
            pass

        self.folderimagetemplate = self.PartNumber+"/Template/"
        try:
            self.imagetemplate = os.listdir(self.folderimagetemplate)
        except:
            pass

        self.Point_Clear_Create()
        customtkinter.CTkLabel(master=self.Frame_Point, text="POINT CHECK", text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=18, weight="bold"), corner_radius=10).place(x=1770, y=275)
        if self.Sever == "Connected":
            color = "#00B400"
        else:
            color = "#D8D874"
        self.CouterPacking = packing.Read_Priter(self.PartNumber)
        customtkinter.CTkLabel(master=self.Frame_details, text=self.MachineName, text_color=color, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=65, weight="bold")).place(x=10, y=0)
        customtkinter.CTkLabel(master=self.Frame_details, text="PartNumber :", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=10, y=85)
        self.PartNumber_bottom = customtkinter.CTkButton(master=self.Frame_details, text=self.PartNumber, text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), fg_color=("#00B400"), corner_radius=10, command=lambda: readfile.ImageWI(self.PartNumber))
        self.PartNumber_bottom.place(x=190, y=80)
        self.PartNumber_bottom.configure(width=300,height=50)
        customtkinter.CTkLabel(master=self.Frame_details, text="Batch :", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=10, y=155)
        self.BatchNumber_lable = customtkinter.CTkLabel(master=self.Frame_details, text=self.BatchNumber, text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), fg_color=("#00B400"), corner_radius=10)
        self.BatchNumber_lable.place(x=190, y=150)
        self.BatchNumber_lable.configure(width=300, height=50)
        customtkinter.CTkLabel(master=self.Frame_details, text="Mold :", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=10, y=225)
        self.Mold = customtkinter.CTkLabel(master=self.Frame_details, text=self.MoldId, text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), fg_color=("#00B400"), corner_radius=10)
        self.Mold.place(x=190, y=220)
        self.Mold.configure(width=300, height=50)

        customtkinter.CTkLabel(master=self.Frame_details, text="PartName :", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=510, y=85)
        self.PartName = customtkinter.CTkLabel(master=self.Frame_details, text=self.PartNameId[0:20], text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), fg_color=("#00B400"), corner_radius=10)
        self.PartName.place(x=650, y=80)
        self.PartName.configure(width=420, height=50)
        customtkinter.CTkLabel(master=self.Frame_details, text="Customer :", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=510, y=155)
        self.Customer = customtkinter.CTkLabel(master=self.Frame_details, text=self.CustomerPartNumberId, text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), fg_color=("#00B400"), corner_radius=10)
        self.Customer.place(x=650, y=150)
        self.Customer.configure(width=420, height=50)

        customtkinter.CTkLabel(master=self.Frame_details, text="Packing :", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold"), corner_radius=10).place(x=510, y=225)
        self.Packing_lable = customtkinter.CTkLabel(master=self.Frame_details, text=str(self.CouterPacking) + "/" + str(self.Packing), text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=("#00B400"), width=150)
        self.Packing_lable.place(x=650, y=220)

        self.NG = customtkinter.CTkButton(master=self.Frame_details, command=lambda: self.ViewNG(), text="NG : " + str(self.CouterNG), text_color="#FFFFFF", hover_color="#C80000", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=60, weight="bold"), corner_radius=10, fg_color=("#FF0000"), width=400)
        self.NG.place(x=1100, y=190)
        self.OK = customtkinter.CTkLabel(master=self.Frame_details, text="OK : " + str(self.CouterOK), text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=62, weight="bold"), corner_radius=10, fg_color=("#00B400"), width=400, height=85)
        self.OK.place(x=1100, y=80)

        customtkinter.CTkButton(master=self, text="KeyBoard", text_color="Yellow",command= lambda: self.Keyboard(),font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=32, weight="bold"), corner_radius=10, fg_color=("#A9A9A9"), width=150).place(x=900, y=220)
        """image_path = "Image/"+self.PartNumber+".png"
        if os.path.isfile(image_path):
            img = cv.imread(image_path)
        else:
            img = np.zeros((350, 700, 3), dtype=np.uint8)
        img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img = img.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float)))
        image = ImageTk.PhotoImage(image=img)
        self.frame.image = image
        self.frame.configure(image=image)"""
    def NumericKey(self, event):
        if event.char == str(key) and self.check_loing_and_addmaster() is True:
            named_tuple = time.localtime()
            self.Time = time.strftime("%Y%m%d%H%M%S", named_tuple)
            self.single_process()

    def single_process(self):
        if self.CouterPoint != 0:
            try:
                savedata.Save_ImageProcess(frame)
            except:
                messagebox.showerror('Camera', 'Cameras Disconnect')
                self.Destory()
            self.Camerarun = True
            self.ProcessP.configure(text="Process")
            self.ProcessP.configure(text_color='yellow')
            self.ImageSave, self.ColorView, self.Result, self.Score_Outline_Data, self.Score_Area_Data, self.Color, ColorShow, self.Left_Find, self.Top_Find, self.Right_Find, self.Bottom_Find,self.Imagemodel = Image_Processing.Singleshot(self.PartNumber, self.PointMode, self.Searching, self.PointCamera,
                                                                                                                                                                                                                              self.PointLeft, self.PointTop, self.PointRight, self.PointBottom,
                                                                                                                                                                                                                              self.PointScoreOutline,
                                                                                                                                                                                                                              self.PointScoreArea, self.PointColor, self.PointThreshold,self.PointBrightness)
            self.ViewPointSigleshot(self.CouterPoint, ColorShow)
            self.ShowResultSingle()
            self.Alarm()
            savedata.Save_Image_Model_Singel(self.PartNumber,self.Result ,self.Imagemodel)
            savedata.Save_Image_Singel(self.PartNumber, self.CouterPoint, self.PointMode, self.ImageSave, self.PointLeft, self.PointTop, self.PointRight, self.PointBottom, self.Left_Find, self.Top_Find, self.Right_Find, self.Bottom_Find, self.Color,
                                       self.Score_Outline_Data, self.PointScoreOutline, self.Score_Area_Data, self.PointScoreArea, self.Result, 30)
            self.ViewImage()
            self.ProcessP.configure(text="Ready")
            self.ProcessP.configure(text_color="#00B400")

        else:
            messagebox.showinfo("Master", "Please add a master image.")

    def multishot_process(self, Point):
        if self.CouterPoint != 0:
            try:
                savedata.Save_ImageProcess(frame)
            except:
                messagebox.showerror('Camera', 'Cameras Disconnect')
                self.Destory()
            self.Camerarun = True
            self.ProcessP.configure(text="Process")
            self.ProcessP.configure(text_color='yellow')
            self.PointSnap = Point
            self.ImageSave, self.ColorView, self.Result, self.Score_Outline_Data, self.Score_Area_Data, self.Color, ColorShow, self.Left_Find, self.Top_Find, self.Right_Find, self.Bottom_Find,self.Imagemodel = Image_Processing.Multishot(self.PartNumber, self.PointMode, self.Searching, self.PointCamera,
                                                                                                                                                                                                                             self.PointLeft, self.PointTop, self.PointRight, self.PointBottom,
                                                                                                                                                                                                           self.PointScoreOutline,self.PointScoreArea, self.PointColor, self.PointThreshold, self.PointBrightness,Point)
            if self.Result == 1:
                self.message = "OK"
            else:
                self.message = "NG"
            self.flag_result.append(self.Result)
            self.flag_score_ares.append(self.Score_Area_Data)
            self.flag_score_outline.append(self.Score_Outline_Data)
            self.flag_imagesave.append(self.ImageSave)
            self.flag_color.append(self.Color)
            self.flag_left.append(self.Left_Find)
            self.flag_top.append(self.Top_Find)
            self.flag_right.append(self.Right_Find)
            self.flag_bottom.append(self.Bottom_Find)
            self.flag_image_model.append(self.Imagemodel)
            self.ViewPointMutishot(self.PointSnap, ColorShow)
            self.ViewImage()
            self.ViewImagemaster(self.PointSnap)
            if self.CouterPoint == len(self.flag_result):
                self.TCPSendResult()
                self.ShowResultMulti()
                savedata.Save_Image_Model_Multi(self.PartNumber,self.Time, self.flag_result, self.flag_image_model)
                savedata.Save_Score(self.PartNumber,self.Time, self.BatchNumber, Machinename, self.CouterPoint, self.flag_score_ares, self.flag_result, mode)
                savedata.Save_Image_Muti(self.PartNumber,self.Time, self.CouterPoint, self.PointMode, self.flag_imagesave, self.PointLeft, self.PointTop, self.PointRight, self.PointBottom, self.flag_left, self.flag_top, self.flag_right, self.flag_bottom, self.flag_color,
                                           self.flag_score_outline, self.PointScoreOutline, self.flag_score_ares, self.PointScoreArea, self.flag_result, 30)

            self.ProcessP.configure(text="Ready")
            self.ProcessP.configure(text_color="#00B400")
        else:
            messagebox.showinfo("Master", "Please add a master image.")

    def Point_Clear_Create(self):
        self.Frame_Point = customtkinter.CTkFrame(master=self, width=170, height=810).place(x=1750, y=270)
        self.lablePointMutishot = []
        for point in range(self.CouterPoint):
                self.lablePointMutishot.append(customtkinter.CTkLabel(master=self.Frame_Point, text=str(point+1), text_color="#FFFFFF", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=(self.PointColorDefault[point]), width=170, height=50))
                self.lablePointMutishot[point].place(x=1750, y=310 + (((point+1) - 1) * 65))

    def ViewPointSigleshot(self, point, color):
        for i in range(point):
            self.lablePointMutishot[i].configure(text=str(i+1), fg_color=(color[i]))

    def ViewPointMutishot(self, point, color):
        self.lablePointMutishot[point-1].configure(text=str(point), fg_color=(color))

    def connectingTCP(self):
        self.Communication.configure(text="Connecting..", fg_color="yellow")
        self.Communication.place(x=1520)
        timer = Timer(0.5, self.connectTCP, args=())
        timer.start()

    def connectTCP(self):
        server_socket = socket.socket()
        server_socket.settimeout(60)
        try:
            try:
                server_socket.bind((host, port))
            except:
                messagebox.showwarning("Communication Error !!", "The address or port does not match. !!!")
                self.Communication.configure(text="Connect")
            server_socket.listen(2)
            self.conn, address = server_socket.accept()
            self.Looptcp = InfiniteTimer(0.1, self.TCP_server)
            self.Looptcp.start()
            self.Communication.configure(text="Connected", fg_color="#353535")
        except socket.timeout:
            messagebox.showwarning("Communication Error !!", "The communication with Robot time out 60 seconds")
            self.Communication.configure(text="Connect", fg_color="#353535")
        finally:
            server_socket.close()
    def TCPSendResult(self):
        if self.CouterPoint == sum(self.flag_result):
            self.reture_robot = True
        else:
            self.reture_robot = False


    def TCP_server(self):
        self.data = self.conn.recv(128).decode()
        PartNumber = self.PartNumber + "|" + "|"
        if self.data == "Vision":
            if self.Sever == "Connected":
                if self.CouterPoint != 0:
                    self.message = "Ready"
                else:
                    self.message = "Setup"
            else:
                self.message = "Setup"
        elif self.data == "PartNumber":
            self.message = PartNumber
        elif mode == "MultiPoint":
            if self.data == "Snap01":  # Single
                named_tuple = time.localtime()
                self.Time = time.strftime("%Y%m%d%H%M%S", named_tuple)
                self.single_process()
            else:
                self.message = "Error"
                messagebox.showinfo("Transmission Control Protocol", "Singleshot use only Snap01!")
        elif mode == "SinglePoint":
            if self.data == "Snap01":
                self.flag_result = []
                self.flag_score_ares = []
                self.flag_score_outline = []
                self.flag_imagesave = []
                self.flag_color = []
                self.flag_left = []
                self.flag_top = []
                self.flag_right = []
                self.flag_bottom = []
                named_tuple = time.localtime()
                self.Time = time.strftime("%Y%m%d%H%M%S", named_tuple)
                self.multishot_process(1)
            elif self.data == "Snap02":
                self.multishot_process(2)
            elif self.data == "Snap03":
                self.multishot_process(3)
            elif self.data == "Snap04":
                self.multishot_process(4)
            elif self.data == "Snap05":
                self.multishot_process(5)
            elif self.data == "Snap06":
                self.multishot_process(6)
            elif self.data == "Snap07":
                self.multishot_process(7)
            elif self.data == "Snap08":
                self.multishot_process(8)
            elif self.data == "Snap09":
                self.multishot_process(9)
            elif self.data == "Snap10":
                self.multishot_process(10)
            elif self.data == "Snap11":
                self.multishot_process(11)
            elif self.data == "Snap12":
                self.multishot_process(12)
            elif self.data == "Snap13":
                self.multishot_process(13)
            elif self.data == "Snap14":
                self.multishot_process(14)
            elif self.data == "Snap15":
                self.multishot_process(15)
            elif self.data == "Result":
                if self.reture_robot == True:
                    self.message = "OK"
                elif self.reture_robot == False:
                    self.message = "NG"
                    # self.message = "Snap" + str(i)
        self.conn.send(self.message.encode())
        self.message = ""

    def BoardIO(self):
        self.runboard.ReadBoard()
        Bin = self.runboard.data
        self.showboard.configure(text=Bin.split()[0])
        if self.CouterPoint != 0:
            if mode == "MultiPoint":
                if Bin == "#00":
                    self.runboard.inst.write("@1 I0")
                    self.SaveDataBoard = True
                elif Bin == "#01" and self.SaveDataBoard == True:  # 01
                    self.runboard.inst.write("@1 I0")
                    named_tuple = time.localtime()
                    self.Time = time.strftime("%Y%m%d%H%M%S", named_tuple)
                    self.single_process()
                    self.SaveDataBoard = False
                else:
                    self.runboard.inst.write("@1 I0")
            elif mode == "SinglePoint":
                try:
                    if Bin == "#00":  # 00
                        self.SaveDataBoard = True
                        if self.SaveDataBoard00 == True:
                            self.runboard.inst.write("@1 R00")
                            self.SaveDataBoard00 = False
                        else:
                            self.runboard.inst.write("@1 I0")
                    elif Bin == "#01" and self.SaveDataBoard == True:  # 01
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.flag_result = []
                        self.flag_score_ares = []
                        self.flag_score_outline = []
                        self.flag_imagesave = []
                        self.flag_color = []
                        self.flag_left = []
                        self.flag_top = []
                        self.flag_right = []
                        self.flag_bottom = []
                        named_tuple = time.localtime()
                        self.Time = time.strftime("%Y%m%d%H%M%S", named_tuple)
                        self.multishot_process(1)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#02" and self.SaveDataBoard == True:  # 02
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(2)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#03" and self.SaveDataBoard == True:  # 03
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(3)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#04" and self.SaveDataBoard == True:  # 04
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(4)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#05" and self.SaveDataBoard == True:  # 05
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(5)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#06" and self.SaveDataBoard == True:  # 06
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(6)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#07" and self.SaveDataBoard == True:  # 07
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(7)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#08" and self.SaveDataBoard == True:  # 08
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(8)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#09" and self.SaveDataBoard == True:  # 09
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(9)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#0A" and self.SaveDataBoard == True:  # 0a
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(10)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#0B" and self.SaveDataBoard == True:  # 0b
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(11)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#0C" and self.SaveDataBoard == True:  # 0c
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        self.runboard.inst.write("@1 R20")
                        self.multishot_process(12)
                        # self.runboard.inst.write("@1 R20")

                    elif Bin == "#0F" and self.SaveDataBoard == True:  # 0f
                        self.SaveDataBoard = False
                        self.SaveDataBoard00 = True
                        if self.reture_robot:
                            self.runboard.inst.write("@1 R80")
                        elif not self.reture_robot:
                            self.runboard.inst.write("@1 R40")
                        #self.ViewPointSigleshot(self.CouterPoint, self.PointColorDefault)
                        self.Camerarun = False
                    else:
                        self.runboard.inst.write("@1 I0")
                except:
                    self.ProcessP.configure(text="BoardError")
                    self.ProcessP.configure(text_color='red')
        else:
            self.runboard.inst.write("@1 I0")
            """messagebox.showerror("IO Board", "IO Board disconnection")
            self.Destory()"""

    def on_enter(self, event):
        self.Exit.configure(image=self.ExitImage)

    def on_leave(self, enter):
        self.Exit.configure(image=self.BKFImage)

    def Destory(self):
        response = messagebox.askquestion("Close Programe", "Are you sure?", icon='warning')
        if response == "yes":
            try:
                if communication == "TcpIP":
                    self.Looptcp.cancel()
                elif communication == "Board":
                    self.LoopBoard.cancel()
            except:
                pass
            for i in range(quantitycamera):
                frame[i].release()
            cv.destroyAllWindows()
            self.destroy()
            sys.exit(1)
            close()

    def Camera(self):
        camerack = Image.fromarray(cv.cvtColor(frame[int(self.camera_value.get().split('a')[2]) - 1].read()[1], cv.COLOR_BGR2RGB))
        camerarun = ImageTk.PhotoImage(image=camerack.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float))))
        #camerarun1 = ImageTk.PhotoImage(image=camerack.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float))))
        if not self.Camerarun:
            self.frame.camerarun = camerarun
            self.frame.configure(image=camerarun)
            #self.mastershow.camerarun1 = camerarun1
            #self.mastershow.configure(image=camerarun1)
        self.after(10, self.Camera)

    def Close_SaveMasterNewWindow(self):
        self.Login.destroy()
        self.Login = None

    def check_loing_and_addmaster(self):
        Login = False
        SaveMaster = False
        Choose_config = False
        try:
            self.Login.winfo_geometry()
        except:
            Login = True
        try:
            self.SaveMaster.winfo_geometry()
        except:
            SaveMaster = True
        try:
            self.Choose_config.winfo_geometry()
        except:
            Choose_config = True
        if Login and SaveMaster and Choose_config:
            return True
        else:
            return False

    def SaveMasterNewWindow(self):
        if not self.Login:
            self.Login = Toplevel(self)
            self.Login.protocol("WM_DELETE_WINDOW", self.Close_SaveMasterNewWindow)
            self.Login.title("Login")
            self.Login.wm_attributes("-topmost", 0)
            self.Login.configure(background='#232323')
            self.Login.attributes('-toolwindow', True)
            self.Login.geometry(str(int(220 * self.new_scaling_float)) + "x" + str(int(140 * self.new_scaling_float)))
            self.Login.grab_set()
            self.Password = tk.StringVar()
            self.Password.trace("w", lambda *args: character_limit())

            def character_limit():
                try:
                    if len(self.Password.get()) > 0:
                        self.Password.set(self.Password.get()[6])
                except:
                    pass

            self.Error_passWord = customtkinter.CTkLabel(self.Login, text="", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=10, weight="bold"), text_color="red")
            self.Error_passWord.place(x=10, y=0)
            customtkinter.CTkEntry(self.Login, width=200, height=50, corner_radius=10, placeholder_text="Password", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=40, weight="bold"), show='*', textvariable=self.Password).place(x=10, y=20)

            def Loginform():
                with open('config\Operator.json', 'r') as json_Part:
                    json_object = json.loads(json_Part.read())
                    id_Emp = []
                    for d in json_object:
                        id_Emp.append(d['id_Emp'])
                for i in range(len(id_Emp)):
                    if id_Emp[i] == self.Password.get():
                        return True
                self.Error_passWord.configure(text='Wrong password did not match')
                return False

            def Choose_config():
                if Loginform():
                    self.Login.destroy()
                    self.Login = None
                    # self.Login.protocol("WM_DELETE_WINDOW", self.Close_SaveMasterNewWindow)
                    self.Choose_config = Toplevel(self)
                    self.Choose_config.attributes('-toolwindow', True)
                    self.Choose_config.title("Set up")
                    self.Choose_config.configure(background='#232323')
                    self.Choose_config.geometry(str(int(330 * self.new_scaling_float)) + "x" + str(int(330 * self.new_scaling_float)))
                    # self.Choose_config.geometry('330x330')
                    self.Choose_config.grab_set()
                    customtkinter.CTkButton(self.Choose_config, text="Setting paramiter", text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=("#353535"), height=80, width=310,
                                            command=Settingparamiter).place(x=10, y=30)
                    customtkinter.CTkButton(self.Choose_config, text="Setting Camera", text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=("#353535"), height=80, width=310,
                                            command=SettingCamera).place(x=10, y=130)
                    customtkinter.CTkButton(self.Choose_config, text="Save Master", text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=("#353535"), height=80, width=310, command=Addmaster).place(
                        x=10, y=230)
        customtkinter.CTkButton(self.Login, text="Login", text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=30, weight="bold"), corner_radius=10, fg_color=("#353535"), command=Choose_config).place(x=40, y=90)
        self.Login.deiconify()

        def Settingparamiter():
            yes = messagebox.askquestion(
                title="Parameter settings",
                message="You must close the program to set parameters ?",
            )
            if yes == "yes":
                os.remove("config/SettingParamiter.json")
                try:
                    if communication == "TcpIP":
                        self.Looptcp.cancel()
                    elif communication == "Board":
                        self.LoopBoard.cancel()
                except:
                    pass
                for i in range(quantitycamera):
                    frame[i].release()
                cv.destroyAllWindows()
                self.destroy()
                from templates.checksetting import createsettingparamiter
                app = createsettingparamiter()
                app.mainloop()

        def SettingCamera():
            yes = messagebox.askquestion(
                title="Camera attribute settings",
                message="You must close the program to set Camera attribute ?",
            )
            if yes == "yes":
                os.remove("config/CameraAttributeSettings.json")
                try:
                    if communication == "TcpIP":
                        self.Looptcp.cancel()
                    elif communication == "Board":
                        self.LoopBoard.cancel()
                except:
                    pass
                for i in range(quantitycamera):
                    frame[i].release()
                cv.destroyAllWindows()
                self.destroy()
                from templates.checksetting import createsettingcamera
                app = createsettingcamera()
                app.mainloop()

        def Addmaster():
            self.Choose_config.destroy()
            self.Choose_config = None
            # self.Login.protocol("WM_DELETE_WINDOW", self.Close_SaveMasterNewWindow)
            self.SaveMaster = Toplevel(self)
            self.SaveMaster.attributes('-toolwindow', True)
            self.SaveMaster.title("Save Master")
            self.SaveMaster.configure(background='#232323')
            self.SaveMaster.geometry(str(int(330 * self.new_scaling_float)) + "x" + str(int(520 * self.new_scaling_float)))
            self.SaveMaster.grab_set()
            Score_Data_Area = tk.StringVar()
            Score_Data_Area.trace("w", lambda *args: score_limit(Score_Data_Area))
            Score_Data_Outline = tk.StringVar()
            Score_Data_Outline.trace("w", lambda *args: score_limit(Score_Data_Outline))

            def Save_Master():
                PartNumber, BatchNumber, PartName, CustomerPartNumber, MachineName, MoldId, Sever, Packing = API.PCB_data(Machinename)
                Point = Point_value.get()
                Emp_ID = self.Password.get()
                ScoreOutlie = ScoreOutlie_value.get()
                ScoreArea = ScoreArea_value.get()
                Mode = Mode_value.get()
                Cam = Camera_value.get()
                Searching = Searching_value.get()
                self.ScoreThreshold = shapethreshold_value.get()
                if (str.isdigit(ScoreOutlie) and int(ScoreOutlie)) >= 500 and (str.isdigit(ScoreArea) and int(ScoreArea)) >= 500:
                    if Camera_value.get() == "Camera1":
                        Imagesave = Image.fromarray(cv.cvtColor(frame[0].read()[1], cv.COLOR_BGR2RGB))
                    elif Camera_value.get() == "Camera2":
                        Imagesave = Image.fromarray(cv.cvtColor(frame[1].read()[1], cv.COLOR_BGR2RGB))
                    elif Camera_value.get() == "Camara3":
                        Imagesave = Image.fromarray(cv.cvtColor(frame[2].read()[1], cv.COLOR_BGR2RGB))
                    Imagesave.save("Current.bmp")
                    Master = PartNumber + '/Master'
                    if not os.path.exists(Master):
                        os.makedirs(Master)
                    else:
                        print("")
                    Template = PartNumber + '/Template'
                    if not os.path.exists(Template):
                        os.makedirs(Template)
                    else:
                        print("")
                    refPt = []
                    cropping = False

                    def click_and_crop(event, x, y, flags, param):
                        global refPt, cropping
                        image = clone.copy()
                        if Mode == "Shape(threshold)":
                            imagegray = imagesave.copy()
                        if event == cv.EVENT_LBUTTONDOWN:
                            refPt = [(x, y)]
                            cropping = True
                        elif event == cv.EVENT_LBUTTONUP:
                            refPt.append((x, y))
                            cropping = False
                            if Mode == "Shape(threshold)" or Mode == "Shape":
                                image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
                            cv.rectangle(image, refPt[0], refPt[1], (85, 255, 51), 2)
                            if Mode == "Shape(threshold)":
                                imagegray = cv.cvtColor(imagegray, cv.COLOR_BGR2RGB)
                                cv.rectangle(imagegray, refPt[0], refPt[1], (85, 255, 51), 2)
                            cv.imshow(Point, image)
                            if len(refPt) == 2:
                                if Mode == "Shape(threshold)":
                                    roi = imagesave[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
                                else:
                                    roi = clone[refPt[0][1]:refPt[1][1], refPt[0][0]:refPt[1][0]]
                                Left = refPt[0][0]
                                Top = refPt[0][1]
                                Right = refPt[1][0]
                                Bottom = refPt[1][1]
                                Showtext = cv.putText(image, Point, (10, 35),cv.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), 2)
                                if Mode == "Shape(threshold)":
                                    cv.putText(imagegray, Point, (10, 35),cv.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), 2)
                                else:
                                    cv.putText(image, Point, (10, 35),cv.FONT_HERSHEY_SIMPLEX, font_scale, (0, 255, 0), 2)
                                cv.imshow(Point, Showtext)
                                cv.imwrite('' + Master + '/' + Point + '_Master.bmp', roi)
                                if Mode == "Shape(threshold)":
                                    hsv = []
                                    cv.imwrite('' + Template + '/' + Point + '_Template.bmp', imagegray)
                                elif Mode == "Color":
                                    hsv = Image_Processing.Color.rbg2hsv(roi)
                                    cv.imwrite('' + Template + '/' + Point + '_Template.bmp', image)
                                brightness = Image_Processing.get_image_brightness(roi)
                                if Left and Top and Right and Bottom != 0:
                                    savedata.Master(Left, Top, Right, Bottom, Mode, Searching, ScoreOutlie, ScoreArea, Cam, Point, Emp_ID, PartNumber, hsv, self.ScoreThreshold, brightness)

                    if Mode == "Shape(threshold)":
                        path = r'Current.bmp'
                        imagesave = cv.imread(path, cv.IMREAD_GRAYSCALE)
                        image = cv.imread(path, cv.IMREAD_GRAYSCALE)
                        image = Image_Processing.Threshold(image, int(self.ScoreThreshold))
                        clone = image.copy()
                        Threshold = cv.imread(path, cv.IMREAD_GRAYSCALE)
                        Threshold = Image_Processing.Threshold(Threshold, int(self.ScoreThreshold))
                    elif Mode == "Color":
                        path = r'Current.bmp'
                        image = cv.imread(path)
                        clone = image.copy()
                    elif Mode == "Shape":
                        path = r'Current.bmp'
                        image = cv.imread(path, cv.IMREAD_GRAYSCALE)
                        clone = image.copy()
                    cv.namedWindow(Point)
                    cv.setMouseCallback(Point, click_and_crop)
                    cv.imshow(Point, image)
                else:
                    messagebox.showwarning("Score", "Minumun Score 500")

            shapethreshold_value = customtkinter.StringVar()
            shapethreshold_value.set("150")
            customtkinter.CTkLabel(self.SaveMaster, text="Point:", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=5, y=26)
            Point_value = customtkinter.StringVar()
            Point_value.set("Point1")
            Point = customtkinter.CTkComboBox(self.SaveMaster, variable=Point_value, values=['Point1', 'Point2', 'Point3', 'Point4', 'Point5', 'Point6', 'Point7', 'Point8', 'Point9', 'Point10', 'Point11', 'Point12'],
                                              corner_radius=10, border_color="#C5C5C5", text_color="#00B400", border_width=5, width=200, height=50, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold"), button_hover_color="#B4F0B4", button_color="#C5C5C5",
                                              dropdown_hover_color="#B4F0B4", dropdown_text_color="#00B400", dropdown_font=("Microsoft PhagsPa", 20)).place(x=120, y=20)

            customtkinter.CTkLabel(self.SaveMaster, text="Camera:", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=5, y=102)

            Camera_value = customtkinter.StringVar()
            Camera_value.set("Camera1")
            Camera = customtkinter.CTkComboBox(self.SaveMaster, variable=Camera_value, values=self.camera,
                                               corner_radius=10, border_color="#C5C5C5", text_color="#00B400", border_width=5, width=200, height=50, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold"), button_hover_color="#B4F0B4", button_color="#C5C5C5",
                                               dropdown_hover_color="#B4F0B4", dropdown_text_color="#00B400", dropdown_font=("Microsoft PhagsPa", 20)).place(x=120, y=100)

            customtkinter.CTkLabel(self.SaveMaster, text="Mode:", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=5, y=182)
            Mode_value = customtkinter.StringVar()
            Mode_value.set("Shape(threshold)")
            Mode = customtkinter.CTkComboBox(self.SaveMaster, variable=Mode_value, values=['Shape(threshold)', 'Color', ],
                                             corner_radius=10, border_color="#C5C5C5", text_color="#00B400", border_width=5, width=200, height=50, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold"), button_hover_color="#B4F0B4", button_color="#C5C5C5",
                                             dropdown_hover_color="#B4F0B4", dropdown_text_color="#00B400", dropdown_font=("Microsoft PhagsPa", 20))
            Mode.place(x=120, y=180)
            customtkinter.CTkLabel(self.SaveMaster, text="Outlie: ", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=5, y=260)
            ScoreOutlie_value = customtkinter.StringVar()
            ScoreOutlie_value.set("900")
            customtkinter.CTkEntry(self.SaveMaster, width=200, height=50, placeholder_text="Score", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=30, weight="bold"), textvariable=ScoreOutlie_value, text_color="#00B400").place(x=120, y=265)

            customtkinter.CTkLabel(self.SaveMaster, text="Area: ", text_color="#00B400", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold")).place(x=5, y=340)
            ScoreArea_value = customtkinter.StringVar()
            ScoreArea_value.set("850")
            customtkinter.CTkEntry(self.SaveMaster, width=200, height=50, placeholder_text="Score", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=30, weight="bold"), textvariable=ScoreArea_value, text_color="#00B400").place(x=120, y=345)
            Searching_value = customtkinter.BooleanVar()
            Searching_value.set(True)
            customtkinter.CTkCheckBox(self.SaveMaster, text="Template Searching", variable=Searching_value, onvalue=True, offvalue=False).place(x=10, y=400)
            customtkinter.CTkButton(self.SaveMaster, text="Save", text_color="#00B400", hover_color="#B4F0B4", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=55, weight="bold"), corner_radius=10, fg_color=("#353535"), command=Save_Master, width=310).place(x=10, y=430)

            def score_limit_Area(*args):
                s = ScoreArea_value.get()
                if str.isdigit(s):
                    if len(s) > 3:
                        ScoreArea_value.set(s[:3])
                else:
                    ScoreArea_value.set(s[:0])

            def score_limit_outline(*args):
                s = ScoreOutlie_value.get()
                if str.isdigit(s):
                    if len(s) > 3:
                        ScoreOutlie_value.set(s[:3])
                else:
                    ScoreOutlie_value.set(s[:0])

            def score_limit_threshold(*args):
                s = shapethreshold_value.get()
                if str.isdigit(s) and int(s) < 256:
                    shapethreshold_value.set(s[:3])
                else:
                    shapethreshold_value.set(s[:0])
            shapethreshold_value.trace("w", score_limit_threshold)

            def shapethreshold(*args):
                global shapethreshold_entry
                s = Mode_value.get()
                if s == "Shape(threshold)":
                    shapethreshold_entry = customtkinter.CTkEntry(self.SaveMaster, width=150, height=25, placeholder_text="threshold", textvariable=shapethreshold_value, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=20, weight="bold"), text_color="#00B400")
                    shapethreshold_entry.place(x=120, y=232)
                else:
                    try:
                        shapethreshold_entry.place_forget()
                    except:
                        pass

            ScoreOutlie_value.trace("w", score_limit_outline)
            ScoreArea_value.trace("w", score_limit_Area)
            Mode_value.trace("w", shapethreshold)

    def ViewImage(self):
        try:
            if mode == "MultiPoint":
                if quantitycamera == 1:
                    image1 = cv.imread("Snap1.bmp")
                    image1 = cv.cvtColor(image1, cv.COLOR_BGR2RGB)
                    for i in range(self.CouterPoint):
                        if self.camera_value.get() == "Camera1" and self.PointCamera[i] == "Camera1":
                            cv.rectangle(image1, (self.Left_Find[i], self.Top_Find[i]), (self.Right_Find[i], self.Bottom_Find[i]), self.ColorView[i], 1)
                            cv.putText(image1, str(i + 1) + ":" + str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, self.ColorView[i], 1)
                            # cv.putText(image1, str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i]), cv.FONT_HERSHEY_SIMPLEX, 0.7, self.ColorView[i], 1)
                            im = Image.fromarray(image1)
                elif quantitycamera == 2:
                    image1 = cv.imread("Snap1.bmp")
                    image1 = cv.cvtColor(image1, cv.COLOR_BGR2RGB)
                    image2 = cv.imread("Snap2.bmp")
                    image2 = cv.cvtColor(image2, cv.COLOR_BGR2RGB)
                    for i in range(self.CouterPoint):
                        if self.camera_value.get() == "Camera1" and self.PointCamera[i] == "Camera1":
                            cv.rectangle(image1, (self.Left_Find[i], self.Top_Find[i]), (self.Right_Find[i], self.Bottom_Find[i]), self.ColorView[i], 1)
                            cv.putText(image1, str(i + 1) + ":" + str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, self.ColorView[i], 1)
                            im = Image.fromarray(image1)
                        elif self.camera_value.get() == "Camera2" and self.PointCamera[i] == "Camera2":
                            cv.rectangle(image2, (self.Left_Find[i], self.Top_Find[i]), (self.Right_Find[i], self.Bottom_Find[i]), self.ColorView[i], 1)
                            cv.putText(image2, str(i + 1) + ":" + str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, self.ColorView[i], 1)
                            im = Image.fromarray(image2)
                elif quantitycamera == 3:
                    image1 = cv.imread("Snap1.bmp")
                    image1 = cv.cvtColor(image1, cv.COLOR_BGR2RGB)
                    image2 = cv.imread("Snap2.bmp")
                    image2 = cv.cvtColor(image2, cv.COLOR_BGR2RGB)
                    image3 = cv.imread("Snap2.bmp")
                    image3 = cv.cvtColor(image2, cv.COLOR_BGR2RGB)
                    for i in range(self.CouterPoint):
                        if self.camera_value.get() == "Camera1" and self.PointCamera[i] == "Camera1":
                            cv.rectangle(image1, (self.Left_Find[i], self.Top_Find[i]), (self.Right_Find[i], self.Bottom_Find[i]), self.ColorView[i], 1)
                            cv.putText(image1, str(i + 1) + ":" + str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, self.ColorView[i], 1)
                            im = Image.fromarray(image1)
                        elif self.camera_value.get() == "Camera2" and self.PointCamera[i] == "Camera2":
                            cv.rectangle(image2, (self.Left_Find[i], self.Top_Find[i]), (self.Right_Find[i], self.Bottom_Find[i]), self.ColorView[i], 1)
                            cv.putText(image2, str(i + 1) + ":" + str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, self.ColorView[i], 1)
                            im = Image.fromarray(image2)
                        elif self.camera_value.get() == "Camera3" and self.PointCamera[i] == "Camera3":
                            cv.rectangle(image3, (self.Left_Find[i], self.Top_Find[i]), (self.Right_Find[i], self.Bottom_Find[i]), self.ColorView[i], 1)
                            cv.putText(image3, str(i + 1) + ":" + str(self.Score_Area_Data[i]), (self.Left_Find[i], self.Top_Find[i] - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, self.ColorView[i], 1)
                            im = Image.fromarray(image3)
                im = im.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float)))
                image = ImageTk.PhotoImage(image=im)
                self.frame.image = image
                self.frame.configure(image=image)

            elif mode == "SinglePoint":
                #image = cv.imread("Snap" + str(self.PointCamera[self.PointSnap - 1].split('a')[2]) + ".bmp")
                image = cv.cvtColor(self.ImageSave, cv.COLOR_BGR2RGB)
                cv.rectangle(image, (self.Left_Find, self.Top_Find), (self.Right_Find, self.Bottom_Find), self.ColorView, 2)
                cv.putText(image, "Outline: " + str(self.Score_Outline_Data) + " : " + str(self.PointScoreOutline[self.PointSnap - 1]), (10, 35), cv.FONT_HERSHEY_SIMPLEX, font_scale, self.ColorView, 2)
                cv.putText(image, "Area:   " + str(self.Score_Area_Data) + " : " + str(self.PointScoreArea[self.PointSnap - 1]), (10, 75), cv.FONT_HERSHEY_SIMPLEX, font_scale, self.ColorView, 2)
                # cv.putText(image, "Check : " + self.PointMode[self.PointSnap - 1], (10, 95), cv.FONT_HERSHEY_SIMPLEX, font_scale, self.ColorView[0], 1)
                # cv.putText(image, str(self.PointSnap), (self.Left_Find[0], self.Top_Find[0] - 5), cv.FONT_HERSHEY_SIMPLEX, font_scale, self.ColorView[0], 1)
                im = Image.fromarray(image)
                im = im.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float)))
                image = ImageTk.PhotoImage(image=im)
                self.frame.image = image
                self.frame.configure(image=image)
        except:
            pass

    def ViewImagemaster(self,Point):
        image = cv.imread(self.folderimagetemplate+self.imagetemplate[Point-1])
        image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
        im = Image.fromarray(image)
        im = im.resize((int(widget * self.new_scaling_float), int(height * self.new_scaling_float)))
        image = ImageTk.PhotoImage(image=im)
        self.mastershow.image = image
        self.mastershow.configure(image=image)

        #self.imagetemplate[Point-1]

    def Alarm_continue(self):
        mixer.init()
        mixer.music.load('config/Alarm.mp3')
        if self.message == "NG":
            mixer.music.play(-1)
        elif self.message == "OK":
            try:
                mixer.stop()
            except:
                pass
    def Alarm(self):
        self.Run_Alarm = threading.Thread(target=self.Alarm_continue())
        self.Run_Alarm.start()

    def ResultComfrim(self):
        if self.Comfrim_Data >= 4:
            savedata.Save_Score(self.PartNumber,self.Time ,self.BatchNumber, Machinename, self.CouterPoint, self.Score_Area_Data, self.Result, mode)
            self.CouterNG += 1
            self.NG.configure(text="NG : " + str(self.CouterNG))

    def ShowResultSingle(self):
        if sum(self.Result) == self.CouterPoint:
            self.message = "OK"
            self.CouterOK += 1
            self.OK.configure(text="OK : " + str(self.CouterOK))
            self.Comfrim_Data = 0
            savedata.Save_Score(self.PartNumber,self.Time ,self.BatchNumber, Machinename, self.CouterPoint, self.Score_Area_Data, self.Result, mode)
            self.CouterPacking = packing.Counter_Printer(self.PartNumber, self.Packing)
            self.Packing_lable.configure(text=str(self.CouterPacking) + "/" + str(self.Packing))
            if communication == "Board" and self.SaveDataBoard_IO == False:
                self.runboard.inst.write("@1 R00")
                self.SaveDataBoard_IO = True
        else:
            self.message = "NG"
            self.Comfrim_Data += 1
            self.ResultComfrim()
            if communication == "Board" and self.SaveDataBoard_IO == True:
                self.runboard.inst.write("@1 R40")
                self.SaveDataBoard_IO = False


    def ShowResultMulti(self):
        if sum(self.flag_result) == self.CouterPoint:
            self.CouterOK += 1
            self.OK.configure(text="OK : " + str(self.CouterOK))
            self.CouterPacking = packing.Counter_Printer(self.PartNumber, self.Packing)
            self.Packing_lable.configure(text=str(self.CouterPacking) + "/" + str(self.Packing))
            self.ViewPointSigleshot(self.CouterPoint, self.PointColorDefault)
        else:
            self.CouterNG += 1
            self.NG.configure(text="NG : " + str(self.CouterNG))

    def ViewNG(self):
        # camerarun = ImageTk.PhotoImage(image=camerack.resize((int(1480 * self.new_scaling_float), int(780 * self.new_scaling_float))))
        NGheight = int(900 * self.new_scaling_float)
        NGweight = int(630 * self.new_scaling_float)
        self.Image_NG = []
        self.Next = 0
        self.Previous = 0
        self.Couter_Image = 0
        self.Stand = False
        self.Save_Previous = 0
        self.Save_Next = 0
        self.Keep = 0
        self.index = 0
        self.PartNumber_show = ""
        self.folder = "D:\Backup"
        if os.path.isdir(self.folder):
            dir_list = os.listdir(self.folder)
            if len(dir_list) > 0:
                self.pathbackup = self.folder + '/' + dir_list[-1]
                dir_list_partnumber = os.listdir(self.pathbackup)
                if self.PartNumber in dir_list_partnumber:
                    self.PartNumber_show = self.PartNumber
                ViewNG = Toplevel(self)
                PointNG = []
                for i in range(self.CouterPoint):
                    PointNG.append("Point" + str(i + 1))
                PointNG_value = customtkinter.StringVar()
                customtkinter.CTkComboBox(ViewNG, variable=PointNG_value, values=PointNG,
                                          corner_radius=10, border_color="#C5C5C5", text_color="#00B400", border_width=5, width=200, height=50, font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=25, weight="bold"), button_hover_color="#B4F0B4", button_color="#C5C5C5",
                                          dropdown_hover_color="#B4F0B4", dropdown_text_color="#00B400", dropdown_font=("Microsoft PhagsPa", 20)).place(x=10, y=10)
                customtkinter.CTkButton(ViewNG, text="Choose", text_color="#00B400", hover_color="#94FF8B", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=("#353535"), command=lambda: ShowImageNG()).place(x=220, y=10)
                customtkinter.CTkButton(ViewNG, text="Exit", text_color="#FF3939", hover_color="#FF9797", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=35, weight="bold"), corner_radius=10, fg_color=("#353535"), command=lambda: Destory()).place(x=1770, y=5)

                customtkinter.CTkButton(ViewNG, text="Previous", text_color="#00B400", hover_color="#94FF8B", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=50, weight="bold"), corner_radius=10, fg_color=("#353535"), command=lambda: Previous()).place(x=700, y=800)
                customtkinter.CTkButton(ViewNG, text="Next", text_color="#00B400", hover_color="#94FF8B", font=customtkinter.CTkFont(family="Microsoft PhagsPa", size=50, weight="bold"), corner_radius=10, fg_color=("#353535"), command=lambda: Next()).place(x=1000, y=800)
                ViewNG.configure(background='#232323')
                ViewNG.attributes('-fullscreen', True)

                def Destory():
                    ViewNG.destroy()

                def ReadImageNG():
                    Image_NG = []
                    Point = PointNG_value.get()
                    image_path_NG = self.pathbackup + '/' + self.PartNumber_show + "/NG/" + Point
                    for path in os.listdir(image_path_NG):
                        if os.path.isfile(os.path.join(image_path_NG, path)):
                            if path.endswith('.jpg'):
                                Image_NG.append(path)
                    return Image_NG, Point

                def Next():
                    try:
                        if self.Stand is True:
                            self.index = (self.index + 1) % len(self.Image_NG)
                            Point = PointNG_value.get()
                            image_path_NG = self.pathbackup + '/' + self.PartNumber_show + "/NG/" + Point + "/" + self.Image_NG[self.index]
                            imageNG = cv.imread(image_path_NG)
                            imageNG = cv.cvtColor(imageNG, cv.COLOR_BGR2RGB)
                            imageNG = Image.fromarray(imageNG)
                            photoNG = ImageTk.PhotoImage(imageNG.resize((NGheight, NGweight)))
                            image_show_NG = customtkinter.CTkLabel(master=ViewNG, text="")
                            image_show_NG.photoNG = photoNG
                            image_show_NG.configure(image=photoNG)
                            image_show_NG.place(x=1000, y=100)
                    except:
                        pass

                def Previous():
                    try:
                        self.Stand = True
                        self.index = (self.index - 1) % len(self.Image_NG)
                        # print(self.index)
                        Point = PointNG_value.get()
                        image_path_NG = self.pathbackup + '/' + self.PartNumber_show + "/NG/" + Point + "/" + self.Image_NG[self.index]
                        imageNG = cv.imread(image_path_NG)
                        imageNG = cv.cvtColor(imageNG, cv.COLOR_BGR2RGB)
                        imageNG = Image.fromarray(imageNG)
                        photoNG = ImageTk.PhotoImage(imageNG.resize((NGheight, NGweight)))
                        image_show_NG = customtkinter.CTkLabel(master=ViewNG, text="")
                        image_show_NG.photoNG = photoNG
                        image_show_NG.configure(image=photoNG)
                        image_show_NG.place(x=1000, y=100)
                    except:
                        pass

                def ShowImageNG():
                    Point = PointNG_value.get()
                    image_path_Master = self.PartNumber + '/Template/' + Point + '_Template.bmp'
                    image = cv.imread(image_path_Master)
                    image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
                    image = Image.fromarray(image)
                    photo = ImageTk.PhotoImage(image.resize((NGheight, NGweight)))
                    image_show = tk.Label(ViewNG, image=photo)
                    image_show.image = photo
                    image_show.place(x=10, y=100)
                    try:
                        self.Image_NG, Point = ReadImageNG()
                        image_path_NG = self.pathbackup + '/' + self.PartNumber_show + "/NG/" + Point + "/" + self.Image_NG[len(self.Image_NG) - 1]
                        imageNG = cv.imread(image_path_NG)
                        imageNG = cv.cvtColor(imageNG, cv.COLOR_BGR2RGB)
                        imageNG = Image.fromarray(imageNG)
                        photoNG = ImageTk.PhotoImage(imageNG.resize((NGheight, NGweight)))
                        image_show_NG = customtkinter.CTkLabel(master=ViewNG, text="")
                        image_show_NG.photoNG = photoNG
                        image_show_NG.configure(image=photoNG)
                        image_show_NG.place(x=1000, y=100)
                    except:
                        pass
            else:
                messagebox.showwarning('Path','Directory is empty')
        else:
            messagebox.showwarning('Backup','Directory is empty')

if startapp:
    app = App()
    app.mainloop()
elif startapp is False:
    messagebox.showerror('Camera', 'Camera does not match the settings')
