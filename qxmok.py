import pandas as pd
import jieba
import re
import pymysql
import html
import emoji
from bs4 import BeautifulSoup
import opencc
import pypinyin

# 配置
csv_path = 'shuju/all.csv'
text_col = "评论内容"             # 需要分词的列名
stopwords_path = "stopwords.txt"  # 停用词文件（每行一个词）
encoding = "utf-8-sig"

# MySQL配置
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'pl_data',
    'charset': 'utf8mb4'
}
table_name = 'pinglunshuju'  # 表名              

def load_stopwords(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            sw = {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        # 创建默认停用词
        sw = {
            "的", "了", "啊", "哦", "嗯", "呢", "吧", "呀", "吗", "呢",
            "是", "有", "在", "和", "就", "都", "而", "及", "与", "着",
            "或", "一个", "没有", "我们", "你们", "他们", "它们", "这个",
            "那个", "这些", "那些", "自己", "什么", "怎么", "这样", "那样",
            "因为", "所以", "如果", "虽然", "但是", "而且", "因此", "然后",
            "不过", "还是", "只是", "只有", "已经", "现在", "这里", "那里",
            "时候", "时候", "事情", "东西", "问题", "情况", "方面", "方面",
            "可以", "可能", "应该", "需要", "必须", "一定", "非常", "特别",
            "比较", "相对", "比较", "相对", "一样", "一样", "不同", "一样",
            "时候", "时候", "时候", "时候", "地方", "地方", "地方", "地方"
        }
    # 可选：添加常见符号
    sw.update({" ", "\n", "\t"})
    return sw

# 繁简转换器
converter = opencc.OpenCC('t2s')

def clean_text(text):
    """高级文本清洗"""
    if not isinstance(text, str):
        return ""

    # 1. HTML解码
    text = html.unescape(text)

    # 2. 去除HTML标签
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()

    # 3. 去除表情符号
    text = emoji.replace_emoji(text, replace='')

    # 4. 去除特殊字符和多余空白
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：""''（）【】《》]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # 5. 广告过滤关键词
    ad_keywords = [
        '广告', '推广', '淘宝', '天猫', '京东', '拼多多', '微信', '支付宝',
        '优惠券', '红包', '返现', '佣金', '代理', '招商', '合作', '联系',
        '加微信', '加群', '私信', '咨询', '购买', '下单', '链接', '二维码'
    ]

    for keyword in ad_keywords:
        if keyword in text:
            return ""  # 过滤掉包含广告关键词的评论

    return text

def normalize_text(text):
    """文本规范化"""
    if not isinstance(text, str) or not text:
        return ""

    # 1. 繁体转简体
    text = converter.convert(text)

    # 2. 拼音转汉字（简单处理，实际需要更复杂的逻辑）
    # 这里可以集成更复杂的拼音转换工具
    # 暂时跳过，需要专门的拼音转汉字库

    # 3. 简单错别字纠正（示例）
    corrections = {
        '不愧是': '不愧是',
        '价高质优': '价高质优',
        # 可以添加更多常见错别字
    }

    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)

    return text

def create_mysql_table(cursor):
    """创建MySQL表"""
    # 先删除表重新创建（如果存在）
    cursor.execute("DROP TABLE IF EXISTS pinglunshuju")

    create_table_sql = """
    CREATE TABLE pinglunshuju (
        id INT AUTO_INCREMENT PRIMARY KEY,
        商品名称 VARCHAR(500),
        用户名 VARCHAR(500),
        评论内容 TEXT,
        评论时间 VARCHAR(500),
        评论评分 VARCHAR(50),
        点赞数 INT DEFAULT 0,
        回复数 INT DEFAULT 0,
        商品颜色 VARCHAR(500),
        商品版本 VARCHAR(500),
        清洗后内容 TEXT,
        分词结果 TEXT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """
    cursor.execute(create_table_sql)

