# -*- coding: utf-8 -*-
from collections import deque
from QuModLibs.Server import *

""" 初学测试：手持钻石攻击生物原地复制
@Listen(Events.PlayerAttackEntityEvent)
def test(args):
    playerId = args["playerId"]
    victimId = args["victimId"]

    comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
    itemDict = comp.GetPlayerItem(2, 0)
    if itemDict["newItemName"] == "minecraft:diamond":
        identifier = Entity(victimId).Identifier
        Entity.CreateEngineEntityByTypeStr(identifier, Entity(victimId).Pos, (0, 0), Entity(victimId).DimensionId)
"""

SPECIES = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak")
NETHER_STEMS = ("crimson", "warped")

LOGS = tuple(
    "minecraft:%s%s_%s" % (prefix, s, part)
    for s in SPECIES for prefix in ("", "stripped_") for part in ("log", "wood")
) + tuple(
    "minecraft:%s%s_%s" % (prefix, s, part)
    for s in NETHER_STEMS for prefix in ("", "stripped_") for part in ("stem", "hyphae")
) + (
    "minecraft:log", "minecraft:log2",
    "minecraft:bamboo_block", "minecraft:stripped_bamboo_block",
    "minecraft:mangrove_roots", "minecraft:muddy_mangrove_roots",
)
LEAVES = tuple("minecraft:%s_leaves" % s for s in SPECIES) + (
    "minecraft:leaves", "minecraft:leaves2",
    "minecraft:azalea_leaves", "minecraft:azalea_leaves_flowered",
    "minecraft:flowering_azalea_leaves", "minecraft:leaves_flowered",
    "minecraft:nether_wart_block", "minecraft:warped_wart_block",
)
DIRECTIONS = ((0,0,-1), (0,0,1), (-1,0,0), (1,0,0), (0,1,0), (0,-1,0))
CREATIVE = 1  # serverApi.GetMinecraftEnum().GameType.Creative
COST_TIERS = ((10, 10), (10, 7), (20, 4), (None, 2))  # (该段原木数, 系数×10)；None = 剩下全部
# 按「最大耐久」分档，不认物品ID：木(60)/石(132)/金(33) 走 1:1；铁(251) 走梯度；钻(1562)/合金(2032) 再 5 折
GRADED_MIN_DURABILITY = 200
HALF_COST_MIN_DURABILITY = 1000

STRICT_TREE = True    # False: 跳过邻居成分判定（仍受空间边界与最小限制约束）
NEIGHBOR_RULE = True  # False: 不做「原木贴人工方块 = 建筑」判定
FOREIGN_LIMIT = 3     # 累计几个「人工方块」才否决；森林里连片原木样本多，一票否决必然误伤
LIMIT_CHECK = False   # True: 额外启用保守数量兜底（简化版回退，默认关）
MIN_LOGS = 2          # 最小限制：防单根装饰柱
MIN_LEAVES = 1        # 最小限制：至少要有一片树叶
MAX_LOGS = 48         # 以下四个仅 LIMIT_CHECK=True 时生效，默认不参与判定
MAX_LEAVES = 512
MAX_SPAN = 3
MIN_CANOPY = 6

# ponytail: 只写比默认大的例外；R 取扫到树种的最大值，免得邻树云杉把整片林子压到 4
CANOPY_R = {"mangrove": 8, "cherry": 8}
DEFAULT_CANOPY_R = 6
CANOPY_Y_BELOW = 2    # 从最低原木往下几格；不再用 topY-6，否则矮树树冠会被邻树挤出窗口
CANOPY_Y_ABOVE = 2
SCAN_Y_DOWN = 4
SCAN_Y_UP = 48        # 原木 BFS 的 y 边界，防密集森林沿斜干把整片地形扫穿
SCAN_LIMIT = 6000     # 单次最多查多少个方块；连片森林防事件超时，超出按已收部分砍
DIAG_DIRS = tuple(
    (dx, dy, dz)
    for dy in (1, -1) for dx in (-1, 0, 1) for dz in (-1, 0, 1)
    if (dx, dz) != (0, 0)
)  # 16 个斜上/斜下，只用来连斜干，不参与成分判定

