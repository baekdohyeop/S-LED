import sys
import serial
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from PIL import ImageGrab
import time
import numpy as np
import pyaudio
import keyboard
import win32gui
import win32process
import win32api
import win32con

MODE_NAME = ["화면에 반응", "무지개 파도", "소리에 반응"]
KEYINPUT_BUFFER = []
PATTERNS = {}
EXE_NAME = ""
effect = {'0':'a', '1':'b', '2':'c', '3':'d', '4':'e'}

MODE = 0
PORT = 'COM3'
CHUNK = 1024
DEVICE = 1
BaudRate = 2000000
ARD = serial.Serial(PORT, BaudRate)
STREAM = pyaudio.PyAudio().open(
        format = pyaudio.paInt16,
        channels = 1,
        rate = 44100,
        input = True,
        frames_per_buffer = CHUNK,
        input_device_index = DEVICE
        )
form_class = uic.loadUiType("fin.ui")[0]

class WindowClass(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.serial_process = SerialProcess()
        self.serial_process.start()
        self.keyboard_process = KeyboardProcess()
        self.keyboard_process.start()
        
        self.pushButton_2.clicked.connect(self.prevmode)
        self.pushButton.clicked.connect(self.nextmode)
        self.toolButton.clicked.connect(self.getfilepath)
        self.pushButton_5.clicked.connect(self.addpattern)
        self.pushButton_3.clicked.connect(self.removepattern)
    
    def prevmode(self):
        global ARD
        ARD.write('<'.encode('ascii'))
        global MODE
        global MODE_NAME
        MODE -= 1
        if MODE == -1:
            MODE = 2
        self.label.setText(MODE_NAME[MODE])
    
    def nextmode(self):
        global ARD
        ARD.write('>'.encode('ascii'))
        global MODE
        global MODE_NAME
        MODE += 1
        if MODE == 3:
            MODE = 0
        self.label.setText(MODE_NAME[MODE])
        
    def getfilepath(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', "", "All Files(*);; Python Files(*.py)", "C:/Windows")
        
        if fname[0]:
            self.label_2.setText(fname[0].split('/')[-1])
    
    def removepattern(self):
        if self.listWidget.currentRow() == -1:
            QMessageBox.about(self, "Warning", "패턴을 선택하지 않았습니다.")
            return
        
        global PATTERNS
        
        rdata = str(self.listWidget.takeItem(self.listWidget.currentRow()).text()).replace(' ', '').split(',')

        rprocess = rdata[0].split('=')[-1]
        rpattern = rdata[1].split('=')[-1]
        reffect = rdata[2].split('=')[-1]
        
        idx = 0
        for p in PATTERNS[rprocess]:
            if p[0] == rpattern and p[1] == reffect:
                break
            idx+=1
        PATTERNS[rprocess].pop(idx)
            

    def addpattern(self):
        if self.label_2.text() == '프로세스 선택':
            QMessageBox.about(self, "Warning", "프로세스를 선택하지 않았습니다.")
            return
        if len(self.lineEdit.text()) > 10:
            QMessageBox.about(self, "Warning", "최대 패턴 길이를 초과했습니다.")
            return
        elif self.lineEdit.text():
            for ch in self.lineEdit.text():
                if not 'a' <= ch <= 'z':
                    QMessageBox.about(self, "Warning", "잘못된 패턴을 입력했습니다.")
                    return
        else:
            QMessageBox.about(self, "Warning", "패턴을 입력하지 않았습니다.")
            return
        checked = [ 
                self.radioButton1.isChecked(),
                self.radioButton2.isChecked(),
                self.radioButton3.isChecked(),
                self.radioButton4.isChecked(),
                self.radioButton5.isChecked(),
                ]
        if not True in checked:
            QMessageBox.about(self, "Warning", "효과를 선택하지 않았습니다.")
            return
        
        self.listWidget.addItem('PROCESS=' + self.label_2.text() + ', PATTERN=' + self.lineEdit.text() + ', EFFECT=' + str(checked.index(True)))
        
        if self.label_2.text() in PATTERNS:
            PATTERNS[self.label_2.text()].append([self.lineEdit.text(), str(checked.index(True))])
        else:
            PATTERNS[self.label_2.text()] = [ [self.lineEdit.text(), str(checked.index(True))]]
        
        
        self.label_2.setText('프로세스 선택')
        self.lineEdit.setText('')
        
            
class SerialProcess(QThread):
    def run(self):
        global MODE
        
        while True:
            if MODE == 0:
                px = ImageGrab.grab().load()  
                rsum = 0
                gsum = 0
                bsum = 0   
                num_pixel = 192 * 108        
                for y in range(0, 1080, 10):
                    for x in range(0, 1920, 10):
                        rsum += px[x, y][0]
                        gsum += px[x, y][1]
                        bsum += px[x, y][2]
                R = rsum // num_pixel
                G = gsum // num_pixel
                B = bsum // num_pixel
                DATA = str(R).zfill(3)+str(G).zfill(3)+str(B).zfill(3)
                DATA = DATA.encode('ascii')
                ARD.write(DATA)
                time.sleep(0.1)
            elif MODE == 2:
                data = np.fromstring(STREAM.read(CHUNK), dtype=np.int16)
                volume = np.average(np.abs(data))
                volume_ls = int(volume / (2 ** 15) * 100)
                if volume_ls >= 72:
                    volume_ls = 72
                DATA = str(volume_ls).zfill(2).encode('ascii')
                ARD.write(DATA)

class KeyboardProcess(QThread):
    def run(self):
        keyboard.hook(pressed_keys_hook)
        keyboard.wait()
    
    
def pressed_keys_hook(e):
    temp = str(e).split('(')[1]
    ch = ""
    ud = ""
    
    if temp == "":
        ch = "("
        ud = str(e).split(' ')[1][:-1]
    else:
        ch = temp.split(' ')[0]
        ud = temp.split(' ')[1][:-1]
    
    global EXE_NAME, KEYINPUT_BUFFER, PATTERNS
    
    hwnd = win32gui.GetForegroundWindow()
    pid = win32process.GetWindowThreadProcessId(hwnd)
    handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid[1])
    proc_name = win32process.GetModuleFileNameEx(handle, 0).split('\\')[-1]
    if EXE_NAME != proc_name:
        KEYINPUT_BUFFER = []
        EXE_NAME = proc_name
    if ud == 'down' and 'a' <= ch and ch <= 'z' and len(ch) == 1:
        KEYINPUT_BUFFER.append(ch)
        if len(KEYINPUT_BUFFER) > 10:
            KEYINPUT_BUFFER.pop(1)
        if EXE_NAME in PATTERNS:
            for i in range(len(KEYINPUT_BUFFER)):
                for pattern in PATTERNS[EXE_NAME]:
                    if ''.join(KEYINPUT_BUFFER[i:]) == pattern[0]:
                        global ARD, effect
                        ARD.write(effect[pattern[1]].encode('ascii'))
                
    elif ud == 'down':
        KEYINPUT_BUFFER.append(' ')
        if len(KEYINPUT_BUFFER) > 10:
            KEYINPUT_BUFFER.pop(1)
    
       
app = QApplication(sys.argv)
myWindow = WindowClass()
myWindow.show()
app.exec_()
ARD.close()