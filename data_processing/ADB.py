import subprocess
import json
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class ADB:
    def __init__(self):
        self.ADB_PATH = r"C:\ADB\adb.exe"
        self.command = "shell getprop ro.product.model"
        self.type = sys.argv[1]
        self.json_file_path = "data/device.json"

    def Get_id_devices(self):
        try:
            result = subprocess.run(f"{self.ADB_PATH} devices", capture_output=True, text=True, shell=True)
            devices = result.stdout.strip().splitlines()[1:]
            connected_devices = [device.split()[0] for device in devices if 'device' in device]
            return connected_devices
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
            return []

    def Get_name_devices(self):
        device_ids = self.Get_id_devices()
        device_list = []

        if device_ids:
            for device_id in device_ids:
                full_command = f"{self.ADB_PATH} -s {device_id} {self.command}"
                result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
                
                device_name = result.stdout.strip()
                error = result.stderr.strip()

                if error:
                    print(f"Error for device {device_id}: {error}")
                else:
                    device_list.append({
                        "device_id": device_id,
                        "device_name": device_name if device_name else "Unknown",
                        "app": []
                    })
        
        return device_list

    def get_application_tiktok(self):
        application_list = []
        result = subprocess.run([self.ADB_PATH, 'devices'], capture_output=True, text=True)
        devices = result.stdout.strip().split("\n")[1:]

        if not devices or devices[0] == "":
            print("No devices connected.")
            return application_list

        for device in devices:
            device_id = device.split()[0]
            app_result = subprocess.run([self.ADB_PATH, '-s', device_id, 'shell', 'pm', 'list', 'packages'], capture_output=True, text=True)
            installed_packages = app_result.stdout.strip().split("\n")

            for package in installed_packages:
                package_name = package.replace("package:", "").strip()
                if "zhiliaoapp" in package_name:
                    app_name = package_name.split(".")[-1].capitalize()
                    application_list.append({
                        "id": package_name,
                        "name": app_name,
                        "status": "Connected"
                    })

        return application_list

    def update_json_file(self, new_data):
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump({"data": []}, f, ensure_ascii=False, indent=2)

        with open(self.json_file_path, 'r+', encoding='utf-8') as f:
            file_data = json.load(f)
            
            for new_device in new_data:
                device_exists = False
                for existing_device in file_data['data']:
                    if existing_device['device_id'] == new_device['device_id']:
                        device_exists = True
                        # Update existing device information
                        existing_device['device_name'] = new_device['device_name']
                        # Update or add new apps
                        for new_app in new_device['app']:
                            app_exists = False
                            for existing_app in existing_device['app']:
                                if existing_app['id'] == new_app['id']:
                                    app_exists = True
                                    existing_app.update(new_app)
                                    break
                            if not app_exists:
                                existing_device['app'].append(new_app)
                        break
                
                if not device_exists:
                    file_data['data'].append(new_device)
            
            f.seek(0)
            json.dump(file_data, f, ensure_ascii=False, indent=2)
            f.truncate()
            
    def save_account(self):
        self.data = sys.argv[2]
        parser_data = json.loads(self.data)
        
        with open(r'data\group_accounts.json', 'r') as file:
            data = json.load(file)
        
        # Duyệt qua các nhóm trong JSON để tìm nhóm có tên tương ứng
        for device in data['data']:
            if device['name_group'] == parser_data['group_name']:
                try:
                    # Kiểm tra nếu nhóm đã có 'account', thì cập nhật
                    if 'data' in device:
                        device['data'].append({
                            'user': parser_data['user'],
                            'password': parser_data['password'],
                            'cookie': parser_data['cookie'],
                            'proxy': parser_data['proxy'],
                            'status': 'disconnected'
                        })
                    else:
                        # Nếu chưa có 'account', tạo mới
                        device['data'] = [{
                            'user': parser_data['user'],
                            'password': parser_data['password'],
                            'cookie': parser_data['cookie'],
                            'proxy': parser_data['proxy'],
                            'status': 'disconnected'
                        }]
                    break
                except Exception as e:
                    print(f"Error updating account: {e}")
        
        # Ghi lại dữ liệu đã cập nhật vào file JSON
        with open(r'data\group_accounts.json', 'w') as file:
            json.dump(data, file, indent=4)
        
        print('Updated')
                            
    def create_groups(self):
        name_group_account = sys.argv[2]
        name_group = json.loads(name_group_account)

        # Mở file JSON để đọc dữ liệu
        with open(r'data\group_accounts.json', 'r') as file:
            datas = json.load(file)
        
        status = True  # Đặt mặc định là True, nếu tìm thấy thì chuyển sang False

        # Kiểm tra xem nhóm đã tồn tại chưa
        for data in datas['data']:
            if data['name_group'] == name_group['name_group']:  # Sửa 'name_group' thành đúng key
                status = False
                break
        
        # Nếu nhóm chưa tồn tại, thêm nó vào dữ liệu
        if status:
            datas['data'].append({'name_group': name_group['name_group']})  # Thêm nhóm mới

            # Ghi lại file JSON sau khi cập nhật
            with open(r'data\group_accounts.json', 'w') as file:
                json.dump(datas, file, indent=4)
            
            print('create groups successfully')
        else:
            print('Group already exists')
            
    def save_file_account(self):
        # Lấy dữ liệu từ tham số dòng lệnh và chuyển thành JSON
        self.data = sys.argv[2]
        parser_data = json.loads(self.data)
        
        # try:
            # Đọc file JSON hiện có
        with open(r'data\group_accounts.json', 'r') as file:
            data = json.load(file)
        

        for get_data in data['data']:
            if get_data['name_group'] == parser_data['name_group']:
                for get_data_account in parser_data['data']:
                    try:
                        # Kiểm tra nếu nhóm đã có 'account', thì cập nhật
                        if 'data' in get_data:
                            get_data['data'].append({
                                'user': get_data_account['user'],
                                'password': get_data_account['password'],
                                'cookie': get_data_account['cookie'],
                                'proxy': get_data_account['proxy'],
                                'status': 'disconnected'
                            })
                        else:
                            # Nếu chưa có 'account', tạo mới
                            get_data['data'] = [{
                                'user': get_data_account['user'],
                                'password': get_data_account['password'],
                                'cookie': get_data_account['cookie'],
                                'proxy': get_data_account['proxy'],
                                'status': 'disconnected'
                            }]
                    except Exception as e:
                        print(f"Error updating account: {e}")
                break
       
        # Ghi lại dữ liệu đã cập nhật vào file JSON
        with open(r'data\group_accounts.json', 'w') as file:
            json.dump(data, file, indent=4)

        print('Updated successfully')
        #

    def maint(self):
        if self.type == 'information_device':
            devices_info = self.Get_name_devices()
            for device in devices_info:
                device['app'] = self.get_application_tiktok()
            self.update_json_file(devices_info)
            print(json.dumps(devices_info, indent=2, ensure_ascii=False))
        elif self.type == 'application_tiktok':
            devices_info = self.get_application_tiktok()
            print(json.dumps(devices_info, indent=2, ensure_ascii=False))
        elif self.type == 'save_account_facebook':
            devices_info = self.save_account()
            print(json.dumps(devices_info, indent=2, ensure_ascii=False))
        elif self.type == 'create_groups_account':
            devices_info = self.create_groups()
            print(json.dumps(devices_info, indent=2, ensure_ascii=False))
        elif self.type == 'save_file_account':
            devices_info = self.save_file_account()
            print(json.dumps(devices_info, indent=2, ensure_ascii=False))
            
            
            
            

if __name__ == "__main__":
    ADB().maint()