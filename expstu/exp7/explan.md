# Exp7: DeepFM CTR预估实验说明

## 一、实验概述

本实验基于Criteo广告点击率数据集，实现DeepFM（Deep Factorization Machine）模型进行CTR（Click-Through Rate）预估。实验涵盖了从数据预处理、模型构建、训练优化到超参数调优的完整流程。

## 二、数据集

- **来源**: Criteo Display Advertising Challenge
- **训练集**: 7,200条样本（按8:2划分为5,760训练 + 1,440验证）
- **测试集**: 391条样本（dev.txt: 409条）
- **特征**: 13个连续特征 + 26个类别特征 = 39个特征字段
- **标签**: 0（未点击）或1（点击）

## 三、代码结构

```
exp7/
├── data/
│   ├── train.txt           # 训练数据
│   ├── test.txt            # 测试数据
│   ├── dev.txt             # 验证数据
│   ├── dataset.py          # CriteoDataset数据加载类
│   ├── feature_sizes.txt   # 特征维度文件（自动生成）
│   └── categorical_vocabs.pkl  # 类别词表（自动生成）
├── model/
│   └── DeepFM.py           # DeepFM模型定义
├── utils/
│   └── __init__.py
├── main.py                 # 训练主程序
└── best_model.pth          # 最佳模型参数
```

## 四、数据预处理（data/dataset.py）

`CriteoDataset`类完成以下处理：

1. **连续特征处理**（13个字段）：
   - 缺失值填充为0
   - 应用log1p变换：`log(1 + max(x, 0))`压缩数值范围
   - 特征索引Xi设为0（使用1维Embedding）

2. **类别特征处理**（26个字段）：
   - 统计各类别值出现频次
   - 过滤低频类别（cutoff=10，出现次数<10的归为`<unk>`）
   - 索引0保留给未登录词（`<unk>`）
   - 按频次降序排列，从1开始分配整数索引
   - 特征值Xv设为1.0

3. **输出格式**: `(Xi, Xv, label)` 三元组

4. **生成文件**:
   - `feature_sizes.txt`: 每个字段的特征维度（连续=1，类别=词表大小+1）
   - `categorical_vocabs.pkl`: 类别→索引映射字典

## 五、DeepFM模型架构（model/DeepFM.py）

### 5.1 核心组件

| 组件 | 实现 | 作用 |
|------|------|------|
| FM一阶嵌入 | `nn.Embedding(feature_size, 1)` × 39 | 线性特征权重，类似逻辑回归 |
| FM二阶嵌入 | `nn.Embedding(feature_size, 4)` × 39 | 二阶特征交叉（与DNN共享） |
| DNN隐藏层 | Linear + BatchNorm1d + Dropout | 高阶特征交互学习 |
| 全局偏置 | `nn.Parameter(torch.randn(1))` | 全局偏置项 |

### 5.2 前向传播公式

```
y = Σ(fm_first_order) + Σ(fm_second_order) + Σ(deep_out) + bias
```

其中FM二阶交叉使用化简公式：
```
ΣΣ(v_i·v_j)·x_i·x_j = 0.5 × [(Σv_i·x_i)² - Σ(v_i·x_i)²]
```

复杂度从 O(k·n²) 降至 O(k·n)，k为嵌入维度，n为特征数。

### 5.3 关键设计：共享嵌入

FM二阶嵌入层同时被FM组件和DNN组件使用：
- FM组件直接利用嵌入计算二阶交叉
- DNN组件将嵌入拼接后输入隐藏层

这确保了低阶交互和高阶交互从相同的特征表示中学习。

### 5.4 模型参数

- **默认配置**: embedding_size=4, hidden_dims=[32, 32], dropout=[0.5, 0.5]
- **参数量**: 约13,334个可训练参数

## 六、训练流程

### 6.1 训练配置

| 参数 | 值 |
|------|-----|
| 优化器 | Adam |
| 学习率 | 1e-3 |
| 损失函数 | BCEWithLogitsLoss |
| 批量大小 | 100 |
| 训练轮数 | 10（早停patience=3） |
| 设备 | CPU |

### 6.2 训练循环

```
for each epoch:
    for each batch (xi, xv, y):
        total = model(xi, xv)        # 前向传播
        loss = criterion(total, y)   # 计算损失
        optimizer.zero_grad()        # 清零梯度
        loss.backward()              # 反向传播
        optimizer.step()             # 更新参数
```

### 6.3 早停机制

- 监控验证集准确率
- 3个epoch内验证准确率未提升则停止训练
- 自动保存最佳模型参数

## 七、实验结果

### 7.1 训练结果

| Epoch | 训练损失 | 验证准确率 |
|-------|---------|-----------|
| 1 | 26.15 | 0.7056 |
| 2 | 19.48 | 0.7299 |
| 3 | 16.83 | 0.7264 |
| 4 | 14.87 | 0.7229 |
| 5 | 13.31 | 0.7153 |

- **最佳验证准确率**: 73.40%（第7轮）
- **测试集准确率**: 70.59%

### 7.2 结果分析

1. 验证准确率在73%左右，考虑到训练集仅7,200条样本，结果合理
2. 损失持续下降但验证准确率在第5轮后下降，出现轻度过拟合
3. 早停机制在第6轮触发，避免进一步过拟合
4. 测试集准确率（70.59%）略低于验证集，表明模型泛化能力有提升空间

## 八、超参数对比实验（main.py已实现）

### 8.1 嵌入维度对比
```python
experiment_embedding_size()  # 对比 embedding_size = [4, 8, 16]
```

### 8.2 DNN结构对比
```python
experiment_dnn_structure()   # 对比 [32,32] vs [64,64] vs [128,64,32]
```

### 8.3 学习率对比
```python
experiment_learning_rate()   # 对比 lr = [1e-3, 1e-4, 1e-5]
```

## 九、改进方向（对应参考书第十节）

1. **添加激活函数**: 在DNN的BatchNorm后添加ReLU激活，增强非线性表达能力
2. **AUC评估**: 增加AUC和Log Loss指标，较准确率更适合正负样本不平衡场景
3. **随机打乱训练/验证划分**: 使用`random.shuffle(indices)`替代顺序切分
4. **类别加权**: 针对正负样本不平衡设置`pos_weight`参数
5. **注意力机制**: 引入AFM风格的注意力权重学习不同特征交互的重要性

## 十、思考题简答

1. **cutoff阈值影响**: 提高cutoff→词表缩小→参数量减少→可能丢失长尾信息；降低则相反
2. **log1p vs Z-Score**: log1p能有效压缩长尾分布且无需预计算全局统计量；Z-Score更适合近似正态分布的特征
3. **未登录词共享Embedding**: 优点是可泛化到未见值且节省参数量；缺点是所有未知值使用相同表示，丢失了潜在区分信息
