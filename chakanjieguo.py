import pandas as pd

# 读取清洗后的文件
df = pd.read_csv('shuju\qingxijieguo.csv', encoding='utf-8-sig')
print('总行数:', len(df))
print('列名:', df.columns.tolist())

print('\n前3行评论内容:')
for i, content in enumerate(df['评论内容'].head(3), 1):
    print(f"{i}. {content[:100]}...")

print('\n前3行清洗后内容:')
for i, content in enumerate(df['清洗后内容'].head(3), 1):
    print(f"{i}. {content[:100]}...")

print('\n前3行分词文本:')
for i, content in enumerate(df['分词结果'].head(3), 1):
    print(f"{i}. {content[:100]}...")