GROUND = frozenset((
    "minecraft:dirt", "minecraft:grass_block", "minecraft:grass", "minecraft:podzol",
    "minecraft:mycelium", "minecraft:coarse_dirt", "minecraft:rooted_dirt",
    "minecraft:sand", "minecraft:gravel", "minecraft:clay",
    "minecraft:stone", "minecraft:andesite", "minecraft:diorite", "minecraft:granite",
    "minecraft:tuff", "minecraft:deepslate", "minecraft:snow", "minecraft:ice",
    "minecraft:water", "minecraft:netherrack", "minecraft:soul_sand",
    "minecraft:soul_soil", "minecraft:crimson_nylium", "minecraft:warped_nylium",
))
ATTACHMENTS = frozenset("minecraft:%s_sapling" % s for s in SPECIES) | frozenset((
    "minecraft:vine", "minecraft:glow_lichen", "minecraft:moss_block",
    "minecraft:bee_nest", "minecraft:cocoa", "minecraft:shroomlight",
    "minecraft:twisting_vines", "minecraft:weeping_vines",
    "minecraft:red_mushroom", "minecraft:brown_mushroom",
    "minecraft:poppy", "minecraft:dandelion", "minecraft:tallgrass", "minecraft:fern",
))
NATURAL_BLOCKS = GROUND | ATTACHMENTS
ALLOWED_NEIGHBORS = frozenset(LOGS + LEAVES + ("minecraft:air",)) | NATURAL_BLOCKS
# ponytail: 词根放行代替逐个列方块名；基岩版自然方块太多，漏列一个就否决整棵树
# 已知误放行：stone_bricks / smooth_stone / 石台阶等石制品，按需求接受这部分误杀
NATURAL_HINTS = (
    "air", "leaves", "log", "wood", "stem", "hyphae", "root", "propagule",
    "sapling", "flower", "grass", "fern", "mushroom", "vine", "lichen",
    "moss", "snow", "ice", "water", "dirt", "sand", "gravel", "clay",
    "stone", "tuff", "deepslate", "andesite", "diorite", "granite",
    "nylium", "netherrack", "soul", "crimson", "warped", "terracotta",
    "bamboo", "cactus", "bush", "plant", "coral", "kelp", "seagrass",
    "lily", "spore", "cocoa", "bee", "web", "azalea", "bedrock",
    "farmland", "double_plant", "lilac", "sprout", "podzol", "mycelium",
)
SPECIES_BY_LEN = tuple(sorted(SPECIES + NETHER_STEMS, key=len, reverse=True))


def isNatural(name):
    if name in ALLOWED_NEIGHBORS:
        return True
    n = name.replace("minecraft:", "")
    return any(h in n for h in NATURAL_HINTS)


def speciesOf(name):
    # ponytail: 按长度降序，否则 dark_oak 会先被 oak 匹配；无树种名返回 None
    n = name.replace("minecraft:", "").replace("stripped_", "")
    for s in SPECIES_BY_LEN:
        if n.startswith(s + "_"):
            return s
    return None


def carriedPos():
    return serverApi.GetMinecraftEnum().ItemPosType.CARRIED


def isAxeInfo(info):
    return bool(info and info.get("itemType") == "axe")


def isAxe(carried):
    """按物品类别认斧，不认ID；其它mod的斧只要 itemType=axe 就能触发"""
    name = carried.get("newItemName") if carried else None
    if not name:
        return False
    # ponytail: 用 levelId 建组件，与官方 GetItemBasicInfo 示例一致
    info = serverApi.GetEngineCompFactory().CreateItem(levelId).GetItemBasicInfo(name)
    return isAxeInfo(info)


def durabilityCost(logCount, maxDurability):
    """按斧头最大耐久分档：<阈值 严格1:1；中间 分段累进；≥高级阈值 累进后再 5 折"""
    if maxDurability < GRADED_MIN_DURABILITY:
        return logCount
    tenths = 0
    for size, rate10 in COST_TIERS:
        n = logCount if size is None else min(logCount, size)
        tenths += n * rate10
        logCount -= n
        if logCount <= 0:
            break
    cost = (tenths + 9) // 10
    if maxDurability >= HALF_COST_MIN_DURABILITY:
        cost = (cost + 1) // 2  # ponytail: 向上取整，保证再打折也至少扣 1 点
    return cost


