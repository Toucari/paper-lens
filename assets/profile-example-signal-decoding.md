# Profile 样例：脑信号解码 / 神经基础模型

> 这是一份**样例**，演示 profile 该写多具体。其中的领域内容不代表使用者本人。
> 用 `assets/profile-template.md` 生成自己的 profile，不要照抄这份。

---

## research

- **方向**：用深度学习从脑信号（EEG / MEG / fMRI）解码语言与语义，以及跨被试的迁移
- **关键词**：EEG-to-text、brain foundation model、cross-subject transfer
- **主线问题**：在目标被试**没有标注数据**的条件下，如何把源被试上学到的表征迁移过去并保住解码性能

## venues

- **accept**：NeurIPS, ICLR, ICML, CVPR, AAAI, ACL, IJCAI, MICCAI
- **accept_journal**：TPAMI, TNNLS, TMI, MIA, IJCV
- **reject**：workshop, findings, challenge, competition, symposium

> 这里列的是一份**示例白名单**。实际该收哪些场子取决于你的毕业/考核要求，
> 请按自己的情况填——白名单写错，找论文时会把不认的场子当成目标。

## paths

- **root**：`D:/papers`
- **topic_grouping**：`["brain-foundation", "eeg-to-text", "cross-subject"]`

## preferences

- **language**：zh
- **date_format**："%Y-%m-%d"
- **figure_scale**：4
- **quick_card_first**：true

---

## 这份 profile 会怎么影响产物

| 字段 | 影响 |
|---|---|
| `主线问题` | 八节 §七（有价值的点）会围绕"能否用于跨被试无标注迁移"来写，而不是泛泛列优点 |
| `accept` | 找论文时只收白名单内的场子，`Findings` / workshop 一律不进 |
| `topic_grouping` | 论文落到 `papers/<venue year>/<topic>/<title>/`，主题由你按需改 |
| `figure_scale: 4` | 脑信号论文的子图常有多通道小字，3 倍会糊 |
