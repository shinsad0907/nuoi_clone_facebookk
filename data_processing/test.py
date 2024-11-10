from selenium import webdriver
import time

# Đường dẫn đến thư mục lưu trữ profile
chrome_profile_path = r"E:\shinsad\tool nuoi facebook\chrome_"

# Tạo Chrome WebDriver với profile được chỉ định
def open_facebook_with_chrome_profile():
    # Cấu hình để sử dụng profile đã lưu
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"user-data-dir={chrome_profile_path}")

    # Khởi tạo WebDriver với cấu hình đã định
    driver = webdriver.Chrome(options=chrome_options)

    # Mở Facebook
    driver.get("https://www.facebook.com")

    # Đợi để kiểm tra xem đã đăng nhập chưa
    time.sleep(10)  # Chờ 10 giây để bạn có thể kiểm tra

    driver.quit()

# Gọi hàm để mở trình duyệt với profile đã lưu
open_facebook_with_chrome_profile()
