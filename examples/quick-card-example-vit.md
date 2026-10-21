# ViT 速读卡 · 2021-06-03

> ICLR 2021 · arXiv:2010.11929 · 代码：有（官方 JAX/Flax + 社区 PyTorch）
> 全文 22 页 · 主实验 ImageNet / CIFAR / Pets / Flowers / VTAB(19) / 3 个预训练集

<!--
格式示例。本卡中的每个数字都已对 arXiv:2010.11929v2 的 Table 1 / Table 2 与正文核过，
出处见每行末列。定性结论均标了节号。这是示范"核到什么程度才算核过"，
不是让你引用这份文件——真要引用请自己核一遍。
-->

---

## 一句话

把图像切成 16×16 的 patch 当作 token，直接用标准 Transformer 编码器做分类，不含任何卷积。

## 它要解决什么

Transformer 在 NLP 已是标准架构，视觉里始终没替代 CNN。已有尝试要么保留卷积骨架，要么用复杂注意力模式替换卷积核。

**论文的问题设定**：能不能**完全不加卷积**，把图像当作 token 序列喂给标准 Transformer？

**论文自己说的贡献**（引原文措辞）：
1. "we show that a pure transformer applied directly to sequences of image patches can perform very well on image classification tasks"
2. "when pre-trained on large amounts of data and transferred to multiple mid-sized or small image recognition benchmarks, Vision Transformer (ViT) attains excellent results compared to state-of-the-art convolutional networks while requiring substantially fewer computational resources to train"

> 注意第 2 条里有个前提没被强调：**"when pre-trained on large amounts of data"**。这个前提恰恰是全文最关键的限制条件。

## 怎么做

1. **切 patch**：图像 `(H, W, C)` → `N = HW/P²` 个 `P×P` 块，`P=16` → 展平 → 线性投影到 `D` 维 → `N` 个 token
2. **加位置**：序列首位拼一个可学习 `[class]` token；所有 token 加**可学习 1D 位置编码**（非 2D）
3. **过 Transformer**：标准 encoder（MSA + MLP 交替，LN 前置），取 `[class]` 输出接分类头

**关键设计**：patch embedding 等价于 stride=P 的卷积，这是全模型**唯一**与图像结构有关的部分。原文明确写道，位置编码在初始化时"carry no information about the 2D positions of the patches and all spatial relations between the patches have to be learned from scratch"（§3.1）。

**承重墙判断**：不是某个模块，而是**预训练数据规模**——见下面的"最硬的数"第 4 行。

## 最硬的数

| 对比 | 数字 | 出处 |
|---|---|---|
| ViT-H/14（JFT-300M）vs BiT-L（ResNet152x4） | ImageNet top-1 **88.55 vs 87.54**（+1.01） | Table 2 |
| 同上 vs Noisy Student（EfficientNet-L2） | **88.55 vs 88.4**（+0.15） | Table 2 |
| 预训练成本：ViT-H/14 vs Noisy Student | **2.5k vs 12.3k** TPUv3-core-days（约 1/5） | Table 2 末行 |
| **规模效应（定性）** | 用 ImageNet-1k 预训练时，**大 ViT 反而输给小 ViT，也输给 BiT ResNet**；只有 JFT-300M 才体现出大模型优势 | §4.3 + Figure 3 题注 |
| ViT-Base 规模 | 12 层 / D=768 / MLP 3072 / 12 头 / **86M** 参数 | Table 1 |

**第 4 行是全文真正的核心证据**，但要注意：原文用的是散点图（Figure 3），**没有给出对应的表格数值**。所以这一条只能作定性引用，不要写成"某数据集上差 X 个点"。

## 三个疑点

| # | 疑点 | 属于 |
|---|---|---|
| 1 | **主结论依赖未公开数据**：最强结果用 JFT-300M（303M 图，未公开）。公开可复现的版本是 ImageNet-21k（14M 图，Table 2 中 ViT-L/16 为 85.30），与 88.55 差 3.25 个点。复现时对不齐主结果 | 问题（可复现性受限） |
| 2 | **"为什么需要大数据"只给了假说**：论文解释为"fewer inductive biases for vision than ResNets"（§4.3），但没有实验区分"归纳偏置缺失必须由数据补偿"和"训练策略/正则化没调好"这两种解释 | Gap（该做没做） |
| 3 | **2D 位置编码的对比在附录**：正文只说"we have not observed significant performance gains from using more advanced 2D-aware position embeddings"，证据放在 Appendix D.4。速读时容易误判为"没做过对比" | 问题（结论前置、证据后置） |

> 另外记一笔做对了的地方：论文**明确声明**了预训练数据与下游测试集的去重——"We de-duplicate the pre-training datasets w.r.t. the test sets of the downstream tasks"（§4.1）。这是数据泄漏审计里最容易被跳过的一步，多数论文不写。见 `references/06-leakage-audit.md` 问 3。

## 值不值得读

**结论**：读 §3.1（方法）+ §4.3（数据需求）+ Figure 3，其余跳读。

**理由**：方法本身十分钟能讲完；真正有迁移价值的是"换掉架构问法"这件事——它不问"哪个架构更好"，而问"在给定数据预算下哪个架构更好"。如果你的主线涉及归纳偏置与数据量的权衡，这篇的论证结构可以直接借。

---

## 建议档位

| 若你想… | 建议 |
|---|---|
| 只想知道 ViT 是什么 | **到此为止** |
| 要把 patch embedding 或位置编码搬进自己的模型 | 升 **Standard**——需要看清 patch 维度换算，以及微调时分辨率变化如何插值位置编码（§3.2 + 附录 B.1.1） |
| 要在 ViT / CNN / 混合架构间选型 | 升 **Full**——需要把预训练数据量、算力、数据可得性拉到同一张表上比 |

**注意**：升 Standard 需要你自己读完精读稿，之后才做八节总结。速读卡不能替代阅读。
