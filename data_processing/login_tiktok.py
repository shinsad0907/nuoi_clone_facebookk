import subprocess
import xml.etree.ElementTree as ET
import time
import io,sys,json
class Login:
    def __init__(self, adb_path=r'ABD\adb.exe'):
        self.adb = adb_path

    def execute_adb_command(self, command, device_id=None):
        cmd = [self.adb]
        if device_id:
            cmd.extend(['-s', device_id])
        cmd.extend(command)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error executing command: {' '.join(cmd)}")
            print(f"Error message: {result.stderr.strip()}")
        return result.stdout.strip()

    def get_ui(self):
        self.execute_adb_command(['shell', 'rm', '/sdcard/ui.xml'])
        self.execute_adb_command(['shell', 'uiautomator', 'dump', '/sdcard/ui.xml'])
        self.execute_adb_command(['pull', '/sdcard/ui.xml', 'ui.xml'])
        print("UI XML file downloaded.")

    def check_ui(self, resource_id):
        self.get_ui()
        try:
            tree = ET.parse(r'ui.xml')
            root = tree.getroot()
            for node in root.iter('node'):
                if node.attrib.get('resource-id') == resource_id:
                    return True
            return False
        except ET.ParseError:
            print("Error parsing UI XML file.")
            return False

    def wait_for_ui(self, resource_id, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_ui(resource_id):
                print(f"Found UI element: {resource_id}")
                return True
            time.sleep(1)
        print(f"Timeout: UI element not found: {resource_id}")
        return False

    def input_text(self, device_id, text):
        time.sleep(1)
        text = text.replace(" ", "%s")
        self.execute_adb_command(['shell', 'input', 'text', text], device_id)

    def tap(self, device_id, x, y):
        time.sleep(1)
        self.execute_adb_command(['shell', 'input', 'tap', str(x), str(y)], device_id)

    def swipe_up(self, device_id):
        time.sleep(1)
        self.execute_adb_command(['shell', 'input', 'swipe', '500', '1500', '500', '500'], device_id)

    def launch_app(self, device_id, package_name):
        self.execute_adb_command(['shell', 'pm', 'clear', package_name], device_id)
        self.execute_adb_command(['shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'], device_id)

    def main(self, device_id, package_name):
        self.launch_app(device_id, package_name)
        if self.wait_for_ui(f'{package_name}:id/ck9'):
            self.tap(device_id, 992, 2038)
        if self.wait_for_ui(f'{package_name}:id/bf7'):
            self.tap(device_id, 95, 2034)
        if self.wait_for_ui(f'{package_name}:id/nl8'):
            self.tap(device_id, 84, 1981)
        if self.wait_for_ui(f'{package_name}:id/qc2'):
            self.swipe_up(device_id)
        if self.wait_for_ui(f'{package_name}:id/ih9'):
            self.tap(device_id, 864, 2029)
        else:
            self.tap(device_id, 864, 2029)
        if self.wait_for_ui(f'{package_name}:id/cl8'):
            self.tap(device_id, 79, 675)
            time.sleep(1)
            self.tap(device_id, 123, 1193)
        else:
            self.tap(device_id, 79, 675)
        if self.wait_for_ui('android:id/text1'):
            self.tap(device_id, 540, 200)
        if self.wait_for_ui(f'{package_name}:id/ggr'):
            self.tap(device_id, 84, 432)
            self.input_text(device_id, 'user8842988133184')
        else:
            self.tap(device_id, 84, 432)
            self.input_text(device_id, 'user8842988133184')
        if self.wait_for_ui(f'{package_name}:id/cxx'):
            self.tap(device_id, 84,1028)
            self.tap(device_id, 84, 1992)
        else:
            self.tap(device_id, 84,1028)
            self.tap(device_id, 84, 1992)
        if self.wait_for_ui(f'{package_name}:id/ggr'):
            self.tap(device_id, 84,421)
            self.input_text(device_id, 'Thuynga@1205')
        else:
            self.tap(device_id, 84,421)
            self.input_text(device_id, 'Thuynga@1205')
        if self.wait_for_ui(f'{package_name}:id/cxx'):
            self.tap(device_id, 84,1028)
            self.tap(device_id, 84, 1992)
        else:
            self.tap(device_id, 84,1028)
            self.tap(device_id, 84, 1992)
            

        print("Login process completed.")

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    data = sys.argv[1]
    parser_data = json.loads(data)
    login = Login()
    login.main(parser_data[0]['id_device'], parser_data[0]['application'])