def collect_tree(x, y, z, dm):
    """沿原木/树叶收本树；人工方块累计到阈值才否决；空间边界只截断不整批放弃"""
    blockComp = serverApi.GetEngineCompFactory().CreateBlockInfo(levelId)
    # ponytail: 起点已被挖成空气，它的 6 邻居既是原木 BFS 起点，也是成分判定样本
    # ponytail: key 带 checkSide，斜向先到的格子不能吃掉 6 面成分判定样本
    scanLo, scanHi = y - SCAN_Y_DOWN, y + SCAN_Y_UP
    cache = {}

    def nameAt(pos):
        # ponytail: 每格只查一次；(pos, checkSide) 双键去重会让同一格被查两遍
        if pos not in cache:
            bd = blockComp.GetBlockNew(pos, dm)
            cache[pos] = bd["name"] if bd else None
        return cache[pos]

    visited = set()
    queue = deque(((x+dx, y+dy, z+dz), True) for dx, dy, dz in DIRECTIONS)
    logNames, leafNames, seeds = {}, {}, {}
    foreign = set()
    R = DEFAULT_CANOPY_R
    while queue:
        pos, checkSide = queue.popleft()
        key = (pos, checkSide)
        if key in visited:
            continue
        visited.add(key)
        if not (scanLo <= pos[1] <= scanHi):
            continue
        name = nameAt(pos)
        if name is None:
            continue
        if len(cache) >= SCAN_LIMIT:
            break
        if name in LOGS:
            # ponytail: 取最大值不取首值，森林里先扫到云杉不该把整片林子压到 R=4
            R = max(R, CANOPY_R.get(speciesOf(name), DEFAULT_CANOPY_R))
            logNames[pos] = name
            for dx, dy, dz in DIRECTIONS:
                np = (pos[0]+dx, pos[1]+dy, pos[2]+dz)
                if max(abs(np[0]-x), abs(np[2]-z)) > R:
                    continue
                queue.append((np, True))   # 6 面：既连原木，也参与成分判定
            for dx, dy, dz in DIAG_DIRS:
                np = (pos[0]+dx, pos[1]+dy, pos[2]+dz)
                if max(abs(np[0]-x), abs(np[2]-z)) > R:
                    continue
                queue.append((np, False))  # 斜向：只连斜干，不判成分
        elif name in LEAVES:
            if checkSide:
                seeds[pos] = name
        elif checkSide and not isNatural(name):
            foreign.add(pos)
    if len(logNames) < MIN_LOGS:
        return []
    if STRICT_TREE and NEIGHBOR_RULE and len(foreign) >= FOREIGN_LIMIT:
        return []

    # ponytail: 下界取最低原木；森林里邻树把 topY 拉高时，topY-6 会把矮树树冠整批过滤掉
    minY = min(p[1] for p in logNames)
    topY = max(p[1] for p in logNames)
    yLo, yHi = minY - CANOPY_Y_BELOW, topY + CANOPY_Y_ABOVE
    # ponytail: 空间边界只跳过越界格，不整批放弃；连片树冠沿窗口自然切断
    q2 = deque((p, n) for p, n in seeds.items()
               if max(abs(p[0]-x), abs(p[2]-z)) <= R and yLo <= p[1] <= yHi)
    leafSeen = {p for p, _ in q2}
    while q2:
        if len(cache) >= SCAN_LIMIT:
            break
        pos, name = q2.popleft()
        leafNames[pos] = name
        for dx, dy, dz in DIRECTIONS:
            np = (pos[0]+dx, pos[1]+dy, pos[2]+dz)
            if np in leafSeen:
                continue
            if max(abs(np[0]-x), abs(np[2]-z)) > R or not (yLo <= np[1] <= yHi):
                continue
            leafSeen.add(np)
            nm = nameAt(np)
            if nm in LEAVES:
                q2.append((np, nm))  # 外部原木/其它方块一律当边界
    if len(leafNames) < MIN_LEAVES:
        return []

    # ponytail: 简化版保守回退，默认关；不参与「是不是树」的判定
    if LIMIT_CHECK and (
        len(logNames) > MAX_LOGS or len(leafNames) > MAX_LEAVES
        or len(leafNames) < MIN_CANOPY
        or max(p[0] for p in logNames) - min(p[0] for p in logNames) + 1 > MAX_SPAN
        or max(p[2] for p in logNames) - min(p[2] for p in logNames) + 1 > MAX_SPAN
    ):
        return []
    return [(p, n) for p, n in logNames.items()] + [(p, n) for p, n in leafNames.items()]


