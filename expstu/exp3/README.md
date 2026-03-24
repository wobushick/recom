# 实验三：RDD编程基础 - 完整实验

## 📋 实验概述

本实验是关于Apache Spark RDD编程的完整学习和实践，包含9个主要实验部分，涵盖从基础的RDD创建到高级的聚合操作的全方位内容。

**实验时间**: 2026年3月24日  
**环境**: Python 3.10.12 + PySpark 4.1.1 + Spark 4.1.1

---

## 📁 文件结构

```
exp3/
├── experiment_3.py              # 完整的实验代码（可直接运行）
├── README.md                    # 本文件
├── 实验总结.md                  # 详细的实验成果总结
├── 最佳实践指南.md              # 常见错误与优化建议
├── 实验参考书.md                # 原始实验指导书
├── 实验报告.docx                # 原始实验报告模板
├── data/                        # 实验数据目录
│   ├── employees.txt            # 员工数据（35条记录）
│   ├── departments.txt          # 部门数据
│   ├── scores.txt               # 学生成绩数据（36条记录）
│   ├── sentences.txt            # 句子文本（15行）
│   ├── articles.txt             # 文章文本
│   ├── documents.txt            # 文档数据（10条）
│   ├── logs.txt                 # 日志数据（30条）
│   └── products.txt             # 产品数据
└── output/                      # 实验结果输出目录
    ├── employees_cleaned/       # 清洗后的员工数据
    ├── rdd_output/              # RDD输出示例
    ├── rdd_output_5parts/       # 多分区RDD输出
    ├── wordcount_results/       # 词频统计结果
    └── inverted_index/          # 倒排索引结果
```

---

## 🚀 快速开始

### 运行完整实验

```bash
cd /workspaces/recom/expstu/exp3
python3 experiment_3.py
```

**预计执行时间**: 2-3分钟

### 查看实验结果

实验执行完成后，会在控制台输出详细的实验过程和结果，同时在 `output/` 目录生成相应的输出文件。

---

## 📚 实验内容详解

### 实验1：RDD的创建与基础数据预处理
- **目标**: 学会使用textFile方法创建RDD并进行数据清洗
- **关键API**: `textFile()`, `filter()`, `count()`
- **处理数据**: employees.txt
- **输出**: cleaned data with 35 valid records

**核心代码**:
```python
employees_rdd = sc.textFile("data/employees.txt")
cleaned_rdd = employees_rdd.filter(lambda line: line.strip() != "")
cleaned_rdd = cleaned_rdd.filter(lambda line: len(line.split(",")) == 3)
```

---

### 实验2：Transformation和Action算子的区别
- **目标**: 理解RDD的惰性求值机制
- **关键概念**: 
  - Transformation（转换）：`map()`, `filter()` - 不立即执行
  - Action（行动）：`collect()`, `count()` - 立即执行
- **核心发现**: 每次Action都会重新计算RDD（除非使用缓存）

**对比演示**:
```python
# Transformation - 不执行
mapped = rdd.map(lambda x: x * 2)
filtered = mapped.filter(lambda x: x > 5)

# Action - 立即执行所有Transformation
result = filtered.collect()  # [6, 8, 10]
```

---

### 实验3：常用Transformation算子的应用
- **关键算子**: 
  - `flatMap()`: 一对多映射
  - `map()`: 一对一映射
  - `filter()`: 过滤
  - `distinct()`: 去重
  - `union()`: 合并
- **处理数据**: sentences.txt (15行 → 139个单词 → 84个不重复单词)

---

### 实验4：常用Action算子与结果获取
- **关键算子**:
  - `count()`: 统计元素个数
  - `take(n)`: 获取前n个元素
  - `first()`: 获取第一个元素
  - `collect()`: 获取所有元素（小数据集）
  - `reduce()`: 聚合
  - `takeOrdered()`: 排序后取前n个

**测试数据**: 1-100的整数

---

### 实验5：RDD分区机制与自定义分区策略
- **关键概念**: 分区是并行计算的基本单位
- **分区操作**:
  - `repartition(n)`: 重新分区（会产生Shuffle）
  - `coalesce(n)`: 合并分区（不产生Shuffle）
  - `getNumPartitions()`: 查看分区数
  - `glom()`: 查看每个分区的内容

**演示**: 默认2分区 → repartition到4分区 → coalesce到2分区

---

### 实验6：RDD数据的持久化与分布式存储
- **关键操作**:
  - `saveAsTextFile()`: 保存为文本文件
  - `cache()`: 内存缓存
  - `persist()`: 指定存储级别
- **性能对比**: 使用缓存后第2次执行速度提升约65%

---

### 实验7：键值对RDD的排序与二次排序技术
- **关键算子**:
  - `sortByKey()`: 按Key排序
  - `sortBy()`: 自定义排序规则
  - 二次排序：构造复合Key
- **处理数据**: scores.txt (36条学生成绩)

