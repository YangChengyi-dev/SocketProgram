# -*- coding: utf-8 -*-
import socket
import threading
import sys

# 客户端连接池：键为客户端昵称，值为(套接字, 地址)
client_pool = {}
# 线程锁，保证多线程操作client_pool的安全性
lock = threading.Lock()


def handle_client(client_socket, client_addr):
    """处理单个客户端的消息交互"""
    try:
        # 接收客户端的昵称
        nickname = client_socket.recv(1024).decode('utf-8')
        with lock:
            if nickname in client_pool:
                try:
                    client_socket.send("昵称已占用，请更换".encode('utf-8'))
                finally:
                    client_socket.close()
                return
            client_pool[nickname] = (client_socket, client_addr)
        print(f"客户端 {nickname}（{client_addr}）已连接，当前在线人数：{len(client_pool)}")

        # 广播新用户上线消息
        broadcast(f"{nickname} 加入了聊天", exclude_nickname=None)

        while True:
            # 接收客户端消息
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                raise ConnectionResetError("客户端主动断开连接")

            # 解析消息：@指定用户:内容 或 广播内容
            if data.startswith('/'):
                cmd = data.strip()
                if cmd == '/list':
                    with lock:
                        users = ", ".join(sorted(client_pool.keys()))
                    send_to_nick(nickname, f"在线用户：{users}" if users else "暂无在线用户")
                elif cmd.startswith('/nick '):
                    new_nick = cmd[6:].strip()
                    if not new_nick:
                        send_to_nick(nickname, "昵称不能为空")
                    else:
                        with lock:
                            if new_nick in client_pool:
                                send_to_nick(nickname, "该昵称已被占用")
                            else:
                                sock_addr = client_pool[nickname]
                                del client_pool[nickname]
                                client_pool[new_nick] = sock_addr
                                broadcast(f"{nickname} 现在叫做 {new_nick}", exclude_nickname=None)
                                nickname = new_nick
                                send_to_nick(nickname, f"昵称已更新为 {nickname}")
                elif cmd == '/nick':
                    send_to_nick(nickname, "用法：/nick 新昵称")
                elif cmd == '/quit':
                    break
                else:
                    send_to_nick(nickname, "未知命令")
            elif data.startswith('IMGREQ|'):
                try:
                    _, target_field, filename, size_str = data.split('|', 3)
                    target_nick = target_field[1:] if target_field.startswith('@') else target_field
                    with lock:
                        if target_nick in client_pool:
                            target_sock, _ = client_pool[target_nick]
                            payload = f"IMGREQ|{nickname}|{filename}|{size_str}"
                            target_sock.send(payload.encode('utf-8'))
                        else:
                            send_to_nick(nickname, f"目标用户 {target_nick} 不存在或已离线")
                except:
                    send_to_nick(nickname, "图片请求格式错误")
            elif data.startswith('IMGOK|'):
                try:
                    _, target_field, filename = data.split('|', 2)
                    target_nick = target_field[1:] if target_field.startswith('@') else target_field
                    with lock:
                        if target_nick in client_pool:
                            target_sock, _ = client_pool[target_nick]
                            payload = f"IMGOK|{nickname}|{filename}"
                            target_sock.send(payload.encode('utf-8'))
                        else:
                            send_to_nick(nickname, f"目标用户 {target_nick} 不存在或已离线")
                except:
                    send_to_nick(nickname, "图片接受通知格式错误")
            elif data.startswith('IMGNO|'):
                try:
                    _, target_field, filename = data.split('|', 2)
                    target_nick = target_field[1:] if target_field.startswith('@') else target_field
                    with lock:
                        if target_nick in client_pool:
                            target_sock, _ = client_pool[target_nick]
                            payload = f"IMGNO|{nickname}|{filename}"
                            target_sock.send(payload.encode('utf-8'))
                        else:
                            send_to_nick(nickname, f"目标用户 {target_nick} 不存在或已离线")
                except:
                    send_to_nick(nickname, "图片拒收通知格式错误")
            elif data.startswith('IMG|'):
                try:
                    parts = data.split('|', 5)
                    _, target_field, filename, seq_str, total_str, chunk = parts
                    target_nick = target_field[1:] if target_field.startswith('@') else target_field
                    with lock:
                        if target_nick in client_pool:
                            target_sock, _ = client_pool[target_nick]
                            payload = f"IMG|{nickname}|{filename}|{seq_str}|{total_str}|{chunk}"
                            target_sock.send(payload.encode('utf-8'))
                        else:
                            send_to_nick(nickname, f"目标用户 {target_nick} 不存在或已离线")
                except:
                    send_to_nick(nickname, "图片消息格式错误")
            elif data.startswith('@'):
                # 定向消息格式：@目标昵称:消息内容
                target_nickname, msg = data.split(':', 1)
                target_nickname = target_nickname[1:]  # 去掉@符号
                send_direct_msg(nickname, target_nickname, msg)
            else:
                # 广播消息
                broadcast(f"[{nickname}] {data}", exclude_nickname=None)

    except Exception as e:
        print(f"客户端 {nickname if 'nickname' in locals() else client_addr} 连接异常：{e}")
    finally:
        # 移除客户端连接并广播下线消息
        if 'nickname' in locals() and nickname in client_pool:
            with lock:
                del client_pool[nickname]
            broadcast(f"{nickname} 离开了聊天", exclude_nickname=None)
            print(f"🔌 客户端 {nickname} 已断开，当前在线人数：{len(client_pool)}")
        client_socket.close()


