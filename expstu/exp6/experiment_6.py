#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import math
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, split, explode, array_contains, collect_set, countDistinct, lit, expr
from pyspark.ml.recommendation import ALS
from pyspark.ml.fpm import FPGrowth
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator


def try_cast(value):
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    if value.isdigit():
        return int(value)
    try:
        return float(value)
    except ValueError:
        return value


def read_csv_as_spark_df(spark, relative_path):
    path = os.path.join(os.getcwd(), relative_path)
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("AIGC:")]

    reader = csv.DictReader(lines)
    rows = []
    for record in reader:
        rows.append({k: try_cast(v) for k, v in record.items()})

    return spark.createDataFrame(rows)


def load_movielens_ratings(spark, relative_path):
    path = os.path.join(os.getcwd(), relative_path)
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text or text.startswith("AIGC:"):
                continue
            if text.count("::") != 3:
                continue
            parts = text.split("::")
            if len(parts) != 4:
                continue
            try:
                rows.append(Row(userId=int(parts[0]), movieId=int(parts[1]), rating=float(parts[2])))
            except ValueError:
                continue
    return spark.createDataFrame(rows)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    spark = SparkSession.builder \
        .appName("Experiment6_Recommender") \
        .master("local[*]") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    print("=" * 80)
    print("实验六：推荐系统与 ALS / FP-growth 实验")
    print("=" * 80)

    # 一、RDD 数据清洗与 DataFrame 格式化
    print("\n【一】RDD 数据清洗与 DataFrame 格式化")
    ratings = load_movielens_ratings(spark, "sample_movielens_ratings.txt")
    print("数据结构：")
    ratings.printSchema()
    print("前10条记录：")
    ratings.show(10, truncate=False)

    # 二、调用 ALS 算法完成模型训练
    print("\n【二】调用 ALS 算法完成模型训练")
    train, test = ratings.randomSplit([0.8, 0.2], seed=42)
    print(f"训练集行数: {train.count()}, 测试集行数: {test.count()}")

    als = ALS(
        rank=10,
        maxIter=5,
        regParam=0.01,
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        coldStartStrategy="drop"
    )
    model = als.fit(train)

    print("ALS 模型训练完成。用户隐因子和物品隐因子预览：")
    model.userFactors.show(5, truncate=False)
    model.itemFactors.show(5, truncate=False)

    # 三、基于用户和商品的推荐
    print("\n【三】基于用户和商品的推荐")
    print("为所有用户生成 Top-10 推荐")
    user_recs = model.recommendForAllUsers(10)
    user_recs.show(5, truncate=False)

    print("为所有商品生成 Top-10 用户推荐")
    item_recs = model.recommendForAllItems(10)
    item_recs.show(5, truncate=False)

    users_subset = ratings.select("userId").distinct().limit(3)
    print("为指定用户子集推荐")
    user_subset_recs = model.recommendForUserSubset(users_subset, 10)
    user_subset_recs.show(truncate=False)

    items_subset = ratings.select("movieId").distinct().limit(3)
    print("为指定商品子集推荐")
    item_subset_recs = model.recommendForItemSubset(items_subset, 10)
    item_subset_recs.show(truncate=False)

    # 四、FP-growth 关联规则商品推荐
    print("\n【四】FP-growth 关联规则商品推荐")
    sample_data = [
        (0, [1, 2, 5]),
        (1, [1, 2, 3, 5]),
        (2, [1, 2]),
        (3, [1, 3, 4]),
        (4, [2, 3, 5]),
        (5, [1, 3, 5])
    ]
    sample_df = spark.createDataFrame(sample_data, ["id", "items"])
    print("小规模示例数据：")
    sample_df.show(truncate=False)

    fp_growth = FPGrowth(itemsCol="items", minSupport=0.5, minConfidence=0.6)
    fp_model = fp_growth.fit(sample_df)
    print("频繁项集：")
    fp_model.freqItemsets.show(truncate=False)
    print("关联规则：")
    fp_model.associationRules.show(truncate=False)
    print("原始事务预测结果：")
    fp_model.transform(sample_df).show(truncate=False)

    print("使用完整交易数据进行关联规则挖掘")
    transaction_df = read_csv_as_spark_df(spark, "user_transactions.csv")
    transaction_df = transaction_df.withColumn("items", expr("transform(split(items, ' '), x -> cast(x as int))"))
    transaction_fp = FPGrowth(itemsCol="items", minSupport=0.2, minConfidence=0.6)
    transaction_fp_model = transaction_fp.fit(transaction_df)
    transaction_fp_model.freqItemsets.show(10, truncate=False)
    transaction_fp_model.associationRules.show(10, truncate=False)
    transaction_fp_model.transform(transaction_df).show(5, truncate=False)

    # 五、基于评分次数的电影推荐
    print("\n【五】基于评分次数的电影推荐")
    user_counts = ratings.groupBy("userId").count().orderBy(col("count").desc())
    movie_counts = ratings.groupBy("movieId").count().orderBy(col("count").desc())
    print("用户评分次数前10：")
    user_counts.show(10, truncate=False)
    print("电影评分次数前10：")
    movie_counts.show(10, truncate=False)

    active_users = user_counts.filter(col("count") >= 30)
    print(f"活跃用户数量（评分次数>=30）: {active_users.count()}")

    activity_df = read_csv_as_spark_df(spark, "user_activity.csv")
    print("user_activity.csv 验证结果：")
    activity_df.show(10, truncate=False)

    # 六、混合推荐规则与已观看项目过滤
    print("\n【六】混合推荐规则与已观看项目过滤")
    als_recs = model.recommendForAllUsers(10).select("userId", explode("recommendations").alias("rec"))
    als_recs = als_recs.select(
        col("userId"),
        col("rec.movieId").alias("movieId"),
        col("rec.rating").alias("prediction")
    )
    fp_recs = transaction_fp_model.transform(transaction_df).select("userId", explode("prediction").alias("movieId"))
    fp_recs = fp_recs.withColumn("prediction", lit(0.0))

    combined_recs = als_recs.unionByName(fp_recs)
    watched = ratings.groupBy("userId").agg(collect_set("movieId").alias("watched"))
    filtered_recs = combined_recs.join(watched, on="userId", how="left")
    filtered_recs = filtered_recs.filter(~array_contains(col("watched"), col("movieId")))
    filtered_recs = filtered_recs.dropDuplicates(["userId", "movieId"]).orderBy("userId", col("prediction").desc())
    print("混合推荐过滤已观看结果示例：")
    filtered_recs.show(20, truncate=False)

    # 七、使用 RegressionEvaluator 评估 ALS 模型
    print("\n【七】使用 RegressionEvaluator 评估 ALS 模型")
    predictions = model.transform(test).na.drop(subset=["prediction"])
    print(f"测试集预测结果数量（去除 NaN）: {predictions.count()}")
    evaluator_rmse = RegressionEvaluator(metricName="rmse", labelCol="rating", predictionCol="prediction")
    evaluator_mae = RegressionEvaluator(metricName="mae", labelCol="rating", predictionCol="prediction")
    rmse = evaluator_rmse.evaluate(predictions)
    mae = evaluator_mae.evaluate(predictions)
    print(f"RMSE = {rmse:.4f}")
    print(f"MAE = {mae:.4f}")

    # 八、稀疏性问题与冷启动应对
    print("\n【八】稀疏性问题与冷启动应对")
    num_users = ratings.select(countDistinct("userId")).first()[0]
    num_movies = ratings.select(countDistinct("movieId")).first()[0]
    num_ratings = ratings.count()
    sparsity = 1.0 - num_ratings / float(num_users * num_movies)
    print(f"用户数={num_users}, 电影数={num_movies}, 评分数={num_ratings}")
    print(f"评分矩阵稀疏度={sparsity:.6f}")

    cold_users = read_csv_as_spark_df(spark, "cold_start_users.csv")
    print("冷启动用户评分数据：")
    cold_users.show(10, truncate=False)

    cold_preds = model.transform(cold_users)
    print(f"原始 ALS 模型对冷启动用户的预测条数: {cold_preds.count()} (如果为0则大多数冷启动用户被丢弃)")

    extended_ratings = load_movielens_ratings(spark, "extended_ratings.txt")
    extended_training = ratings.union(extended_ratings)
    extended_model = als.fit(extended_training)
    cold_preds_extended = extended_model.transform(cold_users)
    print(f"扩展训练后冷启动用户预测条数: {cold_preds_extended.count()}")

    # 九、交叉验证与超参数优化
    print("\n【九】交叉验证与超参数优化")
    param_grid = ParamGridBuilder() \
        .addGrid(als.rank, [5, 10]) \
        .addGrid(als.regParam, [0.01, 0.1]) \
        .addGrid(als.maxIter, [5]) \
        .build()
    cv = CrossValidator(
        estimator=als,
        estimatorParamMaps=param_grid,
        evaluator=evaluator_rmse,
        numFolds=2
    )
    cv_model = cv.fit(train)
    best_model = cv_model.bestModel
    print("最优模型参数：")
    best_rank = getattr(best_model, "rank", None)
    best_reg = getattr(best_model, "getRegParam", None)
    best_iter = getattr(best_model, "getMaxIter", None)
    if callable(best_reg):
        best_reg = best_reg()
    if callable(best_iter):
        best_iter = best_iter()
    print(f"rank = {best_rank}")
    print(f"regParam = {best_reg}")
    print(f"maxIter = {best_iter}")
    print(f"平均评估指标数量: {len(cv_model.avgMetrics)}")

    best_predictions = best_model.transform(test).na.drop(subset=["prediction"])
    best_rmse = evaluator_rmse.evaluate(best_predictions)
    print(f"最优模型测试集 RMSE = {best_rmse:.4f}")

    # 十、隐因子矩阵的可解释性分析与可视化
    print("\n【十】隐因子矩阵的可解释性分析与可视化")
    user_factors = best_model.userFactors.collect()
    item_factors = best_model.itemFactors.collect()

    import numpy as np
    user_ids = [row.id for row in user_factors]
    item_ids = [row.id for row in item_factors]
    user_vectors = np.array([row.features for row in user_factors])
    item_vectors = np.array([row.features for row in item_factors])

    print(f"用户隐因子样例数量: {len(user_vectors)}, 物品隐因子样例数量: {len(item_vectors)}")
    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        user_2d = pca.fit_transform(user_vectors)
        item_2d = pca.fit_transform(item_vectors)
        print("PCA 降维完成，二维表示前5个用户/物品点：")
        print("用户二维样例:")
        for i in range(min(5, len(user_ids))):
            print(f"  userId={user_ids[i]}, point={user_2d[i].tolist()}")
        print("物品二维样例:")
        for i in range(min(5, len(item_ids))):
            print(f"  movieId={item_ids[i]}, point={item_2d[i].tolist()}")
    except Exception as exc:
        print(f"PCA 未安装或无法执行: {exc}")

    sample_user_id = user_ids[0]
    sample_user_vec = user_vectors[0]
    item_scores = item_vectors.dot(sample_user_vec)
    top_indices = np.argsort(-item_scores)[:5]
    top_movie_ids = [item_ids[i] for i in top_indices]
    print(f"用户 {sample_user_id} 的 Top-5 物品（基于隐因子点积）: {top_movie_ids}")

    movies_df = read_csv_as_spark_df(spark, "movies.csv")
    movies_df = movies_df.withColumn("movieId", col("movieId").cast("int"))
    top_movies = spark.createDataFrame([(mid,) for mid in top_movie_ids], ["movieId"]) \
        .join(movies_df, on="movieId", how="left")
    print("Top-5 电影详情：")
    top_movies.show(truncate=False)

    spark.stop()
    print("SparkSession 已停止。")


if __name__ == "__main__":
    main()
