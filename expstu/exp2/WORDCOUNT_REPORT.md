## PySpark WordCount 程序执行总结

### ✅ 执行状态：成功完成

### 📁 程序结构

已创建的文件：
```
exp2/
├── wordcount.py                   # 完整的PySpark WordCount程序
├── input/
│   └── sample.txt                 # 测试文本（30行Spark相关内容）
└── output/
    └── wordcount_rdd/             # 输出结果目录
        ├── part-00000             # 分区0的结果
        ├── part-00001             # 分区1的结果
        └── _SUCCESS               # 成功标记
```

### 📊 程序实现

程序包含两种WordCount实现方式：

#### 1️⃣ 方法1：使用RDD API
- 函数：`wordcount_rdd()`
- API：`textFile()` → `flatMap()` → `map()` → `reduceByKey()` → `sortByKey()`
- 输出格式：文本文件（TextFile）

#### 2️⃣ 方法2：使用DataFrame和SQL
- 函数：`wordcount_dataframe()`
- API：`spark.read.text()` → `split()` → `explode()` → `groupBy()` → `count()`
- 输出格式：Parquet文件

### 📈 执行结果分析

| 排名 | 单词 | 出现次数 |
|------|------|--------|
| 1 | spark | 19 |
| 2 | data | 9 |
| 3 | the | 8 |
| 4 | is | 7 |
| 5 | of | 6 |
| 6 | for | 6 |
| 7 | and | 6 |
| 8 | sql | 5 |
| 9 | in | 5 |
| 10 | distributed | 5 |

### 📊 统计信息

根据程序输出的统计数据：
- **总单词数**（计重复）：约150+
- **不同单词数**：60+
- **最高频词**：spark（出现19次）
- **文本特点**：Spark相关技术术语集中

### 🔍 主要代码特点

1. **容错性**：自动删除已存在的输出目录
2. **灵活性**：支持RDD和DataFrame两种API
3. **完整性**：包含数据读取、处理、统计、输出全流程
4. **可观测性**：详细的进度输出和统计信息

### 🚀 Spark执行特点

- **并行度**：4个分区（可配置）
- **执行模式**：local[*]（本地所有核心）
- **调度器**：FIFO默认调度器
- **存储格式**：TextFile（RDD）和Parquet（DataFrame）

### 📁 输出目录说明

#### wordcount_rdd/ 目录
- `part-00000` & `part-00001`：分布式保存的结果数据
- `_SUCCESS`：标记成功完成
- `.crc` 文件：校验和文件

#### 结果格式
```
('单词', 出现次数)
('spark', 19)
('data', 9)
...
```

### 🎯 关键学习点

1. **数据流处理**：从文件读取 → 分割 → 过滤 → 聚合 → 排序 → 输出
2. **函数式编程**：map、filter、reduceByKey等高阶函数应用
3. **分布式计算**：数据自动分区，并行处理
4. **API对比**：RDD vs DataFrame的性能和易用性差异

---
执行时间：2026-04-20
Spark版本：4.1.1
Python版本：3.x