def insert_to_mysql(df, cursor):
    """批量插入数据到MySQL"""
    insert_sql = """
    INSERT INTO pinglunshuju (
        商品名称, 用户名, 评论内容, 评论时间, 评论评分, 点赞数, 回复数,
        商品颜色, 商品版本,清洗后内容, 分词结果
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = []
    for _, row in df.iterrows():
        # 处理NaN值和空值
        def safe_get(col, default=''):
            val = row.get(col, default)
            if pd.isna(val) or val == 'nan':
                return default
            return str(val)

        def safe_get_int(col, default=0):
            val = row.get(col, default)
            if pd.isna(val) or val == 'nan' or val == '':
                return default
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return default

        data.append((
            safe_get('商品名称'),
            safe_get('用户名'),
            safe_get('评论内容'),
            safe_get('评论时间'),
            safe_get('评论评分'),
            safe_get_int('点赞数'),
            safe_get_int('回复数'),
            safe_get('商品颜色'),
            safe_get('商品版本'),
            safe_get('清洗后内容'),
            safe_get('分词结果')
        ))

    cursor.executemany(insert_sql, data)

def clean_tokens(tokens, stopwords):
    cleaned = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        # 只保留中文、英文、数字（按需调整）
        if not re.match(r"^[\u4e00-\u9fa5a-zA-Z0-9]+$", tok):
            continue
        if tok in stopwords:
            continue
        # 过滤长度过短的词
        if len(tok) <= 1:
            continue
        cleaned.append(tok)
    return cleaned

def main():
    # 连接MySQL数据库（先连接到mysql数据库创建目标数据库）
    try:
        # 先连接到默认数据库创建目标数据库
        temp_config = mysql_config.copy()
        temp_config['database'] = 'mysql'  # 连接到系统数据库
        conn = pymysql.connect(**temp_config)
        cursor = conn.cursor()

        # 创建目标数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS pl_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()

        # 重新连接到目标数据库
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()
        print("MySQL数据库连接成功")
    except Exception as e:
        print(f"MySQL连接失败: {e}")
        return

    try:
        # 创建表
        create_mysql_table(cursor)
        print("数据表创建/检查完成")

        # 读取数据
        df = pd.read_csv(csv_path, encoding=encoding)
        print(f"读取到 {len(df)} 条评论数据")

        # 加载停用词
        stopwords = load_stopwords(stopwords_path)
        print(f"加载停用词 {len(stopwords)} 个")

        # 数据清洗和规范化
        print("开始数据清洗...")
        df["清洗后内容"] = df[text_col].apply(lambda x: normalize_text(clean_text(str(x))))

        # 过滤掉空评论（清洗后内容为空或原始内容为空/NaN）
        df = df[df["清洗后内容"].str.len() > 0]
        df = df[df[text_col].notna() & (df[text_col] != '')]
        print(f"清洗后剩余 {len(df)} 条有效评论")

        # 去重
        print("去重...")
        before_count = len(df)
        df = df.drop_duplicates(subset=["清洗后内容"], keep='first')
        after_count = len(df)
        print(f"去重后剩余 {after_count} 条评论（删除了 {before_count - after_count} 条重复评论）")

        # 中文分词和去停用词
        print("开始中文分词...")
        def process_text(text):
            tokens = jieba.cut(text)
            cleaned_tokens = clean_tokens(tokens, stopwords)
            return cleaned_tokens

        df["tokens"] = df["清洗后内容"].apply(process_text)
        df["分词结果"] = df["tokens"].apply(lambda xs: " ".join(xs))

        # 保存本地CSV
        out_path = "G:\guidian\pachong\shujumokuai\shuju\qingxijieguo.csv"
        df.to_csv(out_path, index=False, encoding=encoding)
        print(f"本地文件已保存: {out_path}")

        # 存入MySQL数据库
        print("开始存入MySQL数据库...")
        insert_to_mysql(df, cursor)
        conn.commit()
        print(f"成功存入 {len(df)} 条数据到MySQL数据库")

    except Exception as e:
        print(f"处理过程中出错: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        print("MySQL连接已关闭")

if __name__ == "__main__":
    main()