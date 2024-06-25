import sys
import requests

def get_ip_location(ip_address):
    api_url = f"https://api.iplocation.net/?ip={ip_address}"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        location_info = {
            "ip_address": data.get("ip"),
            "country_name": data.get("country_name"),
            "country_code": data.get("country_code2"),
            "isp": data.get("isp")
        }
        return location_info
    else:
        return None

if len(sys.argv) < 2:
    print("Vui lòng nhập địa chỉ IP cần kiểm tra vị trí!")
    sys.exit()

ip_address = sys.argv[1]

location = get_ip_location(ip_address)

if location:
    print("- IP Address:", ip_address)
    print("- Quốc gia:", location.get("country_name"))
    print("- Mã quốc gia:", location.get("country_code"))
    print("- Nhà cung cấp dịch vụ Internet (ISP):", location.get("isp"))
else:
    print("- Không thể lấy thông tin vị trí cho IP Address:", ip_address)