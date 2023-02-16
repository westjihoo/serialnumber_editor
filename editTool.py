import json
import requests
import re
import subprocess
import os

class EditTool:

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    base_bios_infoes = {
        "Manufacturer" : "default",
        "BIOS_Manufacturer" : "default",
        "Product" : "default",
        "SerialNumber_Win" : "default",
        "BATTERY" : "default"
    }

    base_system_infoes = {
    }

    with open(BASE_DIR + r'\resource\toolinfo.json') as cfg :
        config = json.load(cfg)

    with open(BASE_DIR + r'\resource\venderlist.data') as vender :
        list_vender = vender.read().splitlines()


    def get_biosinfo(self, wmi, **infoes) :
        temp_info = wmi.Win32_BaseBoard()[0]
        infoes['Manufacturer'] = (temp_info.Manufacturer).upper()
        infoes['Product'] = (temp_info.Product).upper()

        temp_info = wmi.Win32_BIOS()[0]
        infoes['BIOS_Manufacturer'] = (temp_info.Manufacturer).upper()
        infoes['SerialNumber_Win'] = (temp_info.SerialNumber)

        temp_info = wmi.Win32_Battery()
        if temp_info == [] :
            infoes['BATTERY'] = "N"
        else :
            infoes['BATTERY'] = "Y"
        return infoes


    def get_sysinfo(self, wmi, **infoes):
        temp_info = wmi.Win32_Processor()
        i = 0
        for l in temp_info :
            infoes[f'CPU{i}'] = l.Name
            i+=1

        temp_info = wmi.Win32_VideoController()
        i = 0
        for l in temp_info :
            infoes[f'GPU{i}'] = l.Name
            i+=1

        temp_info = wmi.Win32_PhysicalMemory()
        for l in temp_info :
            str = l.BankLabel
            i = re.sub(r'[^0-9]', "", str)
            infoes[f'RAM{i}'] = f'{int((l.Capacity))/1073741824}GB'

        temp_info = wmi.Win32_DiskDrive()
        for l in temp_info :
            if l.Model.find('USB') == -1 :
                infoes[f'STORAGE{l.index}'] = l.Model
        return infoes


    def get_tpm(self, wmi) :
        temp_info = wmi.Win32_Tpm()
        return temp_info



    def send_request(self, url, serial, **datas) :
        datas_xml = ""
        for key in datas :
            datas_xml += f'<p n="{key}" v="{datas[key]}" />'
        sending_data = {
            "SerialNumber" : serial,
            "HARDWAREXML" : datas_xml
                        }
        try:
            res = requests.post(url, data=sending_data, verify=False)
            return res.text

        except requests.exceptions.Timeout:
            err = "Request - Timeout Error"
            return err
        except requests.exceptions.ConnectionError:
            err = "Request - Error Connecting"
            return err
        except requests.exceptions.HTTPError:
            err = "Request - Http Error"
            return err
        except requests.exceptions.RequestException:
            err = "Request - AnyException"
            return err


    def filter_manuf(self, **infoes) : # return init_Manufacturer
        init_Manufacturer="default"
        for vender in self.list_vender :
            vender=vender.upper()
            sel_menu = infoes['Manufacturer'].find(vender)
            if sel_menu != -1 :
                init_Manufacturer = vender
                break
        if init_Manufacturer=="default" and self.base_bios_infoes['BATTERY'] == "Y" :
            sel_menu = infoes['BIOS_Manufacturer'].find('AMERICAN')
            if sel_menu != -1 :
                init_Manufacturer = 'TONGFANG_AMI'
            sel_menu = infoes['BIOS_Manufacturer'].find('INSYDE')
            if sel_menu != -1 :
                init_Manufacturer = 'CLEVO'
        return init_Manufacturer

    # def get_serial_win(wmi): # return serial
    #     temp_info = wmi.Win32_BIOS()[0]
    #     serial = temp_info.SerialNumber.upper()
    #     return serial

    def set_serial(self, filtered_manufacturer, serialNumber): # return result
        serialNumber = serialNumber.upper()

        if filtered_manufacturer == 'default' :
            return ' # Error : manufacturer filtering error'

        self.config[filtered_manufacturer]

        DMI_tool = self.config[filtered_manufacturer]
        
        if filtered_manufacturer == 'CLEVO' :
            pram = "-SS"
        else :
            pram = "/SS"

        for i in DMI_tool :
            result = subprocess.getstatusoutput(self.BASE_DIR + fr'\resource\DMI-tools\{DMI_tool[i]["folder"]}\x64\{DMI_tool[i]["exe"]} {pram} "{serialNumber}"')
            # result = subprocess.getstatusoutput(self.BASE_DIR + fr'\resource\DMI-tools\{DMI_tool[i]["folder"]}\x64\{DMI_tool[i]["exe"]} {pram}')
            if result[0] == 0 : break

        if result[0] == 0 :
            return 'OK'
        else :
            return ' # Error : DMI tool error'
            # return result[1]


        # if filtered_manufacturer == 'CLEVO' :
        #     result = subprocess.getstatusoutput(f'resource\\DMI-tools\\{DMI_tool["folder"]}\\x64\\{DMI_tool["exe"]} -SS "{serialNumber}"')
        # else :
        #     result = subprocess.getstatusoutput(f'resource\\DMI-tools\\{DMI_tool["folder"]}\\x64\\{DMI_tool["exe"]} /SS "{serialNumber}"')
        
        # if result[0] == 0 :
        #     return 'OK'
        # elif filtered_manufacturer == 'CLEVO' :
        #     result = subprocess.getstatusoutput(f'resource\\DMI-tools\\{DMI_tool["folder_2nd"]}\\x64\\{DMI_tool["exe_2nd"]} -SS "{serialNumber}"')
        # else :
        #     result = subprocess.getstatusoutput(f'resource\\DMI-tools\\{DMI_tool["folder_2nd"]}\\x64\\{DMI_tool["exe_2nd"]} /SS "{serialNumber}"')
        
        # if result[0] == 0 :
        #     return 'OK'
        # else :
        #     return ' # Error : DMI tool error'

    # def get_serial(self, filtered_manufacturer): # print result
    #     DMI_tool = self.config[filtered_manufacturer]

    #     if filtered_manufacturer == 'CLEVO' :
    #         result = subprocess.getstatusoutput(f'resource\\DMI-tools\\{DMI_tool["folder"]}\\x64\\{DMI_tool["exe"]} -SS')
    #     else :
    #         result = subprocess.getstatusoutput(f'resource\\DMI-tools\\{DMI_tool["folder"]}\\x64\\{DMI_tool["exe"]} /SS')

    #     if result[0] == 0 :
    #         print('OK')
    #         return result[1]
    #     else :
    #         print('ERROR - SMBIOS TOOL ERROR')
    #         return result[1]


    # def print_menu(self): # print menu
    #     menu = ' 1. 시리얼 변경\n'
    #     menu += ' 2. 시리얼 조회 (Windows)\n'
    #     menu += ' 3. 시리얼 조회 (BIOS)\n'
    #     menu += ' 4. 시리얼 초기화\n'
    #     menu += ' q. 종료\n'
    #     return menu


    # def print_infoes(self, infoes): # print menu
    #     for key in infoes :
    #         print(f' {key} : {infoes[key]}')
        # info = f"M/B Manufacturer : {base_bios_infoes['Manufacturer']}\n"
        # info += f"BIOS_Manufacturer : {base_bios_infoes['BIOS_Manufacturer']}\n"
        # info += f"Product : {base_bios_infoes['Product']}\n"
        # info += f"SerialNumber : {base_bios_infoes['SerialNumber']}\n"
        # return info