def broadcast(msg, exclude_nickname=None):
    """广播消息给所有客户端（可排除指定客户端）"""
    with lock:
        # 遍历客户端池，发送消息
        to_remove = []
        for nick, (sock, _) in client_pool.items():
            if nick != exclude_nickname:
                try:
                    sock.send(msg.encode('utf-8'))
                except:
                    to_remove.append(nick)
        for nick in to_remove:
            if nick in client_pool:
                del client_pool[nick]


def send_direct_msg(sender_nick, target_nick, msg):
    """定向发送消息：从发送者到指定接收者"""
    with lock:
        if target_nick in client_pool:
            target_sock, _ = client_pool[target_nick]
            try:
                target_sock.send(f"[{sender_nick}] 悄悄对你说：{msg}".encode('utf-8'))
                # 给发送者反馈
                sender_sock, _ = client_pool[sender_nick]
                sender_sock.send(f"已向{target_nick}发送消息：{msg}".encode('utf-8'))
            except:
                del client_pool[target_nick]
                broadcast(f"目标用户 {target_nick} 已离线", exclude_nickname=sender_nick)
        else:
            # 目标用户不存在
            sender_sock, _ = client_pool[sender_nick]
            sender_sock.send(f"目标用户 {target_nick} 不存在或已离线".encode('utf-8'))


def send_to_nick(nick, msg):
    with lock:
        if nick in client_pool:
            sock, _ = client_pool[nick]
            try:
                sock.send(msg.encode('utf-8'))
            except:
                del client_pool[nick]


def server_input():
    """服务器自身输入消息并发送"""
    print("服务器已启动，可输入消息广播（输入'quit'退出）")
    while True:
        msg = input("> 服务器：")
        if msg.lower() == 'quit':
            # 关闭所有客户端连接
            with lock:
                for sock, _ in client_pool.values():
                    sock.close()
                client_pool.clear()
            print("🔌 服务器已关闭所有连接，即将退出")
            sys.exit(0)
        # 广播服务器消息
        broadcast(f"服务器：{msg}", exclude_nickname=None)


def main():
    # 配置服务器地址
    HOST = '0.0.0.0'  # 监听所有网卡
    PORT = 21567
    ADDR = (HOST, PORT)

    # 创建TCP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 端口复用
    server_socket.bind(ADDR)
    server_socket.listen(5)
    print(f"TCP服务器已启动，监听地址：{HOST}:{PORT}")

    # 启动服务器输入线程
    input_thread = threading.Thread(target=server_input, daemon=True)
    input_thread.start()

    # 循环接受客户端连接
    while True:
        client_socket, client_addr = server_socket.accept()
        # 为每个客户端创建处理线程
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_addr), daemon=True)
        client_thread.start()


if __name__ == "__main__":
    main()
