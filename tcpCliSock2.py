# -*- coding: utf-8 -*-
import socket
import threading
import sys


def recv_msg(client_socket):
    """监听服务器消息的线程函数"""
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                raise ConnectionResetError("与服务器断开连接")
            # 清空输入行并打印消息（优化用户体验）
            print(f"\n{data}\n> 你：", end="", flush=True)
        except Exception as e:
            print(f"\n 与服务器连接异常：{e}")
            client_socket.close()
            sys.exit(1)


def main():
    # 配置服务器地址
    HOST = input("请输入服务器IP地址：")  # 如192.168.1.105或localhost
    PORT = 21567
    ADDR = (HOST, PORT)

    # 创建TCP套接字
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(ADDR)
        print("已成功连接服务器")
    except Exception as e:
        print(f"连接服务器失败：{e}")
        return

    # 输入客户端昵称
    nickname = input("请输入你的昵称：")
    client_socket.send(nickname.encode('utf-8'))
    print(" 操作说明：直接输入消息为广播，输入@昵称:消息为定向发送，输入quit退出")

    # 启动接收消息线程
    recv_thread = threading.Thread(target=recv_msg, args=(client_socket,), daemon=True)
    recv_thread.start()

    # 主线程负责发送消息
    while True:
        msg = input("> 你：")
        if msg.lower() == 'quit':
            client_socket.close()
            print("已退出聊天")
            sys.exit(0)
        if msg:
            client_socket.send(msg.encode('utf-8'))


if __name__ == "__main__":
    main()