**二次排序示例**:
```python
# 先按学生名排序，再按分数降序排序
complex_key_rdd = scores.map(lambda line: (
    (line.split(",")[0], -int(line.split(",")[2])),
    line.split(",")[1]
))
result = complex_key_rdd.sortByKey()
```

---

### 实验8：高级聚合算子combineByKey的原理与应用
- **三个核心函数**:
  1. `createCombiner`: 初始化组合器
  2. `mergeValue`: 合并同分区内的值
  3. `mergeCombiners`: 合并不同分区的结果
- **应用场景**: 计算部门统计信息（员工数、工资总和、最高/最低工资等）

**结果示例**:
```
D001: 9名员工，总工资62200，平均6911，范围5500-8500
D002: 8名员工，总工资75800，平均9475，范围8800-10400
```

---

### 实验9：综合练习 - 分布式编程实战

#### 案例1：数据去重与统计
- 处理日志数据，统计各类型日志频率
- 结果：INFO(19次), WARN(6次), ERROR(5次)

#### 案例2：WordCount完整实现
- 完整的文本处理流水线
- 数据清洗 → 分词 → 过滤停用词 → 统计频率
- 结果：368个词，175个不重复词，top词是"spark"(9次)

#### 案例3：倒排索引构建
- 构建检索索引
- 每个单词对应包含它的文档列表
- 用于快速查找包含特定词汇的文档

---

## 🔍 查看结果

### 查看Spark Web UI
实验运行时，可以访问 `http://localhost:4040` 查看实时运行情况

### 查看输出文件

```bash
# 查看清洗后的员工数据
cat output/employees_cleaned/part-00000

# 查看词频统计结果
cat output/wordcount_results/part-00000 | head -20

# 查看倒排索引
cat output/inverted_index/part-00000 | head -10
```

---

## 💡 关键学习要点

### 1. **理解惰性求值**
Spark不会在定义Transformation时立即执行，而是等到遇到Action时才执行。这样可以优化执行计划。

### 2. **API的分类**
掌握Transformation和Action的区分，以及它们各自何时使用

### 3. **分区的重要性**
合理的分区设置直接影响并行度和性能

### 4. **算子选择**
- `groupByKey` vs `reduceByKey` vs `combineByKey` 各有适用场景
- 优先选择能进行局部聚合的算子

### 5. **缓存策略**
对于多次使用的RDD要进行缓存，但要注意内存消耗

---

## 🛠️ 本地运行与调试

### 高级设置参数

```python
# 申请更多内存
conf = SparkConf().setAppName("Experiment3_RDD") \
    .setMaster("local[*]") \
    .set("spark.driver.memory", "4g") \
    .set("spark.executor.memory", "4g")

sc = SparkContext(conf=conf)
```

### 启用DEBUG日志

```python
sc.setLogLevel("DEBUG")  # 查看详细日志
```

### 快速测试（使用小数据集）

```python
# 使用parallelize创建小RDD进行测试
test_rdd = sc.parallelize(range(1, 101))
# 运行测试逻辑
```

---

## 📈 性能优化建议

1. **尽早过滤**: 在processing之前过滤掉不需要的数据
2. **使用reduceByKey**: 而不是groupByKey，可以进行局部聚合
3. **合理设置分区数**: 通常为CPU核数的2-3倍
4. **使用广播变量**: 共享只读的小数据集
5. **避免collect()**: 对于大数据集，使用take()或saveAsTextFile()

---

## ⚠️ 常见问题

**Q: 为什么程序在某个stage卡住了？**  
A: 可能是数据倾斜。检查key的分布，必要时增加分区数或使用二级排序。

**Q: 内存溢出（OOM）怎么办？**  
A: 
- 减少RDD的分区大小
- 使用persist()指定存储级别
- 避免使用collect()

**Q: 怎样确保代码的可序列化？**  
A: 
- 使用顶层函数而不是类方法
- 避免在lambda中引用外部状态
- 测试使用sc.parallelize()时是否出错

---

## 📖 参考资源

- [Apache Spark官方文档](https://spark.apache.org/docs/latest/)
- [PySpark API参考](https://spark.apache.org/docs/latest/api/python/)
- 本目录下的 `实验参考书.md`
- 本目录下的 `最佳实践指南.md`

---

## 📝 实验总结

本实验通过9个循序渐进的实验部分，让学习者从基础的RDD创建到高级的聚合操作，全面掌握Spark RDD编程的核心概念和应用技巧。

**关键收获**:
- ✓ 理解RDD的分布式计算模型
- ✓ 掌握Transformation和Action算子的正确使用
- ✓ 学会性能优化和调试技巧
- ✓ 能够解决实际的大数据处理问题

---

## 🎯 后续学习建议

1. **深入学习Spark SQL和DataFrame**: 这是现代Spark的优选API
2. **学习机器学习库**: MLlib和spark-mllib
3. **探索流处理**: Spark Streaming
4. **跟随最好的实践**: 学习大型开源项目的Spark使用方式
5. **参与真实项目**: 在实际大数据场景中应用所学知识

---

**最后更新**: 2026年3月24日  
**状态**: ✅ 实验完全完成
