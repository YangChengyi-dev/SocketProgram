# -*- coding: utf-8 -*-
import requests
import time

# ########## 关键修改：替换成你的服务器IP ##########
SERVER_IP = "192.168.43.9"  # 比如你的服务器IP是这个，替换成自己的！
DOWNLOAD_URL = f"http://{SERVER_IP}:8080/download_digital_goods"  # 下载地址
LOGS_URL = f"http://{SERVER_IP}:8080/get_logs"  # 日志地址

# 模拟100次下载（相当于100个用户买数字商品）
def simulate_digital_purchases(count=100):
    print(f"开始模拟{count}次数字商品下载...")
    for i in range(count):
        try:
            # 发送下载请求
            response = requests.get(DOWNLOAD_URL, timeout=30)
            if response.status_code == 200:
                print(f"第{i+1}次下载成功")
            else:
                print(f"第{i+1}次下载失败，状态码：{response.status_code}")
            time.sleep(0.5)  # 每次间隔0.5秒，避免服务器太忙
        except Exception as e:
            print(f"第{i+1}次下载报错：{e}")
            time.sleep(0.5)

# 模拟完成后，导出日志到CSV文件
def export_logs():
    try:
        # 从服务器获取所有下载日志
        logs_response = requests.get(LOGS_URL)
        if logs_response.status_code == 200:
            logs = logs_response.json()
            # 保存到CSV文件（和shopping_logistics.csv在同一个文件夹）
            with open("http_digital_logs.csv", "w", encoding="utf-8") as f:
                # 写表头
                f.write("status,delay,file_size_mb,timestamp,error\n")
                for log in logs:
                    error = log.get("error", "")  # 没有错误就填空
                    # 写数据
                    f.write(f"{log['status']},{log['delay']:.3f},{log['file_size_mb']:.2f},{log['timestamp']},{error}\n")
            print("✅ HTTP数字分发日志已保存到 http_digital_logs.csv")
        else:
            print("❌ 获取日志失败")
    except Exception as e:
        print(f"❌ 导出日志报错：{e}")

if __name__ == '__main__':
    simulate_digital_purchases(100)  # 模拟100次下载
    export_logs()  # 导出日志