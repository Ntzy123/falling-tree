# falling-tree

网易我的世界基岩版（MC Studio / ModAPI）连锁砍树 Mod：手持斧头砍掉一格原木，整棵树连同树叶一起倒下，并按实际砍掉的原木数扣斧头耐久。

## 工程结构

| 路径 | 作用 |
|---|---|
| `Af5eeab8d38434d5a81e891a128b78637B/` | 行为包（脚本） |
| `.../FallingTree_Scripts/modMain.py` | 入口，`EasyMod()` 注册 `Server` / `Client` |
| `.../FallingTree_Scripts/Server.py` | **全部砍树逻辑**，唯一业务文件 |
| `.../FallingTree_Scripts/Client.py` | 客户端，空壳 |
| `.../FallingTree_Scripts/QuModLibs/` | 框架库，非本 Mod 代码 |
| `Af5eeab8d38434d5a81e891a128b78637R/` | 资源包（`textures`），当前无自定义资源 |
| `studio.json` | MC Studio 工程元数据 |

两个 manifest 互相依赖，均为 `version 1.0.0`、`min_engine_version 1.18.0`：

- 行为包 `1be4f3b9-2796-4a2b-93e3-9a3587c3f10a`（`type: data`，依赖资源包）
- 资源包 `39e4aa60-38d1-4c2d-88ef-629132448495`（`type: resources`，依赖行为包）
- 两处 `header.name` / `description` 为空，发布前需填写

## 触发链路

`DestroyBlockEvent` → `fallingTree()` → `collect_tree()` → `destroy_tree()`

入口硬条件（任一不满足即结束，方块已经被玩家砍掉）：

1. 被破坏方块的 `fullName` 命中 `LOGS`（放在最前，非原木不查任何物品/玩家信息）。
2. 玩家**未处于潜行状态**（`CreatePlayer(playerId).isSneaking()`）；潜行时只砍掉手上一格，不启动连锁。
3. 主手物品的 `itemType == "axe"`（由 `GetItemBasicInfo(...)` 查询，按类别不按 ID；其他 mod 的斧头只要在行为包里声明了 `itemType: axe` 同样可触发）；副手、其它工具不触发。
4. 非创造模式：`destroy_tree` 二次确认手斧，且剩余耐久 > 1、`SetItemDurability` 成功。创造模式整段跳过（`CREATIVE = 1` 硬编码比对 `GetPlayerGameType`）。

## 判定流程（`collect_tree`）

- 起点已变成空气，从它的 6 邻居起 BFS；原木沿 **6 面 + 16 斜上/斜下**连通，`visited` 用 `(pos, checkSide)` 双键，斜向到达的格子不吃掉 6 面成分样本。
- 方块名用 `nameAt()` 缓存（同一格只查一次），`SCAN_LIMIT` 封顶单次查询数；`SCAN_Y_DOWN/UP` 限制纵向扫描，密集森林防事件超时。
- `R` 取扫到树种的最大水平半径（切比雪夫距离，以被砍点为中心），避免邻树云杉把整片林子压小。
- 树叶种子只取「正交贴着连通原木 6 面」的树叶，再按 `R` 与 `[minY - 2, topY + 2]` 窗口连片收集；下界取最低原木，防止邻树拉高 `topY` 后矮树树冠被整批过滤。
- 否决条件：原木数 < `MIN_LOGS`、树叶数 < `MIN_LEAVES`、或累计 `FOREIGN_LIMIT` 个「人工方块」（按坐标去重）。
- `LIMIT_CHECK = False`，`MAX_LOGS` / `MAX_LEAVES` / `MAX_SPAN` / `MIN_CANOPY` 默认不参与判定。

## 方块表

- 树种 `SPECIES`：oak / spruce / birch / jungle / acacia / dark_oak / mangrove / cherry / pale_oak；下界茎 `NETHER_STEMS`：crimson / warped
- `LOGS`：各树种 `*_log`、`*_wood` 及 `stripped_*`，下界 `*_stem`、`*_hyphae`，老版 `log`/`log2`，竹子块，红树根
- `LEAVES`：各树种 `*_leaves`、老版 `leaves`/`leaves2`、杜鹃/花杜鹃叶、下界疣块
- 邻居白名单 = `LOGS + LEAVES + air + GROUND + ATTACHMENTS`；未精确命中时用 `NATURAL_HINTS` 词根模糊放行（`isNatural()`）。`oak_planks` / `chest` / `crafting_table` 等仍被判为人工方块

