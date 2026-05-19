"""Build experiment5.ipynb from code sections."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.10.12"
    }
}

cells = []

def add_md(source):
    cells.append(nbf.v4.new_markdown_cell(source))

def add_code(source):
    cells.append(nbf.v4.new_code_cell(source))

# ==================== Section 0 ====================
add_md("## 零、环境准备")
add_code("""from pyspark.sql import SparkSession
import pandas as pd

spark = SparkSession.builder \\
    .appName("experiment5") \\
    .getOrCreate()

# 使用 pandas 读取 CSV (规避 Hadoop FileSystem 兼容性问题)
pdf = pd.read_csv("customer_loan.csv")
df = spark.createDataFrame(pdf)
df.printSchema()
df.show(5)""")

# ==================== Section 1 ====================
add_md("## 一、Estimator 与 Transformer 核心抽象")

add_md("### 1.1 创建 LogisticRegression Estimator")
add_code("""from pyspark.ml.classification import LogisticRegression

lr = LogisticRegression(featuresCol="features", labelCol="label")
lr.explainParams()""")

add_md("### 1.2 使用 extractParamMap 查看参数配置")
add_code("""# PySpark 4.x 中 ParamMap 类已移除, 改用 extractParamMap() 返回 dict
pm = lr.extractParamMap()
print(f"参数总数: {len(pm)}")
# 打印部分关键参数
for p, v in pm.items():
    if p.name in ["maxIter", "regParam", "elasticNetParam", "family", "featuresCol", "labelCol"]:
        print(f"  {p.name:20s} = {v}")""")

add_md("### 1.3 直接设置参数与对比")
add_code("""# 方式一：构造函数传参 (PySpark 4.x 推荐)
lr2 = LogisticRegression(featuresCol="features", labelCol="label",
                          maxIter=100, regParam=0.01, elasticNetParam=0.8)
print("方式一 (构造函数传参):")
print(f"  maxIter={lr2.getMaxIter()}, regParam={lr2.getRegParam()}, elasticNetParam={lr2.getElasticNetParam()}")

# 方式二：setter 方法设置
lr3 = LogisticRegression(featuresCol="features", labelCol="label")
lr3.setMaxIter(50).setRegParam(0.05)
print("\\n方式二 (setter 方法):")
print(f"  maxIter={lr3.getMaxIter()}, regParam={lr3.getRegParam()}")

# 再次查看完整参数说明
lr3.explainParams()

print("\\n=== 对比总结 ===")
print("构造函数方式: 一次性设置所有参数, 代码简洁, PySpark 4.x 推荐")
print("setter 方式: 链式调用逐个设置, 适合动态调整参数")
print("注: PySpark 4.x 已移除 ParamMap 类, 原有 ParamMap 用法需更新")""")

# ==================== Section 2 ====================
add_md("## 二、特征工程——文本分词与哈希特征转换")

add_md("### 2.1 加载文本数据")
add_code("""spam_pdf = pd.read_csv("spam_messages.csv")
spam_df = spark.createDataFrame(spam_pdf)
spam_df.show(10, truncate=False)""")

add_md("### 2.2 文本分词（Tokenizer）")
add_code("""from pyspark.ml.feature import Tokenizer

tokenizer = Tokenizer(inputCol="message", outputCol="words")
tokenized_df = tokenizer.transform(spam_df)
tokenized_df.select("message", "words").show(5, truncate=False)""")

add_md("### 2.3 词频哈希特征（HashingTF）")
add_code("""from pyspark.ml.feature import HashingTF

hashingTF = HashingTF(inputCol="words", outputCol="rawFeatures", numFeatures=1000)
featurized_df = hashingTF.transform(tokenized_df)
featurized_df.select("words", "rawFeatures").show(5, truncate=False)""")

# ==================== Section 3 ====================
add_md("## 三、逻辑回归模型训练与预测")

add_md("### 3.1 数据准备与向量化")
add_code("""from pyspark.ml.feature import VectorAssembler

loan_pdf = pd.read_csv("customer_loan.csv")
loan_df = spark.createDataFrame(loan_pdf)

feature_cols = ["age", "income", "credit_score", "loan_amount",
                "employment_years", "debt_ratio"]

assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")
training_data = assembler.transform(loan_df)
training_data.select("label", "features").show(5, truncate=False)""")

add_md("### 3.2-3.3 训练逻辑回归模型并预测")
add_code("""lr = LogisticRegression(
    featuresCol="features", labelCol="label",
    maxIter=100, regParam=0.01, elasticNetParam=0.8
)

model = lr.fit(training_data)

predictions = model.transform(training_data)
predictions.select("label", "prediction", "probability").show(10, truncate=False)""")

# ==================== Section 4 ====================
add_md("## 四、模型训练摘要信息提取")
add_code("""summary = model.summary

print("迭代次数:", summary.totalIterations)
print("\\n目标函数历史值:", summary.objectiveHistory)
print("\\n准确率 (Accuracy):", summary.accuracy)
print("\\nROC 曲线下面积 (AUC):", summary.areaUnderROC)

print("\\n--- 模型参数 ---")
print("系数矩阵:")
print(model.coefficientMatrix)
print("\\n截距向量:", model.interceptVector)

print("\\n--- 按标签评估 ---")
print("真阳性率:", summary.truePositiveRateByLabel)
print("假阳性率:", summary.falsePositiveRateByLabel)

print("\\n--- 各标签预测统计 ---")
# PySpark 4.x: predictionsByLabel 已移除, 改用手动统计
predictions.groupBy("label", "prediction").count().show()

# 打印更多评估指标 (PySpark 4.x 新增)
print("\\n--- 加权评估指标 ---")
print(f"加权精确率: {summary.weightedPrecision:.4f}")
print(f"加权召回率: {summary.weightedRecall:.4f}")
print(f"加权 F1:     {summary.weightedFMeasure(1.0):.4f}")

# 特征重要性分析
import numpy as np
coeffs = model.coefficientMatrix.toArray().flatten()
print("\\n--- 特征重要性（系数绝对值越大 → 影响越强）---")
for name, coef in zip(feature_cols, coeffs):
    print(f"  {name:20s}: {coef:+.6f}  (|coef| = {abs(coef):.6f})")""")

# ==================== Section 5 ====================
add_md("## 五、ML 管道技术——文本逻辑回归分类器")

add_md("### 5.1 加载与划分数据")
add_code("""spam_pdf2 = pd.read_csv("spam_messages.csv")
spam_df2 = spark.createDataFrame(spam_pdf2)
spam_df2 = spam_df2.withColumn("label", spam_df2["label"].cast("double"))

train_data, test_data = spam_df2.randomSplit([0.8, 0.2], seed=42)
print("训练集行数:", train_data.count())
print("测试集行数:", test_data.count())""")

add_md("### 5.2-5.3 组装 Pipeline 并预测")
add_code("""from pyspark.ml import Pipeline

tokenizer = Tokenizer(inputCol="message", outputCol="words")
hashingTF = HashingTF(inputCol="words", outputCol="features", numFeatures=1000)
lr = LogisticRegression(featuresCol="features", labelCol="label",
                        maxIter=100, regParam=0.01)

pipeline = Pipeline(stages=[tokenizer, hashingTF, lr])
pipeline_model = pipeline.fit(train_data)

predictions = pipeline_model.transform(test_data)
predictions.select("label", "message", "prediction", "probability") \\
    .show(10, truncate=False)

# 计算测试集准确率
correct = predictions.filter(predictions["label"] == predictions["prediction"]).count()
total = predictions.count()
print(f"\\n测试集准确率: {correct}/{total} = {correct/total:.4f}")""")

# ==================== Section 6 ====================
add_md("## 六、模型持久化——保存与加载")

add_md("### 6.1 保存 PipelineModel")
add_code("""pipeline_model.write().overwrite().save("file:///workspaces/recom/expstu/exp5/spam_pipeline_model")

import os
print("spam_pipeline_model 目录结构:")
for root, dirs, files in os.walk("spam_pipeline_model"):
    level = root.replace("spam_pipeline_model", "").count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = "  " * (level + 1)
    for f in files[:5]:
        print(f"{subindent}{f}")
    if len(files) > 5:
        print(f"{subindent}... ({len(files)} files total)")""")

add_md("### 6.2 加载 PipelineModel")
add_code("""from pyspark.ml import PipelineModel

