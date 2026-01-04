from graphviz import Digraph

# 字体路径预留（请在此处填写你的字体文件路径，例如："C:/Windows/Fonts/simhei.ttf" 或 "/System/Library/Fonts/PingFang.ttc"）
FONT_PATH = ""

# 创建有向图对象
dot = Digraph(name="TCP_Socket_Communication", format="png")  # format指定输出格式（png/svg等）

# 全局节点样式配置（统一设置字体）
dot.node_attr.update(
    shape="rect", 
    style="filled", 
    fillcolor="lightblue",
    fontname=FONT_PATH if FONT_PATH else "sans-serif",  # 字体路径为空时使用默认字体
    fontsize="10"
)

# 全局边样式配置
dot.edge_attr.update(
    fontname=FONT_PATH if FONT_PATH else "sans-serif",
    fontsize="9"
)

# 1. 添加服务器端节点
dot.node("S1", "服务器端：创建套接字（socket()）")
dot.node("S2", "绑定IP和端口（bind()）")
dot.node("S3", "监听连接（listen()）")
dot.node("S4", "等待并接受客户端连接（accept()）")
dot.node("S5", "多线程处理客户端消息（recv()/send()）")
dot.node("S6", "关闭套接字（close()）")

# 2. 添加客户端节点
dot.node("C1", "客户端：创建套接字（socket()）")
dot.node("C2", "连接服务器（connect()）")
dot.node("C3", "发送/接收消息（send()/recv()）")
dot.node("C4", "关闭套接字（close()）")

# 3. 绘制各端内部流程（实线）- 修正：使用元组列表格式
dot.edges([("S1", "S2"), ("S2", "S3"), ("S3", "S4"), ("S4", "S5"), ("S5", "S6")])
dot.edges([("C1", "C2"), ("C2", "C3"), ("C3", "C4")])

# 4. 绘制两端交互关系（虚线+标签）
dot.edge("C2", "S4", style="dashed", label="发起连接请求")
dot.edge("S5", "C3", style="dashed", label="消息交互")
dot.edge("C3", "S5", style="dashed")  # 补充双向交互的反向边

# 生成流程图文件（会在脚本运行目录生成 "TCP_Socket_Communication.png"）
dot.render(filename="TCP_Socket_Communication", view=False)  # view=True 会自动打开生成的图片

print("流程图已生成完成！文件名为：TCP_Socket_Communication.png")