## 耐久计费

分档依据是**手持斧的最大耐久值**（`GetItemMaxDurability(posType, 0, False)`：先读单件 userData 自定义值，没有再读该类物品通用值），不认物品 ID，因此其他 mod 改过耐久的斧会自动落到对应档位；取不到最大耐久时回退到铁质梯度档。

| 最大耐久 | 对应材质 | 计费方式 |
|---|---|---|
| `< 200` | 金(33) / 木(60) / 石(132) | 严格 1:1，不用梯度 |
| `200 ~ 999` | 铁(251) | 分段累进（下表） |
| `≥ 1000` | 钻石(1562) / 下界合金(2032) | 分段累进后整体 ×0.5（向上取整，至少扣 1 点） |

中间档（含铁质）的分段累进，十分位整数运算后向上取整：

| 原木数 | 每根系数 |
|---|---|
| 前 10 根 | 1.0 |
| 第 11–20 根 | 0.7 |
| 第 21–40 根 | 0.4 |
| 41 根起 | 0.2 |

只按实际砍掉的原木数计费，树叶不扣；保留最后 1 点耐久（`cost = min(cost, durability - 1)`），耐久不够也照样砍完。40 根原木：木/石扣 40 点、铁扣 25 点、钻石扣 13 点。

## 可调参数（均在 `Server.py` 顶部）

| 参数 | 默认 | 作用 |
|---|---|---|
| `STRICT_TREE` / `NEIGHBOR_RULE` | `True` | 关掉任一即跳过建筑识别 |
| `FOREIGN_LIMIT` | `3` | 累计几个人工方块才否决整棵树 |
| `MIN_LOGS` / `MIN_LEAVES` | `2` / `1` | 最小原木/树叶数；注意 `MIN_LOGS` 不含刚砍掉那根 |
| `DEFAULT_CANOPY_R` / `CANOPY_R` | `6` / mangrove、cherry `8` | 水平收集半径 |
| `CANOPY_Y_BELOW` / `ABOVE` | `2` / `2` | 树冠 y 窗口相对最低/最高原木的偏移 |
| `SCAN_Y_DOWN` / `SCAN_Y_UP` | `4` / `48` | 原木 BFS 纵向边界 |
| `SCAN_LIMIT` | `6000` | 单次最多查询方块数，超出按已收部分砍 |
| `GRADED_MIN_DURABILITY` | `200` | 最大耐久 ≥ 此值才启用梯度，低于此严格 1:1 |
| `HALF_COST_MIN_DURABILITY` | `1000` | 最大耐久 ≥ 此值再打 5 折 |
| `COST_TIERS` | `(10,10),(10,7),(20,4),(None,2)` | 中间档的耐久分段（段原木数, 系数×10） |
| `LIMIT_CHECK` | `False` | 打开后启用 `MAX_*` / `MIN_CANOPY` 保守数量兜底 |
| `CREATIVE` | `1` | 与 `GetPlayerGameType` 比对，判定创造模式 |

## 已知取舍

为让交叉相连的大型森林能触发，当前**主动放宽了安全性**：

- `stone` 等词根会放行 `stone_bricks`、`smooth_stone`、石台阶等石制品；
- 连片树冠会被整片清除，斜向连通的邻树原木会一起砍（跨树误杀）；
- 贴着 ≤ 2 个人工方块的原木柱会被当成树；
- 撞到 `SCAN_LIMIT` 时树可能只倒一部分。

更宽松：把 `NEIGHBOR_RULE` 改 `False`（完全跳过建筑识别），或调大 `FOREIGN_LIMIT` / `SCAN_LIMIT`。
更保守：把 `FOREIGN_LIMIT` 调小到 `1`（等同原来的一票否决）、缩小 `DEFAULT_CANOPY_R` 与 `CANOPY_Y_*`，或打开 `LIMIT_CHECK`。

## 自检

`Server.py` 底部 `__main__` 有耐久三档计费（含累进单调性与「越贵越耐用」）、树种常量、`isNatural()` 白名单和 `isAxeInfo()` 断言，需在带 `QuModLibs` 的环境（或打桩）运行。
