#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PySpark WordCount 程序

这是一个经典的Spark应用示例。
功能：
1. 读取输入文本文件
2. 分割文本为单词
3. 统计每个单词的出现次数
4. 输出结果到指定目录
"""

from pyspark.sql import SparkSession
import sys
import os


def wordcount_rdd(spark, input_path, output_path):
    """
    使用RDD API实现WordCount
    
    Args:
        spark: SparkSession对象
        input_path: 输入文件路径
        output_path: 输出结果路径
    """
    print("\n" + "="*60)
    print("方法1：使用RDD API实现WordCount")
    print("="*60)
    
    sc = spark.sparkContext
    
    # 读取输入文件
    text_rdd = sc.textFile(input_path)
    
    # 分割单词并转换为小写
    words = text_rdd.flatMap(lambda line: line.split())
    words_lower = words.map(lambda word: word.lower())
    
    # 过滤空字符串和特殊符号
    words_clean = words_lower.filter(lambda word: word and len(word) > 0)
    
    # 创建(word, 1)的键值对
    word_pairs = words_clean.map(lambda word: (word, 1))
    
    # 按键聚合，计算每个单词的出现次数
    word_counts = word_pairs.reduceByKey(lambda a, b: a + b)
    
    # 按出现次数降序排序
    sorted_counts = word_counts.sortByKey(ascending=False) \
                               .sortBy(lambda x: x[1], ascending=False)
    
    # 显示前20个高频词
    print("\n【Top 20 高频词汇】")
    print("-"*60)
    print(f"{'单词':<20} {'出现次数':<15}")
    print("-"*60)
    
    top_20 = sorted_counts.take(20)
    for word, count in top_20:
        print(f"{word:<20} {count:<15}")
    
    # 保存结果到output目录
    output_dir = output_path
    # 删除已存在的输出目录
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    
    sorted_counts.saveAsTextFile(output_dir)
    print(f"\n✓ 结果已保存到: {output_dir}")
    
    # 统计总单词数和不同单词数
    total_words = words_clean.count()
    unique_words = word_counts.count()
    
    print(f"\n【统计信息】")
    print("-"*60)
    print(f"总单词数（计重复）: {total_words:,}")
    print(f"不同单词数: {unique_words:,}")
    print(f"平均词频: {total_words / unique_words:.2f}")
    
    return sorted_counts


def wordcount_dataframe(spark, input_path, output_path):
    """
    使用DataFrame和SQL实现WordCount
    
    Args:
        spark: SparkSession对象
        input_path: 输入文件路径
        output_path: 输出结果路径
    """
    print("\n" + "="*60)
    print("方法2：使用DataFrame和SQL实现WordCount")
    print("="*60)
    
    # 读取文本文件
    df = spark.read.text(input_path)
    
    # 导入必要的函数
    from pyspark.sql.functions import split, explode, lower, col, count
    
    # 分割单词
    words_df = df.select(explode(split(col("value"), " ")).alias("word"))
    
    # 转换为小写并过滤
    words_df = words_df.filter(col("word") != "").filter(col("word") != "")
    words_df = words_df.select(lower(col("word")).alias("word"))
    
    # 统计词频
    word_counts_df = words_df.groupBy("word").count().alias("count")
    
    # 按count降序排序
    sorted_df = word_counts_df.sort(col("count").desc())
    
    # 显示前20个高频词
    print("\n【Top 20 高频词汇】")
    print("-"*60)
    print(f"{'单词':<20} {'出现次数':<15}")
    print("-"*60)
    
    sorted_df.limit(20).collect()
    for row in sorted_df.limit(20).collect():
        print(f"{row['word']:<20} {row['count']:<15}")
    
    # 保存结果（Parquet格式）
    output_parquet = output_path + "_df"
    if os.path.exists(output_parquet):
        import shutil
        shutil.rmtree(output_parquet)
    
    sorted_df.write.mode("overwrite").parquet(output_parquet)
    print(f"\n✓ 结果已保存到: {output_parquet}")
    
    # 统计信息
    total_words = words_df.count()
    unique_words = word_counts_df.count()
    
    print(f"\n【统计信息】")
    print("-"*60)
    print(f"总单词数（计重复）: {total_words:,}")
    print(f"不同单词数: {unique_words:,}")
    print(f"平均词频: {total_words / unique_words:.2f}")
    
    return sorted_df


def main():
    """主函数"""
    # 创建SparkSession
    spark = SparkSession.builder \
        .appName("WordCount") \
        .master("local[*]") \
        .getOrCreate()
    
    # 获取脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义输入和输出路径
    input_file = os.path.join(script_dir, "input", "sample.txt")
    output_rdd = os.path.join(script_dir, "output", "wordcount_rdd")
    output_df = os.path.join(script_dir, "output", "wordcount_df_parquet")
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 输入文件 {input_file} 不存在")
        spark.stop()
        sys.exit(1)
    
    print("\n" + "="*60)
    print("PySpark WordCount 示例程序")
    print("="*60)
    print(f"输入文件: {input_file}")
    print(f"输出目录: {os.path.dirname(output_rdd)}")
    
    # 运行RDD版本的WordCount
    wordcount_rdd(spark, input_file, output_rdd)
    
    # 运行DataFrame版本的WordCount
    wordcount_dataframe(spark, input_file, output_df)
    
    print("\n" + "="*60)
    print("WordCount 程序执行完成！")
    print("="*60)
    
    spark.stop()


if __name__ == "__main__":
    main()
