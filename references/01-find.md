# 01 · 找论文、排序、归档、写轮次导航

目标：往库里增加**经过核验、真能下载、值得读**的论文，并留下一份可追溯的轮次记录。

核心判据：**按实际价值排，不按方向排。** 方向只是搜索的起点，不是排序依据。

---

## 一、先看库里已有什么

不查重就直接推荐，一定会推荐到已读过的。

```bash
find "$PL_ROOT/papers" -maxdepth 2 -type d | sort
ls "$PL_ROOT/rounds"
```

读最新一份轮次导航的**末尾**——上一轮通常会留下"下一轮候选池"，那是最好的起点。

已读论文如果被移进了 `已读/` 之类的子目录，也要认出来。

---

## 二、确认范围

批量下载前确认三件事：**方向/主题**、**新增还是补缺口**、**篇数**。

用户已经在请求里说清了就跳过，不要为了问而问。

- 用户说"精而不多 / 重在精" → 目标 **2–4 篇**真正高价值的，不要凑数。
- 用户说"尽量覆盖" → 可以放宽到 5–8 篇，但每篇都要能说清为什么选它。

---

## 三、找候选

### 搜索源（按可靠性排序）

| 源 | 用法 | 注意 |
|---|---|---|
| **arXiv API** | `https://export.arxiv.org/api/query` | **必须 https**；http 会 301 且无 `-L` 时返回空 |
| **OpenAlex** | `https://api.openalex.org` | 无限流，适合标题/语义检索与元数据补全 |
| **WebSearch** | 确认接收状态、代码仓库、"X 是不是主会" | 只作交叉验证，不单独作为录用依据 |
| 会议官网 / proceedings | 最终确认主会与年份 | 部分站点有反爬，取不到就用 arXiv comment |

### 判定"这是主会论文"

**唯一可靠的字段是 arXiv 的 `comment`**：

- 接受：`Accepted to {venue}` / `{venue} camera-ready` / `Main track`
- 拒绝：`workshop`、`Findings`、`challenge`/`competition`、`symposium`、`under review`、`submitted`、`preprint`

> `Findings of ACL/EMNLP` **不是**主会。`AAAI Spring Symposium` 不是 AAAI 主会。这两类最常被误报。

venue 白名单在 `profile.md` 的 `venues` 段。**不在白名单里的场子不要当目标**，但可以作为"相关但不在范围内"记录在轮次导航里。

### 查询写法

```bash
# 按 comment 找某会议某年的接收论文（最准）
curl -sL "https://export.arxiv.org/api/query?search_query=co:%22ICLR%202025%22&max_results=50"

# 批量核验一组 id
curl -sL "https://export.arxiv.org/api/query?id_list=2412.07236,2505.15813"
```

**arXiv 会限流**（返回 `Rate exceeded` 或 429）。请求之间留间隔；被限流就换 OpenAlex，或对已下载的 PDF 用 `plens.py text` 本地检索。

`ti:"phrase"` 不可靠，短语检索优先用 OpenAlex。

---

## 四、按价值排序

对每个候选按下面五项打分（**1–5 整数**，不必加总，用来横向比较）：

| 项 | 看什么 |
|---|---|
| **新意** | 新范式/新问题设定 vs 增量改进 |
| **实验强度** | 数据集/任务覆盖广度、是否有具体量化提升、基线是否够强 |
| **可复现** | 代码是否公开（公开 > 匿名仓库 > 无）；预训练成本是否可及 |
| **领域影响** | 是否被后续工作跟进；benchmark/reality-check 类论文此项高 |
| **与你的关系** | 与 `profile.md` 里研究方向的贴合度、能否上手复现 |

**第 5 项是软约束**：它影响优先级，但不该压过前四项。一篇方向贴合但实验稀烂的论文，价值低于一篇方向稍远但做得扎实的。

每篇都要写一句**价值理由**，这句会进轮次导航。写不出理由 = 不该选它。

---

## 五、下载 + 校验 + 归档

```bash
python <skill>/scripts/plens.py fetch 2010.11929 \
  --venue "ICLR 2021" \
  --title "An Image is Worth 16x16 Words Transformers for Image Recognition at Scale" \
  --root "$PL_ROOT"
```

脚本会：建目录 → 下载 → 校验 → 打印 `OK <路径> (<字节>)` 或 `FAIL ...`。

**每个 PDF 都要过三道校验，无例外**：

1. 头 5 字节是 `%PDF-`
2. 尾部含 `%%EOF`
3. 体积 > 10 KB

失败的文件**不要重命名成正常名冒充成功**——重下或报告。

### 下载源现状

| 源 | 状态 |
|---|---|
| `https://arxiv.org/pdf/{id}[vN]` | ✅ 可靠，返回合法 PDF（带 `-L` 跟随跳转） |
| `proceedings.neurips.cc` / `papers.nips.cc` | ⚠️ 部分地区/网络超时 |
| `openreview.net/pdf` | ⚠️ 常 403 |
| `dblp.org/search` | ⚠️ 反爬拦截 |

**没有 arXiv 版的论文无法自动下载。** 这种情况把 OpenReview / proceedings 链接交给用户人工取，并在轮次导航里标注"待人工下载"。**不要静默丢掉它**——往往是好论文。

### info.md

用 `<skill>/assets/info-template.md` 填：四列表格 + `下载源：` 行 + 可选 `代码：` 行。

必填：完整标题（保留标点）、venue 全名 + 是否主会、arXiv abs 链接、发表年月。

---

## 六、写轮次导航

每轮一份，落在 `$PL_ROOT/rounds/<日期> <主题>.md`，**永不覆盖旧轮**——新轮新建文件，或往已有文件追加一节。

必须包含：

1. **轮次头**：日期 / 方向 / 策略 / 篇数 / 状态
2. **清单**：可点击的相对路径 PDF 链接
   ```markdown
   [标题](<../papers/ICLR 2025/论文目录/2412.07236v6.pdf>)
   ```
   含空格必须用尖括号包住，否则链接断裂。
3. **建议阅读顺序** + 每篇一句价值理由
4. **排除项**：筛掉了什么、为什么（workshop？没代码？方向不符？）
5. **下一轮候选池**

---

## 七、汇报

给用户一份精简版：

| 标题 | venue | arXiv | 代码 | 一句话价值 |
|---|---|---|---|---|

外加需要人工处理的项（无 arXiv 版、需登录的源）。

---

## 八、这一步的常见错误

| 错误 | 后果 |
|---|---|
| 把 Findings / workshop 当主会 | 用户的场子要求被打穿，白读 |
| 只看方向贴合度排序 | 选进一批"对口但没价值"的论文 |
| 不查重就开始推荐 | 推荐已读过的论文，浪费一轮 |
| 下载失败后静默跳过 | 好论文被丢掉，用户不知道 |
| 用上下文日期命名 | 文件名日期错，轮次顺序混乱 |
| 覆盖旧轮次导航 | 历史记录丢失，无法追溯 |
