import os
import wmi
import sys
import socket
import datetime
import tempfile
from ftplib import FTP

from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QMessageBox

import editTool

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
form_class = uic.loadUiType(BASE_DIR + r'\resource\mainWindow.ui')[0]


class Validator(QtGui.QValidator):
    def validate(self, string, pos):
        return QtGui.QValidator.Acceptable, string.upper(), pos
        # for old code still using QString, use this instead
        # string.replace(0, string.count(), string.toUpper())
        # return QtGui.QValidator.Acceptable, pos



class QWindow(QMainWindow, form_class):

    filtered_manufacturer = "default"

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # self.setWindowState(Qt.WindowMaximized)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # input_serial 속성 지정
        self.validator = Validator(self)
        self.input_serial.setValidator(self.validator)
        self.input_serial.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("[0-9A-Z]*")))

        # 시그널 슬롯 처리
        self.btn_start.clicked.connect(self.btnStart)
        self.btn_hwscan.clicked.connect(self.btnHwScan)
        self.input_serial.returnPressed.connect(self.btnStart)
        self.btn_report.clicked.connect(self.error_report)

        if tpm == "Not Found" :
            QMessageBox.warning(self, "ERROR", "TPM ERROR\n\n한성BIOS 적용 또는 TPM설정을 확인하세요")
            exit()

        # self.textBrowser_info.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # if self.filtered_manufacturer == "default" :
        inst_tool.base_bios_infoes = inst_tool.get_biosinfo(inst_wmi, **inst_tool.base_bios_infoes)
        self.filtered_manufacturer = inst_tool.filter_manuf(**inst_tool.base_bios_infoes)
        self.setWindowTitle(f'[HANSUNG] S/N Edit Tool - {self.filtered_manufacturer}')

        self.enableUi()
        self.btnHwScan()
        self.input_serial.setFocus()
        
    def btnStart(self):
        # 버튼 비활성화 / 상태바 'Done'
        self.disableUi()

        url = "https://testadm.monsterlabs.co.kr/wms_api/injection_resetdata.php"
        self.serial = self.input_serial.text()
        
        if self.serial == "" :
            self.textBrowser_status.append(' # Error : S/N 미입력 오류')
            self.textBrowser_status.repaint()
            self.enableUi()
            return
        else :
            self.textBrowser_status.append('[SYS] start..')
            self.textBrowser_status.repaint()
        
        res_set_serial = inst_tool.set_serial(self.filtered_manufacturer, self.serial)
        
        if res_set_serial == 'OK' :
            self.textBrowser_status.append('[SYS] Serial Number 삽입 완료')
            self.textBrowser_status.repaint()
        else :
            self.textBrowser_status.append(res_set_serial)
            self.textBrowser_status.append(' # Error : Serial Number 삽입 실패')
            self.textBrowser_status.repaint()
            # self.enableUi()
            # return

        res_request = inst_tool.send_request(url, self.serial, **inst_tool.base_system_infoes)
        # res_request = '1'
        if res_request == '1' : 
            self.textBrowser_status.append('[SYS] Serial Number 정보 확인 완료')
            self.textBrowser_status.append('[SYS] 시스템 정보 전송 완료')
            self.textBrowser_status.repaint()
            QMessageBox.information(self, "[HANSUNG] S/N Edit Tool", "\nS/N 삽입 및 장치정보 전송 완료\n")
            exit()
        elif res_request == 'ERR' : 
            self.textBrowser_status.append(' # Error : 시스템 정보 관련 오류')
            self.textBrowser_status.repaint()
        elif res_request == 'NO' : 
            self.textBrowser_status.append(' # Error : 확인되지 않은 Serial Number')
            self.textBrowser_status.repaint()
        elif res_request == "Request - Error Connecting" :
            self.textBrowser_status.append(f' # Error : {res_request} ')
            self.textBrowser_status.append(' # Error : 인터넷 연결 상태를 확인하십시오. ')
            self.textBrowser_status.repaint()
        else :
            self.textBrowser_status.append(f' # Error : {res_request} ')
            self.textBrowser_status.repaint()

        self.enableUi()

    def btnHwScan(self):
        # 버튼 비활성화 / 상태바 'Done'
        # 제품정보, 시리얼 입력 라인 초기화
        self.disableUi()
        self.resetTexts()
        # 제품정보 출력
        inst_tool.base_system_infoes = inst_tool.get_sysinfo(inst_wmi, **inst_tool.base_system_infoes)
        for key in inst_tool.base_system_infoes :
            self.textBrowser_info.append(f' {key} : {inst_tool.base_system_infoes[key]}')
        for key in inst_tool.base_bios_infoes :
            self.textBrowser_info.append(f' {key} : {inst_tool.base_bios_infoes[key]}')
        self.textBrowser_info.repaint()
        self.enableUi()
        self.input_serial.setFocus()

    def enableUi(self):
        # 버튼 활성화
        self.btn_hwscan.setEnabled(True)
        self.btn_start.setEnabled(True)
        # 하단 상태바 변경 : Done
        self.statusbar.showMessage('Done')
        self.statusbar.repaint()

    def disableUi(self):
        # 버튼 비활성화
        self.btn_hwscan.setEnabled(False)
        self.btn_start.setEnabled(False)
        # 하단 상태바 변경 : Loading..
        self.statusbar.showMessage('Loading..')
        self.statusbar.repaint()

    def cetnerSet(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def resetTexts(self):
        self.input_serial.clear()
        self.input_serial.repaint()
        self.textBrowser_info.clear()
        self.textBrowser_info.repaint()
        self.textBrowser_status.clear()
        self.textBrowser_status.repaint()
    
    def net_check(self): # adding function
        port=5000
        timeout=1

        try:
            host="192.168.20.233"
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True, host
        except socket.error as ex:
            pass

        try:
            host="10.10.10.11"
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True, host
        except socket.error as ex:
            print(ex)
            return False, "None"

    def error_report(self): # adding function
        net, ip = self.net_check()
        if net:
            time = self.get_time()
            tempdir = tempfile.gettempdir()
            status = self.textBrowser_status
            mb_model = inst_tool.base_bios_infoes["Product"].replace(' ','_')
            upload_path = (fr'hansung/Windows/Win10/hansung_sntool/error_report/')

            self.serial = self.input_serial.text()
            if self.serial == "" :
                upload_name = (fr'{time}_{mb_model}_default.txt')
            else :
                upload_name = (fr'{time}_{mb_model}_{self.serial}.txt')

            self.textBrowser_status.append("sending report")
            self.textBrowser_status.repaint()
            
            with tempfile.TemporaryFile('w+',dir=tempdir, suffix='.data') as temp_f:
                temp_file = temp_f.name
                temp_f.write('@@@ System info @@@')
                for key, value in inst_tool.base_system_infoes.items() :
                    temp_f.write('\n')
                    temp_f.write(f' {key} : {value}')
                temp_f.write('\n')
                temp_f.write('@@@ BIOS info @@@')
                for key, value in inst_tool.base_bios_infoes.items() :
                    temp_f.write('\n')
                    temp_f.write(f' {key} : {value}')
                temp_f.write('\n')
                temp_f.write('@@@ Status browser @@@')
                temp_f.write('\n')
                temp_f.write(str(status))
                temp_f.write('\n')
                print(temp_f.read())

            # with FTP(ip) as ftp:
            #     ftp.login('lab_sjh', 'wlgh1595@')
            #     ftp.encoding = 'utf-8'
            #     ftp.cwd(upload_path)
            #     with open(file=temp_file, mode='rb') as wf:
            #         ftp.storbinary('STOR 3.ttf', wf)
            #     os.system('pause')
            #     # file.replace('\\','\')
            #     # upload_path.replace('\\','/')
            #     # with open(full_fname, 'w') as localfile:
            #     #     localfile.write('@@@ System info @@@')
            #     #     for key, value in inst_tool.base_system_infoes.items() :
            #     #         localfile.write('\n')
            #     #         localfile.write(f' {key} : {value}')
            #     #     localfile.write('\n')
            #     #     localfile.write('@@@ BIOS info @@@')
            #     #     for key, value in inst_tool.base_bios_infoes.items() :
            #     #         localfile.write('\n')
            #     #         localfile.write(f' {key} : {value}')
            #     #     localfile.write('\n')
            #     #     localfile.write('@@@ Status browser @@@')
            #     #     localfile.write('\n')
            #     #     localfile.write(str(status))
            #     #     localfile.write('\n')
                
            #     with open(temp_f_dir, 'rb') as localfile:
            #         ftp.cwd(upload_path)
            #         ftp.storbinary('STOR '+upload_name, localfile)
            #         ftp.quit()

                
            # ftp = FTP('10.10.10.11')
            # ftp.login('factory', 'todtks01')
            
            # ftp.cwd(upload_path)  # 업로드할 FTP 폴더로 이동
            # file = open(temp_f,'rb')  # 로컬 파일 열기
            # ftp.storbinary('STOR ' +upload_path, temp_f )  # 파일을 FTP로 업로드
            # file.close()  # 파일 닫기
            # ftp.quit()

            return
        else:
            self.textBrowser_status.append("please network check")
            self.textBrowser_status.repaint()
            return


    def get_time(self):
        time = datetime.datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
        return time


    def exit_error(self):
        
        exit()


if __name__ == "__main__":

    inst_wmi = wmi.WMI()
    inst_wmi_tpm = wmi.WMI(namespace="root/cimv2/security/microsofttpm")
    inst_tool = editTool.EditTool()

    tpm = inst_tool.get_tpm(inst_wmi_tpm)

    if len(tpm) == 0 :
        tpm = "Not Found"
    elif tpm[0].IsActivated() :
        print("tpm is okay")
    else :
        tpm = "Not Found"
    tpm = 'ok'
    app = QApplication(sys.argv)
    inst_Window = QWindow()
    inst_Window.show()
    sys.exit(app.exec_())

















    # inst_wmi = wmi.WMI()
    # inst_tool = EditTool()
    # base_bios_infoes = inst_tool.get_biosinfo(inst_wmi, **base_bios_infoes)
    # base_system_infoes = inst_tool.get_sysinfo(inst_wmi, **base_system_infoes)
    # filtered_manufacturer = inst_tool.filter_manuf(**base_bios_infoes)
    # os.system(f'title [HANSUNG] S/N Edit Tool - {filtered_manufacturer}')

    # serialNumber = input("S/N : ")
    # result = inst_tool.set_serial(filtered_manufacturer, serialNumber)

    # if result == 0 :
    #     inst_tool.send_request("https://testadm.monsterlabs.co.kr/wms_api/injection_resetdata.php", **base_system_infoes)
    # else :
    #     print('ERROR - SMBIOS TOOL ERROR')

    while False:
        os.system('cls')  # 화면 지우기

        inst_tool.print_infoes(base_bios_infoes)
        print()
        inst_tool.print_infoes(base_system_infoes)
        print()
        print(inst_tool.print_menu())
        sel_menu = input('선택 >>> ')

        if sel_menu == '1':  # 시리얼 삽입
            serialNumber = input("S/N : ")
            print(inst_tool.set_serial(filtered_manufacturer, serialNumber))

        # elif sel_menu == '2':  # 시리얼 조회 (Windows)
        #     base_bios_infoes['SerialNumber_Win'] = get_serial_win(inst_wmi)
        #     print(base_bios_infoes['SerialNumber_Win'])

        elif sel_menu == '3':  # 시리얼 조회 (BIOS)
            print(inst_tool.get_serial(filtered_manufacturer))

        elif sel_menu == '4':  # 시리얼 초기화 [ Default ]
            print(inst_tool.set_serial(filtered_manufacturer, "Default"))

        elif sel_menu == '5':  # 리퀘스트 전송
            inst_tool.send_request("https://testadm.monsterlabs.co.kr/wms_api/injection_resetdata.php", **base_system_infoes)

        elif sel_menu == 'q':  # 프로그램 종료
            print('종료합니다.')  
            exit()

        else:
            print('1 ~ 4 or q 중에서 입력해야 합니다.')

        os.system('pause')

