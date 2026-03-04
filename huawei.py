from DrissionPage import ChromiumPage
import csv
import os

FIELDNAMES = [
    '产品名',
    '用户名',
    '评论内容',
    '评论时间',
    '评论评分',
    '点赞数',
    '回复数',
    '商品颜色',
    '商品版本',
]

csv_path = 'shuju/all.csv'
file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
f = open(csv_path, mode='a', newline='', encoding='UTF-8-sig')#a追加模式，w写入模式
csv_writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
if not file_exists:
    csv_writer.writeheader()
#HUAWEI Mate 70 Pro https://item.jd.com/10125696245302.html HUAWEI Mate 70 pro  https://item.jd.com/10125698057396.html
qci = ChromiumPage()
qci.get('https://item.jd.com/10125698057396.html')
qci.listen.start('client.action')
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
        '产品名': 'HUAWEI',
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
    print(f'正在采集HUAWEI第{page}页的数据内容')
    if page <= 2:
        resp = qci.listen.wait(2)
        json_data = resp[-1].response.body
    else:
        resp = qci.listen.wait()
        json_data = resp.response.body
    # print(json_data)  # 注释掉，避免编码问题
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