#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手机评论情感分析器
整合多种情感词典，专门针对手机领域进行情感分析
"""

import os
import pandas as pd
import re
import math
from collections import defaultdict


class PhoneSentimentAnalyzer:
    """手机评论情感分析器"""

    def __init__(self, dict_path="qinggancidian"):
        self.dict_path = dict_path

        # 基础情感词典
        self.positive_words = set()  # 正面情感词
        self.negative_words = set()  # 负面情感词

        # 程度副词词典
        self.degree_words = {}  # 程度副词及其权重

        # 否定词词典
        self.negation_words = set()

        # 转折词词典
        self.conjunction_words = set()

        # 手机领域专用情感词典
        self.domain_sentiment_words = {}

        # 加载所有词典
        self.load_all_dictionaries()

    def detect_encoding(self, file_path):
        """检测文件编码"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)  # pyright: ignore[reportUndefinedVariable]
                return result['encoding']
        except:
            return 'utf-8'

    def load_file_with_encoding(self, file_path):
        """尝试多种编码加载文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin1']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    return content.split('\n')
            except:
                continue

        print(f"无法读取文件：{file_path}")
        return []

    def load_tsinghua_dict(self):
        """加载清华大学李军中文褒贬义词典"""
        print("加载清华大学词典...")
        try:
            # 正面词典
            pos_files = [
                "清华大学李军中文褒贬义词典/tsinghua_positive_gb.txt",
                "清华大学李军中文褒贬义词典/tsinghua_positive_gb_1.txt"
            ]

            for pos_file in pos_files:
                file_path = os.path.join(self.dict_path, pos_file)
                if os.path.exists(file_path):
                    lines = self.load_file_with_encoding(file_path)
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('//'):
                            self.positive_words.add(line)

            # 负面词典
            neg_file = "清华大学李军中文褒贬义词典/tsinghua.negative.gb.txt"
            file_path = os.path.join(self.dict_path, neg_file)
            if os.path.exists(file_path):
                lines = self.load_file_with_encoding(file_path)
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('//'):
                        self.negative_words.add(line)

        except Exception as e:
            print(f"加载清华大学词典失败：{e}")

    def load_ntusd_dict(self):
        """加载台湾大学NTUSD词典"""
        print("加载NTUSD词典...")
        try:
            # 正面词典
            pos_file = "台湾大学NTUSD简体中文情感词典/NTUSD_positive_simplified.txt"
            file_path = os.path.join(self.dict_path, pos_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word:
                            self.positive_words.add(word)

            # 负面词典
            neg_file = "台湾大学NTUSD简体中文情感词典/NTUSD_negative_simplified.txt"
            file_path = os.path.join(self.dict_path, neg_file)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip()
                        if word:
                            self.negative_words.add(word)

        except Exception as e:
            print(f"加载NTUSD词典失败：{e}")

    def load_negation_dict(self):
        """加载否定词典"""
        print("加载否定词典...")
        try:
            file_path = os.path.join(self.dict_path, "否定词典/否定.txt")
            if os.path.exists(file_path):
                lines = self.load_file_with_encoding(file_path)
                for line in lines:
                    word = line.strip()
                    if word:
                        self.negation_words.add(word)
        except Exception as e:
            print(f"加载否定词典失败：{e}")

    def load_conjunction_dict(self):
        """加载转折词典"""
        print("加载转折词典...")
        try:
            file_path = os.path.join(self.dict_path, "turnPointDict.txt")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().split('\t')[0]
                        if word:
                            self.conjunction_words.add(word)
        except Exception as e:
            print(f"加载转折词典失败：{e}")

    def load_hownet_dict(self):
        """加载知网Hownet词典"""
        print("加载知网Hownet词典...")
        try:
            # 正面情感词
            pos_file = "知网Hownet情感词典/正面情感词语（中文）.txt"
            file_path = os.path.join(self.dict_path, pos_file)
            if os.path.exists(file_path):
                lines = self.load_file_with_encoding(file_path)
                for line in lines:
                    line = line.strip()
                    if line and '\t' in line:
                        word = line.split('\t')[0].strip()
                        if word and len(word) > 1:  # 过滤单个字符
                            self.positive_words.add(word)

            # 负面情感词
            neg_file = "知网Hownet情感词典/负面情感词语（中文）.txt"
            file_path = os.path.join(self.dict_path, neg_file)
            if os.path.exists(file_path):
                lines = self.load_file_with_encoding(file_path)
                for line in lines:
                    line = line.strip()
                    if line and '\t' in line:
                        word = line.split('\t')[0].strip()
                        if word and len(word) > 1:  # 过滤单个字符
                            self.negative_words.add(word)

        except Exception as e:
            print(f"加载Hownet词典失败：{e}")

    def define_domain_sentiment_words(self):
        """定义手机领域专用情感词典"""
        print("定义手机领域情感词典...")

        # 手机正面情感词
        positive_domain = {
            # 性能相关
            "续航给力": 0.9, "电池持久": 0.8, "充电快": 0.9, "充电速度快": 0.9,
            "运行流畅": 0.9, "不卡顿": 0.8, "速度快": 0.7, "性能强": 0.8,
            "信号强": 0.8, "信号好": 0.7, "网络稳定": 0.7,

            # 拍照相关
            "拍照清晰": 0.9, "拍照好": 0.8, "像素高": 0.7, "自拍美": 0.8,
            "夜景清晰": 0.8, "镜头牛": 0.7, "摄影强大": 0.8,

            # 外观设计
            "外观漂亮": 0.8, "颜值高": 0.8, "手感佳": 0.7, "轻薄": 0.6,
            "握持舒适": 0.7, "屏占比高": 0.6, "边框窄": 0.6,

            # 系统体验
            "系统流畅": 0.8, "界面美观": 0.6, "功能强大": 0.7, "操作简单": 0.6,
            "生态完善": 0.7, "应用丰富": 0.6,

            # 品牌口碑
            "性价比高": 0.9, "值得买": 0.8, "物超所值": 0.9, "完美": 0.8,
            "杠杠的": 0.7, "顺溜": 0.7, "不错": 0.6, "很好": 0.7,
            "满意": 0.8, "赞": 0.6, "给力": 0.7, "牛逼": 0.9,
            "超出预期": 0.8, "惊喜": 0.7, "太棒了": 0.9, "无敌": 0.8,
            "强大": 0.7, "稳定": 0.6, "耐用": 0.7, "旗舰机": 0.6,
            "高端": 0.6, "智能": 0.5, "创新": 0.6
        }

        # 手机负面情感词
        negative_domain = {
            # 性能问题
            "发热严重": -0.9, "发烫": -0.7, "电池短": -0.8, "续航差": -0.8,
            "充电慢": -0.9, "运行卡顿": -0.9, "死机": -0.8, "崩溃": -0.8,
            "信号差": -0.8, "信号弱": -0.7, "网络不稳": -0.7, "掉线": -0.6,

            # 拍照问题
            "拍照模糊": -0.9, "拍照差": -0.8, "像素低": -0.7, "自拍丑": -0.8,
            "夜景差": -0.8, "镜头渣": -0.7, "成像差": -0.8,

            # 外观设计问题
            "外观丑": -0.8, "颜值低": -0.8, "手感差": -0.7, "过重": -0.6,
            "握持不适": -0.7, "屏占比低": -0.6, "边框宽": -0.6,

            # 系统体验问题
            "系统卡": -0.8, "界面丑": -0.6, "功能少": -0.7, "操作复杂": -0.6,
            "bug多": -0.8, "适配差": -0.7,

            # 品牌口碑问题
            "性价比低": -0.9, "不值得": -0.8, "坑": -0.9, "垃圾": -0.9,
            "差": -0.7, "不好": -0.7, "失望": -0.9, "后悔": -0.8,
            "投诉": -0.8, "返修": -0.7, "问题多": -0.8, "不稳定": -0.7,
            "耗电快": -0.8, "卡": -0.6, "慢": -0.6, "贵": -0.5,
            "智商税": -0.9, "华而不实": -0.8, "缩水": -0.7, "掉价": -0.6,
            "不划算": -0.7, "翻车": -0.8, "拉垮": -0.7
        }

        self.domain_sentiment_words = {**positive_domain, **negative_domain}

    def load_degree_words(self):
        """加载程度副词词典"""
        print("加载程度副词词典...")
        # 极高程度（权重2.0）
        extreme_degree = {
            "极其", "极为", "非常", "特别", "尤其", "太", "最", "超级", "牛逼", 
            "无比", "绝对", "完全", "十足", "彻头彻尾", "彻彻底底","登峰造极",
            "极度", "极端", "至极", "无以复加", "无与伦比"
        }

        # 高程度（权重1.5）
        high_degree = {
            "很", "挺", "相当", "颇为", "比较", "较为", "相对", "稍稍",
            "蛮", "真", "好", "够", "更加", "越发", "愈发"
        }

        # 中等程度（权重1.2）
        medium_degree = {
            "有点", "稍微", "略微", "微微", "稍", "不大", "不很", "不怎么"
        }

        # 低程度（权重0.8）
        low_degree = {
            "一般", "普通", "稍微", "略", "基本", "差不多", "还好"
        }

        for word in extreme_degree:
            self.degree_words[word] = 2.0
        for word in high_degree:
            self.degree_words[word] = 1.5
        for word in medium_degree:
            self.degree_words[word] = 1.2
        for word in low_degree:
            self.degree_words[word] = 0.8

    def load_all_dictionaries(self):
        """加载所有情感词典"""
        print("开始加载情感词典...")

        # 加载基础词典
        self.load_tsinghua_dict()
        self.load_ntusd_dict()
        self.load_hownet_dict()
        self.load_negation_dict()
        self.load_conjunction_dict()

        # 定义领域词典
        self.define_domain_sentiment_words()

        # 加载程度词
        self.load_degree_words()

        print(f"\n词典加载完成统计:")
        print(f"  正面词：{len(self.positive_words)}")
        print(f"  负面词：{len(self.negative_words)}")
        print(f"  程度词：{len(self.degree_words)}")
        print(f"  否定词：{len(self.negation_words)}")
        print(f"  转折词：{len(self.conjunction_words)}")
        print(f"  领域词：{len(self.domain_sentiment_words)}")
        print(f"  总词数：{len(self.positive_words) + len(self.negative_words) + len(self.domain_sentiment_words)}")

    def get_word_sentiment(self, word):
        """获取词语的情感值"""
        # 优先检查领域情感词
        if word in self.domain_sentiment_words:
            return self.domain_sentiment_words[word]

        # 检查通用正面词典
        if word in self.positive_words:
            return 1.0

        # 检查通用负面词典
        if word in self.negative_words:
            return -1.0

        return 0.0

    def calculate_modifiers(self, tokens, sentiment_pos):
        """
        计算修饰词对情感词的影响

        Args:
            tokens: 分词列表
            sentiment_pos: 情感词位置

        Returns:
            float: 修饰后的情感权重
        """
        modifier_score = 1.0
        negation_count = 0
        degree_score = 1.0

        # 检查前面的修饰词（范围：前3个词）
        start_pos = max(0, sentiment_pos - 3)

        for i in range(start_pos, sentiment_pos):
            token = tokens[i]

            # 否定词
            if token in self.negation_words:
                negation_count += 1

            # 程度副词
            elif token in self.degree_words:
                degree_score *= self.degree_words[token]

            # 转折词（转折词会减弱情感）
            elif token in self.conjunction_words:
                degree_score *= 0.7

        # 否定词处理：奇数个否定词取反，偶数个不变
        if negation_count % 2 == 1:
            modifier_score *= -1

        # 应用程度副词
        modifier_score *= degree_score

        return modifier_score

    def analyze_sentiment(self, text, tokens=None):
        """
        分析文本情感倾向

        Args:
            text: 原始文本
            tokens: 分词结果列表

        Returns:
            dict: 情感分析结果
        """
        if tokens is None:
            # 如果没有分词结果，使用简单分词
            tokens = self.simple_tokenize(text)

        # 初始化情感值
        sentiment_score = 0.0
        positive_score = 0.0
        negative_score = 0.0

        # 记录情感词位置和详细信息
        sentiment_words = []

        # 分析每个词
        for i, token in enumerate(tokens):
            # 检查是否为情感词
            word_sentiment = self.get_word_sentiment(token)

            if word_sentiment != 0:
                # 计算修饰词的影响
                modifier_score = self.calculate_modifiers(tokens, i)

                # 计算总情感值
                final_score = word_sentiment * modifier_score
                sentiment_score += final_score

                if final_score > 0:
                    positive_score += final_score
                else:
                    negative_score += abs(final_score)

                # 记录详细信息
                sentiment_words.append({
                    'word': token,
                    'position': i,
                    'base_score': word_sentiment,
                    'modifier_score': modifier_score,
                    'final_score': final_score,
                    'is_domain': token in self.domain_sentiment_words
                })

        # 计算情感倾向
        if sentiment_score > 0.1:
            sentiment_label = "正面"
        elif sentiment_score < -0.1:
            sentiment_label = "负面"
        else:
            sentiment_label = "中性"

        # 计算情感强度
        sentiment_intensity = abs(sentiment_score)

        return {
            'sentiment_score': round(sentiment_score, 3),
            'positive_score': round(positive_score, 3),
            'negative_score': round(negative_score, 3),
            'sentiment_label': sentiment_label,
            'sentiment_intensity': round(sentiment_intensity, 3),
            'sentiment_words': sentiment_words,
            'word_count': len(tokens)
        }

    def simple_tokenize(self, text):
        """简单分词（如果没有分词结果）"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        # 按空格和中文字符分割
        tokens = []
        current_token = ""
        for char in text:
            if char.isspace():
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            elif ord(char) > 127:  # 中文字符
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
                tokens.append(char)
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        return tokens

    def analyze_csv_file(self, csv_path, output_path=None, batch_size=1000):
        """
        分析CSV文件中的评论数据

        Args:
            csv_path: 输入CSV文件路径
            output_path: 输出CSV文件路径（可选）
            batch_size: 批处理大小

        Returns:
            pd.DataFrame: 分析结果
        """
        print(f"\n开始读取CSV文件：{csv_path}")

        # 读取CSV文件
        df = pd.read_csv(csv_path, encoding='utf-8')

        print(f"共读取 {len(df)} 条评论数据")

        # 情感分析结果列
        sentiment_results = []

        # 分批处理
        total_batches = (len(df) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min((batch_idx + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]

            print(f"处理批次 {batch_idx + 1}/{total_batches} ({start_idx}-{end_idx})")

            # 对每条评论进行分析
            for idx, row in batch_df.iterrows():
                if (idx + 1) % 500 == 0:
                    print(f"  已处理 {idx + 1}/{len(df)} 条评论")

                # 获取评论内容
                content = str(row.get('清洗后内容', ''))
                if not content or content == 'nan':
                    content = str(row.get('评论内容', ''))

                # 获取分词结果
                tokens_str = str(row.get('分词结果', ''))
                if tokens_str and tokens_str != 'nan':
                    tokens = tokens_str.split()
                else:
                    tokens = self.simple_tokenize(content)

                # 进行情感分析
                sentiment_result = self.analyze_sentiment(content, tokens)

                # 添加原数据
                result = {
                    '产品名': row.get('产品名', ''),
                    '用户名': row.get('用户名', ''),
                    '评论内容': row.get('评论内容', ''),
                    '评论时间': row.get('评论时间', ''),
                    '评论评分': row.get('评论评分', ''),
                    '点赞数': row.get('点赞数', 0),
                    '回复数': row.get('回复数', 0),
                    '商品颜色': row.get('商品颜色', ''),
                    '商品版本': row.get('商品版本', ''),
                    '清洗后内容': content,
                    **sentiment_result
                }

                sentiment_results.append(result)

        # 转换为DataFrame
        result_df = pd.DataFrame(sentiment_results)

        # 保存结果
        if output_path:
            # 输出CSV要求中文表头：仅在写出文件时重命名，避免影响后续统计代码使用原字段
            cn_col_map = {
                'sentiment_score': '情感得分',
                'positive_score': '正面得分',
                'negative_score': '负面得分',
                'sentiment_label': '情感标签',
                'sentiment_intensity': '情感强度',
                'sentiment_words': '情感词详情',
                'word_count': '词语数量',
            }
            result_df.rename(columns=cn_col_map).to_csv(output_path, index=False, encoding='utf-8-sig')
            print(f"\n分析结果已保存到：{output_path}")

        return result_df

    def generate_statistics(self, result_df):
        """生成情感分析统计报告"""
        print("\n" + "="*60)
        print("手机评论情感分析统计报告")
        print("="*60)

        # 基本统计
        total_reviews = len(result_df)
        print(f"\n总评论数：{total_reviews}")

        # 情感分布
        sentiment_counts = result_df['sentiment_label'].value_counts()
        print("\n情感分布：")
        for label, count in sentiment_counts.items():
            percentage = (count / total_reviews) * 100
            print(f"  {label}: {count} ({percentage:.1f}%)")

        # 平均情感得分
        avg_score = result_df['sentiment_score'].mean()
        print(f"\n平均情感得分：{avg_score:.3f}")

        # 情感强度统计
        intensity_stats = result_df['sentiment_intensity'].describe()
        print("\n情感强度统计：")
        print(f"  平均强度：{intensity_stats['mean']:.3f}")
        print(f"  最大强度：{intensity_stats['max']:.3f}")
        print(f"  最小强度：{intensity_stats['min']:.3f}")

        # 产品分析
        if '产品名' in result_df.columns:
            product_stats = result_df.groupby('产品名').agg({
                'sentiment_score': ['mean', 'count'],
                'sentiment_intensity': 'mean'
            }).round(3)
            product_stats.columns = ['avg_sentiment', 'review_count', 'avg_intensity']
            product_stats = product_stats.sort_values('avg_sentiment', ascending=False)

            print("\n各产品情感分析：")
            print(product_stats)

        # 领域情感词统计
        domain_words_found = []
        for _, row in result_df.iterrows():
            if 'sentiment_words' in row and row['sentiment_words']:
                for word_info in row['sentiment_words']:
                    if word_info.get('is_domain', False):
                        domain_words_found.append(word_info['word'])

        if domain_words_found:
            from collections import Counter
            domain_word_counts = Counter(domain_words_found)
            print("\n最常见的领域情感词：")
            for word, count in domain_word_counts.most_common(20):
                sentiment = "正面" if self.get_word_sentiment(word) > 0 else "负面"
                print(f"  {word} ({sentiment}): {count} 次")

        return {
            'total_reviews': total_reviews,
            'sentiment_distribution': sentiment_counts.to_dict(),
            'avg_sentiment_score': avg_score,
            'intensity_stats': intensity_stats.to_dict(),
            'domain_words': dict(domain_word_counts.most_common(20)) if domain_words_found else {}
        }


def main():
    """主函数"""
    print("手机评论情感分析系统启动...")

    # 创建情感分析器
    analyzer = PhoneSentimentAnalyzer()

    # 分析CSV文件
    input_file = "shuju/qingxijieguo.csv"
    output_file = "qingganjieguo.csv"

    # 执行情感分析
    result_df = analyzer.analyze_csv_file(input_file, output_file)

    # 生成统计报告
    stats = analyzer.generate_statistics(result_df)

    print(f"\n分析完成！结果已保存至：{output_file}")
    print("统计报告生成完毕。")


if __name__ == "__main__":
    main()