def destroy_tree(targets, dm, playerId, creative):
    blockComp = serverApi.GetEngineCompFactory().CreateBlockInfo(levelId)
    if not creative:
        # 只按实际砍掉的原木数计费，树叶不再单独扣耐久
        logCount = sum(1 for _, name in targets if name in LOGS)
        posType = carriedPos()
        itemComp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        carried = itemComp.GetPlayerItem(posType, 0)
        if not isAxe(carried):
            return
        durability = itemComp.GetItemDurability(posType, 0)
        # ponytail: 留最后 1 点耐久，不模拟工具损毁；不够付全款就扣光能扣的，树照砍完
        if durability <= 1:
            return
        # ponytail: isUserData=False → 先读单件自定义值、没有再读该类通用值，兼容其它mod；取不到就回退旧梯度
        maxDurability = itemComp.GetItemMaxDurability(posType, 0, False) or GRADED_MIN_DURABILITY
        cost = min(durabilityCost(logCount, maxDurability), durability - 1)
        if not itemComp.SetItemDurability(posType, 0, durability - cost):
            return
    for pos, _ in targets:
        blockComp.SetBlockNew(pos, {'name': 'minecraft:air'}, 1, dm, True)


@Listen(Events.DestroyBlockEvent)
def fallingTree(args):
    x = args["x"]
    y = args["y"]
    z = args["z"]
    playerId = args["playerId"]
    fullName = args["fullName"]
    dm = args["dimensionId"]

    if fullName not in LOGS:
        return

    # ponytail: 潜行时只保留引擎原生砍掉的那一格，不启动连锁
    if serverApi.GetEngineCompFactory().CreatePlayer(playerId).isSneaking():
        return

    posType = carriedPos()
    comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
    carried = comp.GetPlayerItem(posType, 0)
    if not isAxe(carried):
        return

    creative = serverApi.GetEngineCompFactory().CreateGame(levelId).GetPlayerGameType(playerId) == CREATIVE
    targets = collect_tree(x, y, z, dm)
    if not targets:
        return
    destroy_tree(targets, dm, playerId, creative)


if __name__ == "__main__":
    WOOD, IRON, DIAMOND = 60, 251, 1562  # 原版斧最大耐久（石 132 / 金 33 同 WOOD 档）
    assert [durabilityCost(n, IRON) for n in (1, 10, 11, 20, 21, 40, 41, 50)] == [1, 10, 11, 17, 18, 25, 26, 27]
    costs = [durabilityCost(n, IRON) for n in range(1, 101)]
    assert all(a <= b for a, b in zip(costs, costs[1:]))  # 累进必须单调不减
    assert [durabilityCost(n, WOOD) for n in (1, 10, 40)] == [1, 10, 40]             # 木/石：严格 1:1
    assert [durabilityCost(n, DIAMOND) for n in (1, 10, 20, 40)] == [1, 5, 9, 13]    # 钻石：梯度 5 折
    assert all(durabilityCost(n, DIAMOND) <= durabilityCost(n, IRON) <= durabilityCost(n, WOOD)
               for n in range(1, 101))  # 越贵越耐用
    assert "minecraft:pale_oak_log" in LOGS and "minecraft:pale_oak_leaves" in LEAVES
    assert isAxeInfo({"itemType": "axe"}) and not isAxeInfo({"itemType": "pickaxe"}) and not isAxeInfo(None)
    for n in ("minecraft:cave_air", "minecraft:packed_ice", "minecraft:mangrove_propagule",
              "minecraft:flowering_azalea_leaves", "minecraft:cobweb", "minecraft:farmland"):
        assert isNatural(n), n
    for n in ("minecraft:oak_planks", "minecraft:chest", "minecraft:crafting_table"):
        assert not isNatural(n), n
