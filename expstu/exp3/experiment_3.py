#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
实验三：RDD编程基础 - 简化版 
包括9个部分的实验内容
"""

from pyspark import SparkConf, SparkContext, StorageLevel
import time
import os
import shutil
import re

# 创建SparkContext
conf = SparkConf().setAppName("Experiment3_RDD").setMaster("local[*]")
sc = SparkContext(conf=conf)
sc.setLogLevel("WARN")

# 基础配置
DATA_DIR = "expstu/exp3/data"
OUTPUT_DIR = "expstu/exp3/output"

# 清理旧的输出目录
if os.path.exists(OUTPUT_DIR):
    try:
        shutil.rmtree(OUTPUT_DIR)
    except:
        pass

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("=" * 80)
print("实验三：RDD编程基础")
print("=" * 80)


# ===================== 实验1：RDD的创建与基础数据预处理 =====================
print("\n【实验1】RDD的创建与基础数据预处理")
print("-" * 80)

# 步骤1: 从文件创建RDD
employees_rdd = sc.textFile(f"{DATA_DIR}/employees.txt")
print(f"✓ 已读取employees.txt")

# 步骤3: 查看前几条数据
print("\n原始数据（前5条）：")
for line in employees_rdd.take(5):
    print(f"  {line}")

# 步骤4: 识别脏数据并统计
empty_lines = employees_rdd.filter(lambda line: line.strip() == "")
print(f"\n✓ 原始数据行数: {employees_rdd.count()}")
print(f"✓ 空行数: {empty_lines.count()}")

# 步骤5: 使用filter清洗数据
cleaned_rdd = employees_rdd.filter(lambda line: line.strip() != "")
cleaned_rdd = cleaned_rdd.filter(lambda line: len(line.split(",")) == 3)
print(f"✓ 清洗后数据行数: {cleaned_rdd.count()}")

# 步骤6: 保存清洗后的数据
try:
    cleaned_rdd.saveAsTextFile(f"{OUTPUT_DIR}/employees_cleaned")
    print(f"✓ 清洗后数据已保存到 {OUTPUT_DIR}/employees_cleaned")
except Exception as e:
    print(f"⚠ 保存失败: {e}")


# ===================== 实验2：Transformation和Action算子的区别 =====================
print("\n\n【实验2】Transformation和Action算子的区别")
print("-" * 80)

# 创建基础RDD
rdd_base = sc.parallelize([1, 2, 3, 4, 5])
print("✓ 创建基础RDD: [1, 2, 3, 4, 5]")

# Transformation算子（惰性求值 - 不立即执行）
print("\n应用Transformation算子：")
mapped_rdd = rdd_base.map(lambda x: x * 2)
print("  - map(lambda x: x * 2) - 不会立即执行")

filtered_rdd = mapped_rdd.filter(lambda x: x > 5)
print("  - filter(lambda x: x > 5) - 不会立即执行")

# Action算子（立即执行）
print("\n应用Action算子：")
result = filtered_rdd.collect()
print(f"  - collect(): {result}")
print(f"  ✓ 此时Spark执行所有之前的Transformation操作")

# 多次Action观察是否重复计算
print("\n观察多次Action的执行：")
start = time.time()
result1 = filtered_rdd.count()
time1 = time.time() - start
print(f"  - 第1次count(): {result1} (用时: {time1:.4f}s)")

start = time.time()
result2 = filtered_rdd.count()
time2 = time.time() - start
print(f"  - 第2次count(): {result2} (用时: {time2:.4f}s)")
print(f"✓ 观察结论：每次Action都会重新计算RDD（除非使用了缓存）")


# ===================== 实验3：常用Transformation算子 =====================
print("\n\n【实验3】常用Transformation算子的应用")
print("-" * 80)

# 读取句子文件
sentences_rdd = sc.textFile(f"{DATA_DIR}/sentences.txt")
print(f"✓ 读取sentences.txt，共{sentences_rdd.count()}行")

# 步骤1: 使用flatMap分割单词
words_rdd = sentences_rdd.flatMap(lambda line: line.split(" "))
print(f"✓ 使用flatMap分割单词，共{words_rdd.count()}个单词")

# 步骤2: 使用map转换为小写
lower_rdd = words_rdd.map(lambda word: word.lower())

# 步骤3: 使用filter过滤短单词（长度 >= 3）
filtered_words = lower_rdd.filter(lambda word: len(word) >= 3)
print(f"✓ 过滤后（长度>=3），共{filtered_words.count()}个单词")

# 步骤4: 使用distinct去重
unique_words = filtered_words.distinct()
print(f"✓ 去重后，共{unique_words.count()}个不重复单词")

print(f"\n去重后的部分单词：")
for word in unique_words.take(10):
    print(f"  - {word}")

# union操作示例
rdd1 = sc.parallelize([1, 2, 3])
rdd2 = sc.parallelize([3, 4, 5])
union_result = rdd1.union(rdd2).collect()
print(f"\n✓ union示例: {rdd1.collect()} ∪ {rdd2.collect()} = {union_result}")


# ===================== 实验4：常用Action算子 =====================
print("\n\n【实验4】常用Action算子与结果获取")
print("-" * 80)

# 创建测试RDD
numbers_rdd = sc.parallelize(range(1, 101))

# count - 统计元素个数
count_result = numbers_rdd.count()
print(f"✓ count(): 共{count_result}个元素")

# take - 获取前n个元素
take_result = numbers_rdd.take(5)
print(f"✓ take(5): {take_result}")

# first - 获取第一个元素
first_result = numbers_rdd.first()
print(f"✓ first(): {first_result}")

# reduce - 聚合所有元素
sum_result = numbers_rdd.reduce(lambda a, b: a + b)
print(f"✓ reduce(sum): {sum_result}")

# takeOrdered - 获取最小的n个元素
smallest = numbers_rdd.takeOrdered(5)
print(f"✓ takeOrdered(5): {smallest}")

largest = numbers_rdd.takeOrdered(5, key=lambda x: -x)
print(f"✓ takeOrdered(5, desc): {largest}")


# ===================== 实验5：RDD分区机制 =====================
print("\n\n【实验5】RDD分区机制与自定义分区策略")
print("-" * 80)

# 查看默认分区数
partition_rdd = sc.parallelize(range(1, 101))
print(f"✓ parallelize创建的RDD默认分区数: {partition_rdd.getNumPartitions()}")

# repartition - 增加分区数
repartitioned = partition_rdd.repartition(4)
print(f"✓ repartition(4)后的分区数: {repartitioned.getNumPartitions()}")

# coalesce - 减少分区数
coalesced = repartitioned.coalesce(2)
print(f"✓ coalesce(2)后的分区数: {coalesced.getNumPartitions()}")

# glom - 查看每个分区的内容
print("\n各分区内容（使用coalesce后）：")
for i, partition in enumerate(coalesced.glom().collect()):
    print(f"  分区{i}: 共{len(partition)}个元素，首尾元素: [{partition[0]}, ..., {partition[-1]}]")


# ===================== 实验6：RDD持久化与存储 =====================
print("\n\n【实验6】RDD数据的持久化与分布式存储")
print("-" * 80)

# 创建需要处理的RDD
input_rdd = sc.parallelize(range(1, 11)).map(lambda x: (f"key{x}", x * 10))

# 保存为TextFile
try:
    output_path = f"{OUTPUT_DIR}/rdd_output"
    input_rdd.saveAsTextFile(output_path)
    print(f"✓ 已用saveAsTextFile保存到 {output_path}")
except Exception as e:
    print(f"⚠ 保存失败: {e}")

# 使用不同分区数保存
try:
    output_path_5parts = f"{OUTPUT_DIR}/rdd_output_5parts"
    input_rdd.repartition(5).saveAsTextFile(output_path_5parts)
    print(f"✓ 已用5个分区保存到 {output_path_5parts}")
except Exception as e:
    print(f"⚠ 保存失败: {e}")

# RDD缓存性能对比
print("\nRDD缓存性能对比：")
cache_test_rdd = sc.parallelize(range(1, 100000))

# 不使用缓存
start = time.time()
cache_test_rdd.map(lambda x: x * 2).count()
time_no_cache_1 = time.time() - start

start = time.time()
cache_test_rdd.map(lambda x: x * 2).count()
time_no_cache_2 = time.time() - start
print(f"  不使用缓存 - 第1次: {time_no_cache_1:.4f}s, 第2次: {time_no_cache_2:.4f}s")

# 使用缓存
cache_test_rdd_cached = sc.parallelize(range(1, 100000)).cache()
start = time.time()
cache_test_rdd_cached.map(lambda x: x * 2).count()
time_cache_1 = time.time() - start

start = time.time()
cache_test_rdd_cached.map(lambda x: x * 2).count()
time_cache_2 = time.time() - start
print(f"  使用cache()缓存  - 第1次: {time_cache_1:.4f}s, 第2次: {time_cache_2:.4f}s")
print(f"✓ 缓存说明：cache()将RDD存储在内存中，后续使用时无需重新计算")


# ===================== 实验7：键值对RDD的排序与二次排序 =====================
print("\n\n【实验7】键值对RDD的排序与二次排序技术")
print("-" * 80)

# 读取scores.txt
scores_rdd = sc.textFile(f"{DATA_DIR}/scores.txt")
kv_scores = scores_rdd.map(lambda line: (line.split(",")[0], (line.split(",")[1], int(line.split(",")[2]))))
print(f"✓ 读取scores.txt，共{kv_scores.count()}条记录")

print("\n原始数据（前5条）：")
for student, (subject, score) in kv_scores.take(5):
    print(f"  {student}: {subject} - {score}分")

# sortByKey - 按学生姓名排序
sorted_by_student = kv_scores.sortByKey().collect()
print("\n✓ 按学生姓名排序（sortByKey）：")
for student, (subject, score) in sorted_by_student[:5]:
    print(f"  {student}: {subject} - {score}分")

# sortBy - 按分数降序排序
sorted_by_score = kv_scores.sortBy(lambda x: x[1][1], ascending=False).take(5)
print("\n✓ 按分数降序排序（sortBy）：")
for student, (subject, score) in sorted_by_score:
    print(f"  {student}: {subject} - {score}分")

# 二次排序：先按学生名排序，再按分数降序排序
complex_key_rdd = scores_rdd.map(lambda line: (
    (line.split(",")[0], -int(line.split(",")[2])),  # 复合Key: (学生名, -分数)
    line.split(",")[1]  # Value: 科目
))
secondary_sorted = complex_key_rdd.sortByKey().collect()
print("\n✓ 二次排序（先按学生名，再按分数降序）：")
for (student, neg_score), subject in secondary_sorted[:5]:
    print(f"  {student}: {subject} - {-neg_score}分")


# ===================== 实验8：combineByKey聚合算子 =====================
print("\n\n【实验8】高级聚合算子combineByKey的原理与应用")
print("-" * 80)

# 读取employees.txt并创建key-value RDD
employees_lines = sc.textFile(f"{DATA_DIR}/employees.txt")
# 先清洗数据
employees_cleaned = employees_lines.filter(lambda line: line.strip() != "").filter(lambda line: len(line.split(",")) == 3)
dept_salary = employees_cleaned.map(lambda line: (
    line.split(",")[0],  # 部门ID作为Key
    int(line.split(",")[2])  # 工资作为Value
))
print(f"✓ 读取员工数据，共{dept_salary.count()}条记录")

# 使用combineByKey计算部门统计信息
def create_combiner(salary):
    """第一次遇到某个Key时的初始化"""
    return (1, salary, salary, salary)  # (count, sum, max, min)

def merge_value(acc, salary):
    """在同一分区内合并值"""
    return (acc[0] + 1, acc[1] + salary, max(acc[2], salary), min(acc[3], salary))

def merge_combiners(acc1, acc2):
    """合并不同分区的累计器"""
    return (acc1[0] + acc2[0], acc1[1] + acc2[1], max(acc1[2], acc2[2]), min(acc1[3], acc2[3]))

dept_stats = dept_salary.combineByKey(create_combiner, merge_value, merge_combiners)

print("\n部门统计信息（员工数、工资总和、最高工资、最低工资）：")
print(f"{'部门':<8} {'员工数':<8} {'工资总和':<12} {'平均工资':<12} {'最高工资':<12} {'最低工资':<12}")
print("-" * 70)

for dept_id, (count, total_salary, max_salary, min_salary) in dept_stats.sortByKey().collect():
    avg_salary = total_salary / count
    print(f"{dept_id:<8} {count:<8} {total_salary:<12} {avg_salary:<12.0f} {max_salary:<12} {min_salary:<12}")


# ===================== 实验9：综合练习 =====================
print("\n\n【实验9】综合练习：分布式编程实战")
print("-" * 80)

# 案例1：数据去重与统计
print("\n案例1：数据去重与统计（logs.txt）")
print("-" * 40)

logs_rdd = sc.textFile(f"{DATA_DIR}/logs.txt")
print(f"✓ 原始日志行数: {logs_rdd.count()}")

# 去重
unique_logs = logs_rdd.distinct()
print(f"✓ 去重后日志行数: {unique_logs.count()}")

# 提取日志类型并统计
def extract_log_type(line):
    parts = line.split(",")
    return parts[1] if len(parts) > 1 else "ERROR"

log_types = unique_logs.map(extract_log_type)
log_type_counts = log_types.map(lambda t: (t, 1)).reduceByKey(lambda a, b: a + b)
print("\n日志类型频率排序（前5）：")
for log_type, count in log_type_counts.sortBy(lambda x: x[1], ascending=False).take(5):
    print(f"  {log_type}: {count}次")

# 案例2：WordCount完整实现
print("\n\n案例2：WordCount完整实现（articles.txt）")
print("-" * 40)

articles_rdd = sc.textFile(f"{DATA_DIR}/articles.txt")

# 分词
words = articles_rdd.flatMap(lambda line: line.split())

# 清洗：转小写、去标点
def clean_word(word):
    word = word.lower()
    word = re.sub(r'[^a-z0-9]', '', word)
    return word

cleaned = words.map(clean_word).filter(lambda w: len(w) > 0)

# 停用词过滤
stopwords = {'the', 'is', 'a', 'in', 'and', 'to', 'of', 'for', 'as', 'with', 'or', 'by'}
filtered = cleaned.filter(lambda w: w not in stopwords)

# 统计
word_counts = filtered.map(lambda w: (w, 1)).reduceByKey(lambda a, b: a + b)

print(f"✓ 总词数: {cleaned.count()}")
print(f"✓ 不重复词数: {word_counts.count()}")
print("\n出现频率最高的20个单词：")
top_20 = word_counts.sortBy(lambda x: x[1], ascending=False).take(20)
for word, count in top_20:
    print(f"  {word}: {count}")

# 保存WordCount结果
try:
    word_counts.saveAsTextFile(f"{OUTPUT_DIR}/wordcount_results")
    print(f"\n✓ 结果已保存到 {OUTPUT_DIR}/wordcount_results")
except Exception as e:
    print(f"⚠ 保存失败: {e}")

# 案例3：简单倒排索引
print("\n\n案例3：倒排索引构建（documents.txt）")
print("-" * 40)

docs_rdd = sc.textFile(f"{DATA_DIR}/documents.txt")
print(f"✓ 读取文档数据，共{docs_rdd.count()}条文档")

# 解析文档格式：doc_id,content
def parse_doc(line):
    """将文档解析成(word, doc_id)对"""
    parts = line.split(",", 1)
    if len(parts) > 1:
        doc_id = parts[0]
        content = parts[1]
        return [(word.lower(), doc_id) for word in content.split()]
    return []

doc_words = docs_rdd.flatMap(parse_doc)

# 按单词分组，获取包含该单词的所有文档
inverted_index = doc_words.groupByKey().mapValues(lambda docs: sorted(list(set(docs))))

print("\n倒排索引（部分）：")
for word, docs in inverted_index.take(10):
    print(f"  {word}: {docs}")

# 保存倒排索引
try:
    inverted_index.saveAsTextFile(f"{OUTPUT_DIR}/inverted_index")
    print(f"\n✓ 倒排索引已保存到 {OUTPUT_DIR}/inverted_index")
except Exception as e:
    print(f"⚠ 保存失败: {e}")


# ===================== 总结 =====================
print("\n\n" + "=" * 80)
print("实验三完成!")
print("=" * 80)
print(f"""
已完成的内容：
✓ 实验1: RDD的创建与基础数据预处理
✓ 实验2: Transformation和Action算子的区别
✓ 实验3: 常用Transformation算子的应用
✓ 实验4: 常用Action算子与结果获取
✓ 实验5: RDD分区机制与自定义分区策略
✓ 实验6: RDD数据的持久化与分布式存储
✓ 实验7: 键值对RDD的排序与二次排序技术
✓ 实验8: 高级聚合算子combineByKey的原理与应用
✓ 实验9: 综合练习（数据去重、WordCount、倒排索引）

输出结果保存位置: {OUTPUT_DIR}/
  - employees_cleaned/: 清洗后的员工数据
  - rdd_output/: RDD输出示例
  - rdd_output_5parts/: 多分区RDD输出示例
  - wordcount_results/: 词频统计结果
  - inverted_index/: 倒排索引结果
""")

# 关闭SparkContext
sc.stop()
print("\n✓ SparkContext已关闭")
