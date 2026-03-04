#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPPO和一加手机评论爬虫
从京东商城同时爬取OPPO Find X9 Pro和一加13的用户评论数据
"""

# 导入必要的库
from DrissionPage import ChromiumPage  # 用于控制Chrome浏览器进行自动化操作
import csv  # 用于处理CSV文件读写
import os   # 用于文件系统操作

# 定义CSV文件的字段名（列名）
FIELDNAMES = [
    '产品名',     # 产品名称，如"OPPO Find X9 Pro"或"一加 13"
    '用户名',     # 评论用户的昵称
    '评论内容',   # 用户的评论文字内容
    '评论时间',   # 评论的发布时间
    '评论评分',   # 用户给出的星级评分（1-5星）
    '点赞数',     # 这条评论获得的点赞数量
    '回复数',     # 这条评论的回复数量
    '商品颜色',   # 用户购买的商品颜色
    '商品版本',   # 用户购买的商品规格版本
]

# 设置CSV文件保存路径
csv_path = 'shuju/all.csv'

# 检查CSV文件是否已存在且不为空
file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0

# 以追加模式打开CSV文件
f = open(csv_path, mode='a', newline='', encoding='UTF-8-sig')

# 创建CSV写入器对象
csv_writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

# 如果是第一次创建文件，写入表头
if not file_exists:
    csv_writer.writeheader()

# 商品URL说明：
# OPPO Find X9 Pro: https://item.jd.com/100210407515.html
# 一加 13: https://item.jd.com/100210407515.html 

# 创建浏览器实例
qci = ChromiumPage()

# 打开OPPO Find X9 Pro的京东商品页面
# 注意：这里暂时使用同一个URL，实际使用时需要为不同产品设置不同URL
qci.get('https://item.jd.com/100210407515.html')

# 开始监听网络请求
qci.listen.start('client.action')

# 点击"查看全部评价"按钮
qci.ele('css:.all-btn').click()

def extract_row(item, like_count_page=0, reply_count_page=0):
    cinfo = item.get('commentInfo', {}) or {}
    pinfo = item.get('productInfo', {}) or {}

    # 优先使用页面获取的点赞和回复数，如果为0则使用API数据
    like_count = like_count_page if like_count_page > 0 else (
        cinfo.get('usefulVoteCount')
        or cinfo.get('agreeCount')
        or cinfo.get('praiseCount')
        or cinfo.get('voteCount')
        or 0
    )
    reply_count = reply_count_page if reply_count_page > 0 else (
        cinfo.get('replyCount') or cinfo.get('commentReplyVO') or 0
    )
    if isinstance(reply_count, dict):
        reply_count = reply_count.get('replyCount', 0)

    # 获取商品颜色和版本信息
    product_color = ''
    product_version = ''

    # 优先从productSpecifications字段获取完整规格信息
    product_specifications = cinfo.get('productSpecifications') or ''
    if product_specifications and '已购' in product_specifications:
        # 格式如"已购 黑色 12GB+256GB"，提取颜色和版本
        parts = product_specifications.replace('已购', '').strip().split()
        if len(parts) >= 2:
            product_color = parts[0]
            product_version = ' '.join(parts[1:])

    # 如果上面没有获取到，则尝试从wareAttribute字段获取
    if not product_color or not product_version:
        ware_attribute = cinfo.get('wareAttribute', [])
        if isinstance(ware_attribute, list):
            for attr in ware_attribute:
                if isinstance(attr, dict):
                    if '颜色' in attr:
                        product_color = product_color or attr['颜色']
                    if '型号' in attr:
                        product_version = product_version or attr['型号']

    return {
        '产品名': 'OPPO',
        '用户名': cinfo.get('userNickName') or '',
        '评论内容': cinfo.get('commentData') or '',
        '评论时间': cinfo.get('commentDate') or '',
        '评论评分': cinfo.get('commentScore') or '',
        '点赞数': like_count,
        '回复数': reply_count,
        '商品颜色': product_color,
        '商品版本': product_version,
    }

for page in range(1, 101):
    print(f'正在采集OPPO第{page}页的数据内容')
    if page <= 2:
        resp = qci.listen.wait(2)
        json_data = resp[-1].response.body
    else:
        resp = qci.listen.wait()
        json_data = resp.response.body
    print(json_data)
    data_list = json_data['result']['floors'][2]['data']

    # 获取页面上的点赞和回复数
    try:
        # 获取所有评论卡片的点赞和回复数
        count_elements = qci.eles('css:.jdc-count')
        print(f"找到 {len(count_elements)} 个计数元素")

        # 每条评论有2个计数元素（回复数和点赞数），所以需要成对处理
        count_index = 0
    except Exception as e:
        print(f'获取页面计数元素失败: {e}')
        count_index = 0

    for index in data_list:
        try:
            # 从页面获取点赞和回复数
            like_count_page = 0
            reply_count_page = 0

            if count_index < len(count_elements) - 1:
                try:
                    reply_count_page = int(count_elements[count_index].text.strip()) if count_elements[count_index].text.strip().isdigit() else 0
                    like_count_page = int(count_elements[count_index + 1].text.strip()) if count_elements[count_index + 1].text.strip().isdigit() else 0
                    count_index += 2  # 每条评论消耗2个计数元素
                except:
                    pass

            row = extract_row(index, like_count_page, reply_count_page)
            csv_writer.writerow(row)
            print(row)
        except Exception as e:
            print(f'写入失败: {e}')
            pass
    tab = qci.ele('css:._rateListContainer_1ygkr_45')
    if tab:
        tab.scroll.to_bottom()