import pandas as pd

# 读取原始文件
df_raw = pd.read_csv('shuju/all.csv', encoding='utf-8-sig')
print('原始文件列名:', df_raw.columns.tolist())
print('原始文件总行数:', len(df_raw))
print()

print('原始文件前3行:')
for i in range(3):
    row = df_raw.iloc[i]
    print(f'行{i+1}:')
    print(f'  评论内容: {row["评论内容"]}')
    print(f'  评论时间: {row["评论时间"]}')
    print()

# 检查是否有格式问题
print('各列的非空值数量:')
print(df_raw.count())
print()

print('评论内容列的类型:', type(df_raw['评论内容'].iloc[0]))
print('评论内容列前3个值:')
for i, val in enumerate(df_raw['评论内容'].head(3)):
    print(f'{i+1}. {repr(val)}')