loaded_pipeline_model = PipelineModel.read().load("file:///workspaces/recom/expstu/exp5/spam_pipeline_model")
loaded_predictions = loaded_pipeline_model.transform(test_data)

# 对比原始预测与加载后预测的一致性
original_labels = predictions.select("prediction").collect()
loaded_labels = loaded_predictions.select("prediction").collect()
match = sum(1 for o, l in zip(original_labels, loaded_labels) if o["prediction"] == l["prediction"])
print(f"预测一致性: {match}/{len(original_labels)} (全部一致则模型加载正确)")

loaded_predictions.select("label", "message", "prediction", "probability") \\
    .show(5, truncate=False)""")

add_md("### 6.3 保存与加载单个 LogisticRegressionModel")
add_code("""from pyspark.ml.classification import LogisticRegressionModel

model.write().overwrite().save("file:///workspaces/recom/expstu/exp5/lr_model")

loaded_lr_model = LogisticRegressionModel.read().load("file:///workspaces/recom/expstu/exp5/lr_model")

print("原始模型系数:")
print(model.coefficientMatrix)
print("原始模型截距:", model.interceptVector)

print("\\n加载模型系数:")
print(loaded_lr_model.coefficientMatrix)
print("加载模型截距:", loaded_lr_model.interceptVector)""")

# ==================== Section 7 ====================
add_md("## 七、统计计算——均值、范数与相关矩阵")

add_md("### 7.1-7.2 数据准备与 Summarizer 统计")
add_code("""health_pdf = pd.read_csv("health_data.csv")
health_df = spark.createDataFrame(health_pdf)

health_cols = ["height", "weight", "blood_pressure", "cholesterol", "blood_sugar", "bmi"]
assembler = VectorAssembler(inputCols=health_cols, outputCol="features")
health_data = assembler.transform(health_df)

from pyspark.ml.stat import Summarizer

summary_stats = health_data.select(
    Summarizer.summarizer(health_data["features"],
                          "mean", "variance", "norm(l1)", "norm(l2)", "max", "min")
).collect()[0][0]

print("=== Summarizer 多维度统计 ===")
print("均值 (mean):      ", summary_stats.mean.values)
print("方差 (variance):  ", summary_stats.variance.values)
print("最大值 (max):     ", summary_stats.max.values)
print("最小值 (min):     ", summary_stats.min.values)

# 展示前5个样本的 L1/L2 范数
stats_df = health_data.select(
    Summarizer.summarizer(health_data["features"], "norm(l1)", "norm(l2)")
)
print("\\n前5个样本的 L1 范数和 L2 范数:")
stats_df.show(5, truncate=False)""")

add_md("### 7.3 皮尔逊相关矩阵")
add_code("""from pyspark.ml.stat import Correlation

n = len(health_cols)

pearson_result = Correlation.corr(health_data, "features", method="pearson")
pearson_matrix = pearson_result.collect()[0][0].toArray().reshape(n, n)

print("=== 皮尔逊相关矩阵 ===")
print("              ", "  ".join(f"{c:>10s}" for c in health_cols))
for i, name in enumerate(health_cols):
    row_str = "  ".join(f"{pearson_matrix[i][j]:10.4f}" for j in range(n))
    print(f"{name:>14s}: {row_str}")""")

add_md("### 7.4 斯皮尔曼相关矩阵")
add_code("""spearman_result = Correlation.corr(health_data, "features", method="spearman")
spearman_matrix = spearman_result.collect()[0][0].toArray().reshape(n, n)

print("=== 斯皮尔曼相关矩阵 ===")
print("              ", "  ".join(f"{c:>10s}" for c in health_cols))
for i, name in enumerate(health_cols):
    row_str = "  ".join(f"{spearman_matrix[i][j]:10.4f}" for j in range(n))
    print(f"{name:>14s}: {row_str}")

print("\\n=== 皮尔逊 vs 斯皮尔曼 对比 ===")
print("皮尔逊：度量线性相关关系，对异常值敏感")
print("斯皮尔曼：度量单调关系（秩相关），对异常值鲁棒")
print("若变量呈 U 型关系，皮尔逊 ≈ 0（无线型），斯皮尔曼也可能 ≈ 0（非单调）")""")

# ==================== Section 8 ====================
add_md("## 八、RDD 分层抽样与随机数生成")

add_md("### 8.1-8.2 准备 RDD 数据与分层抽样")
add_code("""sales_pdf = pd.read_csv("sales_data.csv")
sales_df = spark.createDataFrame(sales_pdf)

