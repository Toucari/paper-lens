# Profile

> 复制本文件到 `$PL_ROOT/profile.md` 后修改。这里只写"你自己的情况"，不要写流程。

## research

- **方向**：<一句话，例：生理信号到文本的解码 / 脑基础模型>
- **关键词**：<3 个，找论文时用来扩召回>
- **主线问题**：<你正在解决、并希望这些论文能帮上的那个问题。写具体一句，例：跨被试条件下如何在没有目标被试标注数据时保持解码性能>

> `主线问题` 决定八节总结 §七（有价值的点）和 §五（与我的关系）写得实不实。
> 留空的话这两节只能是套话。

## venues

- **accept**（会议）：<例：NeurIPS, ICLR, ICML, CVPR, AAAI, ACL>
- **accept_journal**（期刊）：<例：TPAMI, TNNLS, TMI>
- **reject**：workshop, findings, challenge, competition, symposium

> 白名单之外的场子不主动推荐，但可以在轮次导航里记为"相关但不在范围"。

## paths

- **root**：<论文库绝对路径，例：D:/papers>
- **topic_grouping**：<若要按主题分层，填子目录名；否则留空 `[]`>

> `topic_grouping` 的例子：`["brain-foundation", "eeg-to-text", "cross-subject"]`
> 填了之后论文会落到 `papers/<venue year>/<topic>/<title>/`，不填就平铺。

## preferences

- **language**：zh
- **date_format**："%Y-%m-%d"
- **figure_scale**：4
- **quick_card_first**：true

> `figure_scale` 是抽图倍数。密集图（多子图、小字）用 4–5；普通图 3 够。
> `quick_card_first`：看完一篇的速读卡后，是否询问是否升档。

## scoring

> **可选段**。不填就用默认六维权重（创新 15 / 实证 25 / 复现 15 / 搬运 20 / 诚实 10 / 训练开销 15）。
> 这是**唯一允许覆盖框架默认值的地方**——改这里不动仓库文件，升级也不会丢。

- **weights**：`{novelty: 15, evidence: 25, repro: 15, reuse: 20, honesty: 10, cost: 15}`

> 六项**必须加总 100**。改了权重等于换口径版本，必须：
> ① 在 `ledger/changelog.md` 记一条；② 跑一次 `05-evaluate.md` 第 4 步的历史重算判断；③ 新旧分数不可混排。
> 若你的领域完全用不上某一维（例如纯理论论文没有训练开销），**不要把它权重设 0**——那会让该维的缺失变成免费得分。正确做法是留空记 `N/A`，按剩余维度归一化。
