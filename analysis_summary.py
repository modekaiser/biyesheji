#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情感分析结果总结脚本
"""

import os
import pandas as pd
from collections import Counter
import json

def _pick_col(df, *candidates):
    """从多个候选列名中选择一个存在的（兼容中英表头）"""
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"找不到列：{candidates}，当前列为：{list(df.columns)}")

def main():
    print("生成情感分析总结报告...")

    # 读取分析结果
    # 使用脚本所在目录的上一级作为项目根目录，避免工作目录不同导致路径错误
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result_file = os.path.join(base_dir, "qingganjieguo.csv")
    df = pd.read_csv(result_file, encoding="utf-8")

    print(f"读取了 {len(df)} 条分析结果")

    col_label = _pick_col(df, '情感标签', 'sentiment_label')
    col_score = _pick_col(df, '情感得分', 'sentiment_score')
    col_words = _pick_col(df, '情感词详情', 'sentiment_words')

    # 1. 整体情感分布
    print("\n" + "="*50)
    print("整体情感分布")
    print("="*50)

    sentiment_dist = df[col_label].value_counts()
    for label, count in sentiment_dist.items():
        percentage = (count / len(df)) * 100
        print(f"{label}: {count} ({percentage:.1f}%)")

    # 2. 情感得分统计
    print("\n" + "="*50)
    print("情感得分统计")
    print("="*50)

    score_stats = df[col_score].describe()
    print(f"平均得分: {score_stats['mean']:.3f}")
    print(f"最高得分: {score_stats['max']:.3f}")
    print(f"最低得分: {score_stats['min']:.3f}")
    print(f"中位数: {score_stats['50%']:.3f}")

    # 3. 产品情感分析TOP10
    print("\n" + "="*50)
    print("产品情感分析 TOP10 (正面)")
    print("="*50)

    product_sentiment = df.groupby('产品名')[col_score].agg(['mean', 'count']).round(3)
    product_sentiment = product_sentiment[product_sentiment['count'] >= 5]  # 只显示评论数>=5的产品
    top_positive = product_sentiment.nlargest(10, 'mean')
    for product, row in top_positive.iterrows():
        print(f"{product}: {row['mean']:.3f} (评论数: {row['count']})")

    print("\n" + "="*50)
    print("产品情感分析 TOP10 (负面)")
    print("="*50)

    top_negative = product_sentiment.nsmallest(10, 'mean')
    for product, row in top_negative.iterrows():
        print(f"{product}: {row['mean']:.3f} (评论数: {row['count']})")

    # 4. 最常出现的情感词
    print("\n" + "="*50)
    print("最常出现的情感词 TOP20")
    print("="*50)

    all_words = []
    for _, row in df.iterrows():
        if pd.notna(row.get(col_words)):
            try:
                words_data = eval(row[col_words])
                for word_info in words_data:
                    all_words.append(word_info['word'])
            except:
                continue

    word_counts = Counter(all_words)
    print("正面情感词:")
    positive_words = [(word, count) for word, count in word_counts.most_common(20) if get_word_sentiment(word) > 0]
    for word, count in positive_words[:10]:
        print(f"  {word}: {count}")

    print("\n负面情感词:")
    negative_words = [(word, count) for word, count in word_counts.most_common(20) if get_word_sentiment(word) < 0]
    for word, count in negative_words[:10]:
        print(f"  {word}: {count}")

    # 5. 评论评分与情感得分的关系
    print("\n" + "="*50)
    print("评论评分与情感得分关系")
    print("="*50)

    rating_sentiment = df.groupby('评论评分')[col_score].agg(['mean', 'count']).round(3)
    for rating, row in rating_sentiment.iterrows():
        print(f"{rating}星: {row['mean']:.3f} (评论数: {row['count']})")

    # 6. 生成JSON摘要
    summary = {
        "total_reviews": len(df),
        "sentiment_distribution": sentiment_dist.to_dict(),
        "score_statistics": {
            "mean": score_stats['mean'],
            "max": score_stats['max'],
            "min": score_stats['min'],
            "median": score_stats['50%']
        },
        "top_products_positive": top_positive.head(5).to_dict('index'),
        "top_products_negative": top_negative.head(5).to_dict('index'),
        "top_positive_words": dict(positive_words[:5]),
        "top_negative_words": dict(negative_words[:5]),
        "rating_sentiment_correlation": rating_sentiment.to_dict('index')
    }

    with open('sentiment_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "="*50)
    print("分析完成！")
    print("="*50)
    print(f"详细结果已保存至: qingganjieguo.csv")
    print(f"分析摘要已保存至: sentiment_summary.json")

def get_word_sentiment(word):
    """简单的情感词判断（用于统计）"""
    positive_words = {'不错', '很好', '满意', '棒', '牛', '给力', '流畅', '清晰', '漂亮', '强大'}
    negative_words = {'差', '不好', '垃圾', '坑', '卡顿', '慢', '热', '贵', '失望', '后悔'}

    if word in positive_words:
        return 1
    elif word in negative_words:
        return -1
    else:
        return 0

if __name__ == "__main__":
    main()
