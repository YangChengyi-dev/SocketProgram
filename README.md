# Socket 聊天室项目说明

## 概述
- 本项目实现了一个基于 TCP 的多人聊天室，支持广播、定向私聊、在线列表、昵称更改、帮助提示与图片点对点发送。
- 重点功能为 Socket 编程的聊天室，不涉及 HTTP 分发或数据分析。

## 目录结构
- tcpSerSock.py：TCP 聊天服务器
- tcpCliSock1.py / tcpCliSock2.py / tcpCliSock3.py：TCP 聊天客户端示例

## 环境依赖
- 纯标准库，无第三方依赖（socket、threading、sys、os、base64）

## TCP 聊天使用
1. 启动服务器
```bash
python tcpSerSock.py
```
2. 启动客户端（任选其一或多个）
```bash
python tcpCliSock1.py
```
3. 客户端命令
- 广播：直接输入消息
- 私聊：@对方昵称:消息
- 查看在线：/list
- 修改昵称：/nick 新昵称
- 帮助：/help
- 退出：quit 或 /quit
- 发送图片：/img @对方昵称 文件路径
  - 示例：/img @Alice d:\pictures\cat.png
  - 接收端自动保存到项目目录下的 received_images

## 注意事项
- 局域网通信需开放 21567（TCP）端口
- 图片发送采用 Base64 分片通过文本通道传输，适合中小图片；如需更高效可升级为二进制协议或专用文件服务
