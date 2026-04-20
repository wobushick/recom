#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
蒙特卡洛方法求Pi的Spark实现示例

原理：
1. 在正方形[0,1] x [0,1]内生成随机点
2. 统计这些点中落在单位圆(半径=1)内的点数
3. 圆内点数 / 总点数 ≈ (π/4) / 1
4. 因此 π ≈ 4 * (圆内点数 / 总点数)

示例图解：
正方形面积 = 1
圆形面积 = π/4
比例 = 圆形面积 / 正方形面积 = π/4

"""

from pyspark.sql import SparkSession
import random
import math


def estimate_pi_monte_carlo(num_samples):
    """
    使用蒙特卡洛方法估算π（单机版）
    
    Args:
        num_samples: 采样点数
        
    Returns:
        估算的π值
    """
    count_inside_circle = 0
    
    for _ in range(num_samples):
        x = random.random()
        y = random.random()
        
        # 计算点到原点的距离
        distance = math.sqrt(x * x + y * y)
        
        # 如果距离 <= 1，说明点在单位圆内
        if distance <= 1:
            count_inside_circle += 1
    
    # π ≈ 4 * (圆内点数 / 总点数)
    pi_estimate = 4 * count_inside_circle / num_samples
    return pi_estimate


def estimate_pi_spark(spark, num_samples, num_partitions=4):
    """
    使用Spark RDD并行计算蒙特卡洛π估算
    
    Args:
        spark: SparkSession对象
        num_samples: 总采样数
        num_partitions: 分区数
        
    Returns:
        估算的π值
    """
    sc = spark.sparkContext
    
    # 创建分区信息：每个分区需要计算的样本数
    samples_per_partition = num_samples // num_partitions
    
    # 创建RDD，每个分区执行蒙特卡洛采样
    def monte_carlo_in_partition(partition_id):
        """在单个分区内执行蒙特卡洛采样"""
        random.seed(partition_id)  # 设置不同的随机种子以获得不同的随机数
        count_inside = 0
        
        for _ in range(samples_per_partition):
            x = random.random()
            y = random.random()
            
            if x * x + y * y <= 1:
                count_inside += 1
        
        return count_inside
    
    # 为每个分区创建一个元素，然后并行执行蒙特卡洛采样
    rdd = sc.parallelize(range(num_partitions), num_partitions)
    
    # 对每个分区应用蒙特卡洛采样函数
    counts = rdd.map(monte_carlo_in_partition).collect()
    
    # 汇总结果
    total_inside_circle = sum(counts)
    pi_estimate = 4 * total_inside_circle / num_samples
    
    return pi_estimate


def main():
    """主函数"""
    print("=" * 60)
    print("蒙特卡洛方法求π - Spark实现示例")
    print("=" * 60)
    
    # 创建SparkSession
    spark = SparkSession.builder \
        .appName("Monte Carlo Pi Estimation") \
        .master("local[*]") \
        .getOrCreate()
    
    print("\n1. 单机版本测试（10,000个样本）")
    print("-" * 60)
    num_samples = 10000
    pi_single = estimate_pi_monte_carlo(num_samples)
    print(f"   估算的π值: {pi_single:.6f}")
    print(f"   实际π值:   {math.pi:.6f}")
    print(f"   误差:      {abs(pi_single - math.pi):.6f}")
    
    print("\n2. Spark分布式版本测试（1,000,000个样本）")
    print("-" * 60)
    num_samples = 1_000_000
    num_partitions = 4
    pi_spark = estimate_pi_spark(spark, num_samples, num_partitions)
    print(f"   采样点数:   {num_samples:,}")
    print(f"   分区数:     {num_partitions}")
    print(f"   估算的π值:  {pi_spark:.6f}")
    print(f"   实际π值:    {math.pi:.6f}")
    print(f"   误差:       {abs(pi_spark - math.pi):.6f}")
    print(f"   准确度:     {100 * (1 - abs(pi_spark - math.pi) / math.pi):.2f}%")
    
    print("\n3. 不同采样数对精度的影响")
    print("-" * 60)
    sample_sizes = [100_000, 500_000, 1_000_000, 5_000_000]
    
    for size in sample_sizes:
        pi_est = estimate_pi_spark(spark, size, num_partitions=4)
        error = abs(pi_est - math.pi)
        print(f"   {size:>9,} 样本 => π ≈ {pi_est:.6f}, 误差: {error:.6f}")
    
    print("\n" + "=" * 60)
    print("实验完成！")
    print("=" * 60)
    
    spark.stop()


if __name__ == "__main__":
    main()
