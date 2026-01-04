# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np

# 1. 读取两个CSV文件的数据
try:
    # 读取HTTP数字分发数据
    http_df = pd.read_csv("http_digital_logs.csv")
    # 读取网购实体分发数据
    shopping_df = pd.read_csv("shopping_logistics.csv", encoding="utf-8")
    print("✅ 数据读取成功！")
except Exception as e:
    print(f"❌ 读取数据失败：{e}")
    print("请确保两个CSV文件在同一个文件夹，且文件名正确：shopping_logistics.csv、http_digital_logs.csv")
    exit()

# ---------------------- 计算HTTP数字分发的核心指标 ----------------------
# 平均延迟（秒）：从请求到下载开始的时间（数字分发速度）
http_success_df = http_df[http_df["status"] == "success"]
http_avg_delay = http_success_df["delay"].mean()  # 平均耗时
# 成功率（%）：成功下载的次数 ÷ 总次数
http_success_rate = (http_df["status"] == "success").sum() / len(http_df) * 100
# 单份成本（元）：数字分发一次制作，无限下载，成本≈0
http_cost_per_unit = 0.0
# 吞吐量（次/分钟）：每分钟能处理多少下载请求（数字分发效率）
http_total_time = http_df["delay"].sum() / 60  # 总耗时（分钟）
http_throughput = len(http_df) / http_total_time  # 吞吐量

# ---------------------- 计算网购实体分发的核心指标 ----------------------
# 先转换时间格式，计算物流耗时（小时）：送达时间 - 下单时间
shopping_df["下单时间"] = pd.to_datetime(shopping_df["下单时间"])
shopping_df["送达时间"] = pd.to_datetime(shopping_df["送达时间"])
shopping_df["物流耗时_小时"] = (shopping_df["送达时间"] - shopping_df["下单时间"]).dt.total_seconds() / 3600

# 平均物流耗时（小时）：实体分发速度
shopping_success_df = shopping_df[shopping_df["是否送达成功"] == "是"]
shopping_avg_delay = shopping_success_df["物流耗时_小时"].mean()
# 成功率（%）：成功送达的订单 ÷ 总订单
shopping_success_rate = (shopping_df["是否送达成功"] == "是").sum() / len(shopping_df) * 100
# 单份成本（元）：平均运费（实体分发的核心成本）
shopping_cost_per_unit = shopping_df["运费（元）"].mean()
# 吞吐量（单/天）：每天能处理多少个实体订单（和数字分发的“分钟”区分）
shopping_time_range = (shopping_df["送达时间"].max() - shopping_df["下单时间"].min()).total_seconds() / 86400  # 总时间（天）
shopping_throughput = len(shopping_df) / shopping_time_range

# ---------------------- 打印对比结果（控制台查看） ----------------------
print("\n" + "="*60)
print("📊 HTTP数字分发 vs 网购实体分发 核心指标对比")
print("="*60)
print(f"{'指标':<18}{'HTTP数字分发':<22}{'网购实体分发':<22}")
print(f"{'平均延迟':<18}{http_avg_delay:.3f} 秒{'':<8}{shopping_avg_delay:.1f} 小时")
print(f"{'成功率':<18}{http_success_rate:.1f}%{'':<13}{shopping_success_rate:.1f}%")
print(f"{'单份成本':<18}{http_cost_per_unit:.2f} 元{'':<13}{shopping_cost_per_unit:.2f} 元")
print(f"{'吞吐量':<18}{http_throughput:.1f} 次/分钟{'':<5}{shopping_throughput:.1f} 单/天")
print("="*60)

# ---------------------- 保存对比结果到Excel（实验报告用） ----------------------
comparison_data = {
    "指标": [
        "平均延迟（单位）", "平均延迟",
        "成功率（%）",
        "单份成本（元）",
        "吞吐量（单位）", "吞吐量"
    ],
    "HTTP数字分发": [
        "秒", f"{http_avg_delay:.3f}",
        f"{http_success_rate:.1f}",
        f"{http_cost_per_unit:.2f}",
        "次/分钟", f"{http_throughput:.1f}"
    ],
    "网购实体分发": [
        "小时", f"{shopping_avg_delay:.1f}",
        f"{shopping_success_rate:.1f}",
        f"{shopping_cost_per_unit:.2f}",
        "单/天", f"{shopping_throughput:.1f}"
    ]
}
comparison_df = pd.DataFrame(comparison_data)
comparison_df.to_excel("分发对比结果.xlsx", index=False)
print("\n✅ 对比结果已保存到：分发对比结果.xlsx（可直接用于实验报告）")

# ---------------------- 生成可视化图表（实验报告必备） ----------------------
try:
    import matplotlib.pyplot as plt
    # 设置中文字体（避免中文乱码）
    plt.rcParams['font.sans-serif'] = ['SimHei']  # Windows用黑体
    # plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac用这个，注释掉上面的Windows字体
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

    # 图1：平均延迟对比图（秒级 vs 小时级，直观显示速度差异）
    plt.figure(figsize=(12, 6))
    labels = ['HTTP数字分发', '网购实体分发']
    # 把实体延迟转换成秒，方便对比（小时×3600）
    delays_seconds = [http_avg_delay, shopping_avg_delay * 3600]
    colors = ['#2E86AB', '#A23B72']

    bars = plt.bar(labels, delays_seconds, color=colors, alpha=0.8, edgecolor='black', linewidth=1)
    plt.title('平均延迟对比（单位：秒）', fontsize=16, fontweight='bold', pad=20)
    plt.ylabel('延迟（秒）', fontsize=14)
    plt.grid(axis='y', alpha=0.3, linestyle='--')

    # 在柱子上标注具体数值
    for bar, delay in zip(bars, delays_seconds):
        height = bar.get_height()
        if delay < 10:
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{delay:.3f}秒',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
        else:
            plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01, f'{delay:.0f}秒',
                    ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig('平均延迟对比图.png', dpi=300, bbox_inches='tight')
    print("✅ 图表1已保存：平均延迟对比图.png")

    # 图2：成功率与单份成本对比（双生子图，左右并排，无兼容性问题）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))  # 1行2列的子图

    # 左子图：成功率对比（柱状图）
    success_rates = [http_success_rate, shopping_success_rate]
    color1 = '#F18F01'
    ax1.bar(labels, success_rates, color=color1, alpha=0.8, edgecolor='black', linewidth=1)
    ax1.set_title('成功率对比', fontsize=16, fontweight='bold', pad=20)
    ax1.set_ylabel('成功率（%）', fontsize=14)
    ax1.set_ylim(95, 101)  # 限定y轴范围，更直观
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    # 标注成功率数值
    for i, rate in enumerate(success_rates):
        ax1.text(i, rate + 0.1, f'{rate:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

    # 右子图：单份成本对比（柱状图）
    costs = [http_cost_per_unit, shopping_cost_per_unit]
    color2 = '#C73E1D'
    ax2.bar(labels, costs, color=color2, alpha=0.8, edgecolor='black', linewidth=1)
    ax2.set_title('单份成本对比', fontsize=16, fontweight='bold', pad=20)
    ax2.set_ylabel('单份成本（元）', fontsize=14)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    # 标注成本数值
    for i, cost in enumerate(costs):
        ax2.text(i, cost + 0.3, f'{cost:.2f}元', ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig('成功率与成本对比图.png', dpi=300, bbox_inches='tight')
    print("✅ 图表2已保存：成功率与成本对比图.png")

except Exception as e:
    print(f"❌ 生成图表失败：{e}")
    print("请确认已安装matplotlib：pip install matplotlib")