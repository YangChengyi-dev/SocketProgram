# -*- coding: utf-8 -*-
import socket
import threading
import sys
import os
import base64

send_jobs = {}
accepted_paths = {}
pending_offers = {}

def recv_msg(client_socket):
    """监听服务器消息的线程函数"""
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                raise ConnectionResetError("与服务器断开连接")
            if data.startswith("IMGREQ|"):
                try:
                    _, sender, filename, size_str = data.split('|', 3)
                    pending_offers[(sender, filename)] = int(size_str)
                    print(f"\n收到来自 {sender} 的图片请求：{filename}（{size_str} 字节）。输入 /accept {sender} {filename} 保存路径 或 /reject {sender} {filename}\n> 你：", end="", flush=True)
                except:
                    print(f"\n图片请求解析失败\n> 你：", end="", flush=True)
            elif data.startswith("IMGOK|"):
                try:
                    _, peer, filename = data.split('|', 2)
                    job = send_jobs.get((peer, filename))
                    if job:
                        b64 = job["b64"]
                        chunk_size = job["chunk_size"]
                        total = job["total"]
                        for i in range(total):
                            chunk = b64[i*chunk_size:(i+1)*chunk_size]
                            payload = f"IMG|@{peer}|{filename}|{i+1}|{total}|{chunk}"
                            client_socket.send(payload.encode('utf-8'))
                        del send_jobs[(peer, filename)]
                        print(f"\n对方已接受，图片已发送：{filename}\n> 你：", end="", flush=True)
                except Exception as e:
                    print(f"\n图片发送失败：{e}\n> 你：", end="", flush=True)
            elif data.startswith("IMGNO|"):
                try:
                    _, peer, filename = data.split('|', 2)
                    if (peer, filename) in send_jobs:
                        del send_jobs[(peer, filename)]
                    print(f"\n对方拒绝接收图片：{filename}\n> 你：", end="", flush=True)
                except:
                    print(f"\n图片拒收通知解析失败\n> 你：", end="", flush=True)
            elif data.startswith("IMG|"):
                try:
                    parts = data.split('|', 5)
                    _, sender, filename, seq_str, total_str, chunk = parts
                    seq = int(seq_str)
                    total = int(total_str)
                    key = (sender, filename)
                    if key not in accepted_paths:
                        continue
                    if not hasattr(recv_msg, "img_buffers"):
                        recv_msg.img_buffers = {}
                    buf = recv_msg.img_buffers.get(key)
                    if buf is None:
                        buf = {"total": total, "chunks": {}}
                        recv_msg.img_buffers[key] = buf
                    buf["chunks"][seq] = chunk
                    if len(buf["chunks"]) == buf["total"]:
                        ordered = "".join(buf["chunks"][i] for i in range(1, buf["total"] + 1))
                        data_bytes = base64.b64decode(ordered.encode('ascii'))
                        save_path = accepted_paths.get(key)
                        if not save_path:
                            del recv_msg.img_buffers[key]
                            continue
                        out_path = save_path
                        if out_path.endswith(os.sep) or os.path.isdir(out_path):
                            try:
                                os.makedirs(out_path, exist_ok=True)
                            except:
                                pass
                            out_path = os.path.join(out_path, filename)
                        else:
                            parent = os.path.dirname(out_path) or os.getcwd()
                            try:
                                os.makedirs(parent, exist_ok=True)
                            except:
                                pass
                        if os.path.exists(out_path):
                            base = os.path.splitext(out_path)[0]
                            ext = os.path.splitext(out_path)[1]
                            i = 1
                            while os.path.exists(out_path):
                                out_path = f"{base}_{i}{ext}"
                                i += 1
                        with open(out_path, "wb") as f:
                            f.write(data_bytes)
                        del recv_msg.img_buffers[key]
                        print(f"\n来自 {sender} 的图片已保存：{out_path}\n> 你：", end="", flush=True)
                    else:
                        pass
                except Exception as e:
                    print(f"\n图片处理异常：{e}\n> 你：", end="", flush=True)
            else:
                print(f"\n{data}\n> 你：", end="", flush=True)
        except Exception as e:
            print(f"\n 与服务器连接异常：{e}")
            client_socket.close()
            sys.exit(1)


def main():
    # 配置服务器地址
    HOST = input("请输入服务器IP地址：")
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
    print(" 操作说明：广播直接输入；@昵称:消息定向；/img @昵称 文件路径 发起图片请求；/accept 发送者 文件名 保存路径 接受图片；/reject 发送者 文件名 拒收；/list在线列表；/nick 新昵称改名；/help帮助；quit或/quit退出")

    # 启动接收消息线程
    recv_thread = threading.Thread(target=recv_msg, args=(client_socket,), daemon=True)
    recv_thread.start()

    # 主线程负责发送消息
    try:
        while True:
            msg = input("> 你：")
            if msg.lower() in ('quit', '/quit'):
                client_socket.close()
                print("已退出聊天")
                sys.exit(0)
            if msg.strip() == '/help':
                print("命令：/list 查看在线用户；/nick 新昵称 修改昵称；/quit 退出；@昵称:消息 定向消息；/img @昵称 文件路径 发起图片请求；/accept 发送者 文件名 保存路径；/reject 发送者 文件名")
                continue
            if msg.startswith('/img '):
                try:
                    parts = msg.split(' ', 2)
                    if len(parts) < 3 or not parts[1].startswith('@'):
                        print("用法：/img @昵称 文件路径")
                        continue
                    target = parts[1][1:]
                    path = parts[2].strip('"').strip("'")
                    if not os.path.isfile(path):
                        print("文件不存在")
                        continue
                    filename = os.path.basename(path)
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode('ascii')
                    chunk_size = 4096
                    total = (len(b64) + chunk_size - 1) // chunk_size
                    send_jobs[(target, filename)] = {"b64": b64, "chunk_size": chunk_size, "total": total}
                    size_bytes = os.path.getsize(path)
                    payload = f"IMGREQ|@{target}|{filename}|{size_bytes}"
                    client_socket.send(payload.encode('utf-8'))
                    print(f"已发起图片请求：{filename}")
                    continue
                except Exception as e:
                    print(f"发送图片失败：{e}")
                    continue
            if msg.startswith('/accept '):
                parts = msg.split(' ', 3)
                if len(parts) < 4:
                    print("用法：/accept 发送者 文件名 保存路径")
                    continue
                sender = parts[1]
                filename = parts[2]
                save_path = parts[3].strip('"').strip("'")
                if (sender, filename) not in pending_offers:
                    print("未找到该图片请求")
                    continue
                accepted_paths[(sender, filename)] = save_path
                client_socket.send(f"IMGOK|@{sender}|{filename}".encode('utf-8'))
                print(f"已接受来自 {sender} 的图片：{filename}，保存到：{save_path}")
                continue
            if msg.startswith('/reject '):
                parts = msg.split(' ', 3)
                if len(parts) < 3:
                    print("用法：/reject 发送者 文件名")
                    continue
                sender = parts[1]
                filename = parts[2]
                if (sender, filename) in pending_offers:
                    del pending_offers[(sender, filename)]
                client_socket.send(f"IMGNO|@{sender}|{filename}".encode('utf-8'))
                print(f"已拒绝来自 {sender} 的图片：{filename}")
                continue
            if msg:
                client_socket.send(msg.encode('utf-8'))
    except KeyboardInterrupt:
        client_socket.close()
        print("已退出聊天")
        sys.exit(0)


if __name__ == "__main__":
    main()
