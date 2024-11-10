# login_facebook.py
import requests
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import json
import sys
import io
import os
import re
import threading
from functools import partial
from time import sleep
import time,random


class Facebook():
    def __init__(self):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        self.type = sys.argv[2]
        self.url = 'https://www.facebook.com/'
        self._print_lock = threading.Lock()
        self.sent_requests = 0
        self.max_requests = 10
        self.max_time = 20  # Thời gian tối đa (5 phút)
        self.stop_threads = False
        self.min_addFriends = 1
        self.max_addFriends = 3
        self.even_follow = True
        self.even_newFeed = False
        self.even_open_driver = False
    # Sử dụng Lock để đảm bảo việc in ấn an toàn

    def send_result(self, account_id, status, cookie=""):
        with self._print_lock:
            result = {
                "type": "result",
                "data": {
                    "id": account_id,
                    "status": status,
                    "cookie": cookie
                }
            }
            print(json.dumps(result))
            sys.stdout.flush()

    def send_log(self, message, account_id="unknown", status=None):
        with self._print_lock:
            log_data = {
                "type": "log",
                "id": account_id,
                "message": message,
                "status": status or "processing"
            }
            print(json.dumps(log_data))
            sys.stdout.flush()
        
    def check_die_cookie(self):
        title = self.driver.title
        current_url = self.driver.current_url
        if title == 'Facebook' and current_url == 'https://www.facebook.com/':
            return True
        else:
            return False
        # try:
        #     if title == 'Facebook - login in or sign up' and current_url == 'https://www.facebook.com/':
        #         return 'Login False die Cookie'
        #     elif title == 'Facebook' or (current_url.split('https://www.facebook.com/checkpoint/')[1].split('/')[0])[-3:] == '681':
        #         return 'Login False die 681'
        #     elif title == 'Facebook' or (current_url.split('https://www.facebook.com/checkpoint/')[1].split('/')[0])[-3:] == '282':
        #         return 'Login False die 282'
        #     else:
        #         return 'Login Successfully'
        # except :
        #     return 'Login False die 681 or 282 die'
    
    def open_session(self, name_group, account_id, cookie):
        """Mở session và duy trì nó trong khi các luồng khác có thể chạy song song."""
        chrome_profile_path = fr"C:\ChromeProfile\{name_group}\{account_id}"
        
        # Cấu hình để sử dụng profile đã lưu
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"user-data-dir={chrome_profile_path}")

        # Khởi tạo WebDriver với cấu hình đã định
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Gửi log và mở Facebook
        self.driver.set_window_size(400, 600)
        self.send_log("Đang bắt đầu đăng nhập...", account_id)
        self.driver.get("https://www.facebook.com")
        self.send_result(account_id, "Đang mở web Facebook", cookie)
        self.even_open_driver = True
        # Duy trì session một cách nhẹ nhàng để không khóa CPU
        while not self.stop_threads:
            try:
                # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                # time.sleep(random.uniform(2, 4))  # Thời gian ngẫu nhiên giữa mỗi lần cuộn
                # Kiểm tra xem phiên có còn hoạt động không
                self.driver.current_url
            except:
                self.stop_threads = True  # Nếu không mở được, dừng lại
            sleep(2)  # Chờ vài giây trước khi kiểm tra lại, giảm tải CPU

            

    def process_facebook_login(self, account):
        account_id = account.get('uid', 'unknown')
        cookie = account.get('cookie', 'unknown')
        name_group = account.get('group', 'unknown')
        
        try:
            self.open_session(name_group, account_id, cookie)
            
            # Các bước xử lý cookie
            cks = cookie.split(';')
            cks = [ck.strip() for ck in cks]
            
            ck_dict = {}
            self.send_result(account_id, "Đang login bằng cookie", cookie)
            
            for ck in cks:
                if '=' in ck:
                    key, value = ck.split('=', 1)
                    ck_dict[key] = value
            
            cks_list = [{'name': key, 'value': value} for key, value in ck_dict.items()]
            
            for ck in cks_list:
                try:
                    self.driver.add_cookie(ck)
                except Exception as cookie_error:
                    self.send_log(f"Lỗi thêm cookie: {str(cookie_error)}", account_id, "cookie_error")
            
            self.send_result(account_id ,"Add Cookie thành công", cookie)
            
            self.driver.refresh()
            sleep(20)
            
            # Các bước kiểm tra còn lại
            
        except Exception as e:
            self.send_log(f"Lỗi chi tiết: {str(e)}", account_id, "error")
            self.send_result(account_id, "Lỗi", "")
        finally:
            # Đóng trình duyệt nếu có
            if hasattr(self, 'driver'):
                try:
                    self.driver.quit()
                except Exception:
                    pass

    def scroll_friends(self, start_time,name_group, account_id, cookie):
        
    
        list_pixel = ['-= 10','-= 20','-= 30','+= 10', '+= 20', '+= 30', '+= 40', '+= 50', '+= 60']
        
        self.driver.get('https://www.facebook.com/friends/suggestions')
    
        scrollable_div = self.driver.find_element(By.XPATH, "/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div/div[2]")

        while not self.stop_threads:
            if (time.time() - start_time) >= self.max_time or self.sent_requests >= self.max_requests:
                self.stop_threads == True
                self.even_newFeed == True
                self.send_result(account_id, f"Ngưng add friend", cookie)
                break
            
            pixel = random.choice(list_pixel)
            
            # Cuộn từng chút một
            # Cuộn từng chút một
            for _ in range(10):  # Cuộn 10 lần cho mỗi lần thực hiện
                self.driver.execute_script(f"arguments[0].scrollTop {pixel}", scrollable_div)  # Cuộn 10 pixel mỗi lần
                time.sleep(random.uniform(0.05, 0.1))  # Thời gian chờ ngẫu nhiên giữa 50ms đến 100ms
                self.send_result(account_id, f"Cuộn {pixel} pixel", cookie)

            # Điều chỉnh giá trị của self.min_addFriends và self.max_addFriends dựa trên pixel
            if '-=' in pixel.split()[0]:
                self.min_addFriends -= int(int(pixel.split(' ')[1]) / 10)
                self.max_addFriends -= int(int(pixel.split(' ')[1]) / 10)
                
                # Đảm bảo giá trị không nhỏ hơn 0
                if self.min_addFriends < 0:
                    self.min_addFriends = 1
                if self.max_addFriends < 0:
                    self.max_addFriends = 3
            else:
                # Chia rồi chuyển về số nguyên
                self.min_addFriends += int(int(pixel.split(' ')[1]) / 10)
                self.max_addFriends += int(int(pixel.split(' ')[1]) / 10)

            # Gửi kết quả không có phần thập phân
            self.send_result(account_id, f"min_addFriends: {self.min_addFriends}, max_addFriends: {self.max_addFriends}", cookie)

            # Thời gian chờ giữa các lần cuộn
            time.sleep(random.uniform(3, 10)) 
    def click_addFriend(self, start_time, account_id, cookie):
        add_count = 0
        
        while not self.stop_threads:
            stt_addFriend = random.randint(int(self.min_addFriends), int(self.max_addFriends))
            if (time.time() - start_time) >= self.max_time or add_count >= 5:  # Giới hạn tối đa 5 lần thêm bạn bè
                self.even_newFeed == True
                self.send_result(account_id, f"Ngưng add friend", cookie)
                break

            try:
                try:
                    add_button_xpath = f"/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div/div[2]/div[1]/div[2]/div/div[{stt_addFriend}]/div/a/div[1]/div[2]/div/div[2]/div/div/div[1]/div[1]/div"
                    add_button = self.driver.find_element(By.XPATH, add_button_xpath)
                    add_button.click()
                except :
                    add_button_xpath = f"/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[1]/div[1]/div[1]/div/div[3]/div[1]/div[2]/div/div[{stt_addFriend}]/div/a/div[1]/div[2]/div/div[2]/div/div/div[1]/div[1]/div"
                    add_button = self.driver.find_element(By.XPATH, add_button_xpath)
                    add_button.click()
                add_count += 1
                self.send_result(account_id, f"Đã thêm bạn bè lần {stt_addFriend}", cookie)
            except Exception as e:
                self.send_result(account_id, f"Lỗi thêm bạn bè: {stt_addFriend}", cookie)

            time.sleep(random.uniform(15, 20))  # Delay giữa mỗi lần thêm bạn bè
        sleep(60)
        self.even_follow == True
        
    def surf_newFeed(self, name_group, account_id, cookie):
        self.driver.get('https://www.facebook.com/')
        list_pixel = ['-= 10','-= 20','-= 30','+= 10', '+= 20', '+= 30', '+= 40', '+= 50', '+= 60']

        while not self.stop_threads:
            if (time.time() - start_time) >= self.max_time or self.sent_requests >= self.max_requests:
                self.stop_threads = True
                break
            
            pixel = random.choice(list_pixel)
            
            # Cuộn từng chút một
            # Cuộn từng chút một
            for _ in range(10):  # Cuộn 10 lần cho mỗi lần thực hiện
                self.driver.execute_script(f"arguments[0].scrollTop {pixel}")  # Cuộn 10 pixel mỗi lần
                time.sleep(random.uniform(0.05, 0.1))  # Thời gian chờ ngẫu nhiên giữa 50ms đến 100ms
                self.send_result(account_id, f"Cuộn {pixel} pixel", cookie)

            time.sleep(random.uniform(3, 10)) 
        
        sleep(60)
        self.even_follow == True
        

    def maint_add_Friend(self, name_group, account_id, cookie):
        start_time = time.time()
        scroll_thread = threading.Thread(target=self.scroll_friends, args=(start_time,name_group, account_id, cookie))
        scroll_thread.start()
        sleep(5)
        # Khởi tạo luồng thêm bạn bè
        add_friend_thread = threading.Thread(target=self.click_addFriend, args=(start_time, account_id, cookie))
        add_friend_thread.start()
        
        scroll_thread.join()
        add_friend_thread.join()
        
        
                
    def add_friend_with_threads(self, account):
        account_id = account['user']
        cookie = account['cookie']
        name_group = account['group']

        # Khởi tạo thời gian bắt đầu và mở session
        open_session_thread = threading.Thread(target=self.open_session, args=(name_group, account_id, cookie))
        open_session_thread.join()
        
        
        sleep(5)  # Đảm bảo session mở trước khi lướt bạn bè
        
        while True:
            if self.even_follow == True and self.even_open_driver == True:
                add_Friend = threading.Thread(target=self.maint_add_Friend, args=(name_group, account_id, cookie))
                add_Friend.start()

                open_session_thread.start()
                
                # Chờ các luồng hoàn thành
                add_Friend.join()
                self.even_follow == False
            elif self.even_newFeed == True and self.even_open_driver == True:
                surf_newfeed = threading.Thread(target=self.surf_newFeed, args=(name_group, account_id, cookie))
                surf_newfeed.start()
                surf_newfeed.join()
                self.even_Newfeed == False
                

        # Reset lại trạng thái cho lần tiếp theo
        self.sent_requests = 0
        self.stop_threads = False


            
    
    def process_account(self,command, account):
        if command == "login_cookie":
            self.process_facebook_login(account)
        elif command == "open_account":
            self.open_session('via', account.get('user', 'unknown'), account.get('cookie', 'unknown'))
        elif command == 'run_interaction':
            self.add_friend_with_threads(account)
            # print(account)
    def main(self):
        input_data = json.loads(sys.argv[1])
        command = sys.argv[2]
        if command == 'run_interaction':
            input_data = input_data["accounts"]
        # print(input_data["accounts"][0]['uid'])
        threads = []
        
        for i, account in enumerate(input_data):
            if command == 'run_interaction':
                self.send_log(f"Bắt đầu xử lý tài khoản: {account['user']}")
                # command = account['command']
            else:
                self.send_log(f"Bắt đầu xử lý tài khoản: {account.get('uid', 'unknown')}")
                # command = account.get("command", "login_cookie")
            thread = threading.Thread(target=partial(self.process_account, command, account))
            thread.daemon = True  # Đảm bảo thread sẽ kết thúc khi chương trình chính kết thúc
            threads.append(thread)
            thread.start()

        # Chờ tất cả các luồng hoàn thành
        for thread in threads:
            thread.join(timeout=300)  # Timeout 5 phút
        
        
        

if __name__ == "__main__":
    Facebook().main()