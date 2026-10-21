# 00 · 首次配置

只在**第一次使用**时走一遍。配置写进 `$PL_ROOT/profile.md`，之后每次开始前读它。

**没有 profile 就先问，不要默认按别人的配置跑。**

---

## 一、需要问清的四件事

用一次简短的问答收集，不要逐条盘问：

| # | 问什么 | 为什么要 |
|---|---|---|
| 1 | **研究方向和 2–3 个关键词** | 决定"与你的关系"这一项怎么算、找论文往哪搜 |
| 2 | **关心哪些会议/期刊** | 决定找论文时接受什么、拒绝什么 |
| 3 | **论文库放在哪个目录** | 决定 `PL_ROOT` |
| 4 | **要不要按主题再分一层子目录** | 论文多了之后平铺会很难找 |

如果用户已有的目录结构（比如已经按 venue 分好了），**照它现有的来**，不要重排。适配现状比统一规范更重要。

---

## 二、生成 profile.md

用 `assets/profile-template.md` 复制一份到 `$PL_ROOT/profile.md`，填好。

最小可用配置只需要三段：`research`、`venues`、`paths`。其余可留空。

```markdown
# Profile

## research
- 方向：<一句话>
- 关键词：<3 个>
- 主线问题：<你正在解决的、这篇论文能帮上的那个问题>

## venues
- accept: <会议列表>
- accept_journal: <期刊列表>
- reject: workshop / findings / challenge / symposium

## paths
- root: <PL_ROOT 绝对路径>
- topic_grouping: []        # 若要分组，填子目录名列表

## preferences
- language: zh              # 产物语言
- date_format: "%Y-%m-%d"
```

### 字段说明

| 字段 | 作用 | 不填会怎样 |
|---|---|---|
| `research.主线问题` | 写"与我的关系"和"有价值的点"时的锚 | 只能给泛泛的价值判断 |
| `venues.accept` | 找论文时的白名单 | 会推荐到不在范围内的场子 |
| `paths.root` | 所有产物的落点 | 无法运行 |
| `paths.topic_grouping` | `papers/` 下的二级分组 | 平铺，论文多了自己找不到 |
| `preferences.language` | 产物语言 | 默认中文 |

---

## 三、初始化库目录

```bash
python scripts/plens.py init --root "<PL_ROOT>"
```

会建出：

```
<PL_ROOT>/
├── papers/
├── rounds/
└── ledger/
    ├── registry.md          ← 空表头 + 字段说明
    ├── case-library.md      ← 空表头 + 字段说明
    └── changelog.md         ← 框架变更记录
```

**已有的库不要重跑 `init`**，它只补缺失的文件，不覆盖已有内容。但保险起见，先确认 `ledger/` 里的文件是否已存在。

---

## 四、检查依赖

```bash
python -c "import pymupdf; print('pymupdf', pymupdf.__version__)"
python -c "import pypdf;   print('pypdf', pypdf.__version__)"
```

- 两个都有 → 最好
- 只有 pypdf → 能抽文本，**抽不了图**
- 都没有 → `pip install pymupdf`

---

## 五、配置完成后的自检

跑一遍最小链路，确认能用：

```bash
# 1. 抽文本（拿任意一篇已有 PDF 试）
python scripts/plens.py text paper.pdf -o _test.txt
wc -l _test.txt

# 2. 捞标题
python scripts/plens.py toc paper.pdf

# 3. 抽图
python scripts/plens.py figures paper.pdf -o _test_figs/

# 4. 看结果
ls _test_figs/
```

四步都过，配置就算完成。清理 `_test*`，然后从 Quick 档开始用。

---

## 六、常见配置错误

| 错误 | 症状 | 修法 |
|---|---|---|
| `paths.root` 写成 skill 目录 | 产物混进仓库，被 git 追踪 | 改成论文库目录 |
| 用了相对路径 | 换个工作目录就找不到 | 一律绝对路径 |
| `venues.accept` 写成小写 | 匹配不上 | 保持论文里的正规写法（`NeurIPS` 不是 `neurips`） |
| 没写 `主线问题` | 八节总结的 §七 全是空话 | 补一句话 |
| 已有库重跑 `init` | 可能覆盖空模板 | 先看 `ledger/` 有无内容 |