print("各类别数据量分布:")
sales_df.groupBy("category").count().show()

# 转换为 PairRDD 并分层抽样
fractions = {"电子产品": 0.5, "服装": 0.3, "食品": 0.4}
pair_rdd = sales_df.rdd.map(lambda row: (row["category"], row))
sampled_rdd = pair_rdd.sampleByKey(False, fractions, seed=42)

# 转回 DataFrame
sampled_df = spark.createDataFrame(sampled_rdd.map(lambda x: x[1]))

print("\\n抽样后各类别数量:")
sampled_df.groupBy("category").count().show()
sampled_df.show(10, truncate=False)""")

add_md("### 8.3 随机数生成（RandomRDDs）")
add_code("""from pyspark.mllib.random import RandomRDDs

sc = spark.sparkContext

# 正态分布 N(0,1)
normal_rdd = RandomRDDs.normalRDD(sc, 1000, seed=42)
normal_mean = normal_rdd.mean()
normal_stdev = normal_rdd.stdev()
print(f"正态分布随机数 (N=1000): 均值={normal_mean:.4f}, 标准差={normal_stdev:.4f}")
print(f"  期望: 均值≈0, 标准差≈1")

# 均匀分布 U(0,1)
uniform_rdd = RandomRDDs.uniformRDD(sc, 1000, seed=42)
uniform_stats = uniform_rdd.stats()
print(f"\\n均匀分布随机数 (N=1000):")
print(f"  均值={uniform_stats.mean():.4f}, 标准差={uniform_stats.stdev():.4f}")
print(f"  最小值={uniform_stats.min():.4f}, 最大值={uniform_stats.max():.4f}")
print(f"  期望: 均值≈0.5, 范围在 [0, 1)")""")

add_md("### 8.4 ML API 与 MLlib API 的对比使用")
add_code("""print("=== ML API vs MLlib API 对比 ===")
print()
print("ML API (DataFrame-based):")
print("  - 基于 DataFrame, 提供 Pipeline、Estimator、Transformer 抽象")
print("  - 适合结构化数据、特征工程、模型训练的生产级管道")
print("  - 示例: Pipeline(stages=[Tokenizer, HashingTF, LogisticRegression])")
print()
print("MLlib API (RDD-based):")
print("  - 基于 RDD, 提供更低层的操作接口")
print("  - 适合自定义算法、随机数生成、数据抽样等底层操作")
print("  - 示例: RandomRDDs.normalRDD(), rdd.sampleByKey()")
print()
print("spark (SparkSession) 与 sc (SparkContext) 的关系:")
print("  sc = spark.sparkContext")
print("  SparkSession 是 DataFrame/SQL 入口, SparkContext 是 RDD 入口")
print("  ML API 主要使用 spark, MLlib API 主要使用 sc")
print()
print("选择策略:")
print("  - 推荐优先使用 ML API (DataFrame), 因其性能优化更好")
print("  - 需要底层控制或兼容旧代码时使用 MLlib API (RDD)")""")

# ==================== Done ====================
add_md("## 实验完成")
add_code("""print("=== 实验五：PySpark 机器学习基础 — 全部完成 ===")
print()
print("完成清单:")
print("  [✓] 零、环境准备 — SparkSession 初始化")
print("  [✓] 一、Estimator 与 Transformer 核心抽象")
print("  [✓] 二、特征工程 — 文本分词与哈希特征转换")
print("  [✓] 三、逻辑回归模型训练与预测")
print("  [✓] 四、模型训练摘要信息提取")
print("  [✓] 五、ML 管道技术 — 文本逻辑回归分类器")
print("  [✓] 六、模型持久化 — 保存与加载")
print("  [✓] 七、统计计算 — 均值、范数与相关矩阵")
print("  [✓] 八、RDD 分层抽样与随机数生成")

spark.stop()""")

nb.cells = cells
nbf.write(nb, "experiment5.ipynb")
print("Notebook created: experiment5.ipynb with", len(cells), "cells")
