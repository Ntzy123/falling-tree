# -*- coding: utf-8 -*-
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


def check_tree(x,y,z,dm,fullName,direction=None,secondary_direction=None):
    # 初始化
    leaves = ["minecraft:oak_leaves", "minecraft:spruce_leaves", "minecraft:birch_leaves", "minecraft:jungle_leaves", "minecraft:acacia_leaves", "minecraft:dark_oak_leaves", "minecraft:mangrove_leaves", "minecraft:cherry_leaves"]
    is_tree = False

    # 判断方向
    if direction == "forward":
        z-=1
    elif direction == "backward":
        z+=1
    elif direction == "left":
        x-=1
    elif direction == "right":
        x+=1
    elif direction == "up":
        y+=1
    else:
        if secondary_direction != "backward": is_tree = check_tree(x,y,z,dm,fullName,"forward","forward")
        if is_tree: return True
        if secondary_direction != "forward": is_tree = check_tree(x,y,z,dm,fullName,"backward","backward")
        if is_tree: return True
        if direction != "right": is_tree = check_tree(x,y,z,dm,fullName,"left",secondary_direction)
        if is_tree: return True
        if direction != "left": is_tree = check_tree(x,y,z,dm,fullName,"right",secondary_direction)
        if is_tree: return True
        is_tree = check_tree(x,y,z,dm,fullName,"up",None)
        if is_tree: return True

    # 获取方块信息，判断是否是原木或树叶
    comp = serverApi.GetEngineCompFactory().CreateBlockInfo(levelId)
    blockDict = comp.GetBlockNew((x, y, z), dm)
    name = blockDict["name"]

    if name in leaves:
        return True
    
    if name == fullName or name in leaves:
        if secondary_direction != "backward": is_tree = check_tree(x,y,z,dm,fullName,"forward","forward")
        if is_tree: return True
        if secondary_direction != "forward": is_tree = check_tree(x,y,z,dm,fullName,"backward","backward")
        if is_tree: return True
        if direction != "right": is_tree = check_tree(x,y,z,dm,fullName,"left",secondary_direction)
        if is_tree: return True
        if direction != "left": is_tree = check_tree(x,y,z,dm,fullName,"right",secondary_direction)
        if is_tree: return True
        is_tree = check_tree(x,y,z,dm,fullName,"up",None)
        if is_tree: return True
    return False

def check_another_tree(x,y,z,dm,fullName,direction=None,secondary_direction=None,tertiary_direction=None,leave_num = 0):
    # 初始化
    logs = ["minecraft:oak_log", "minecraft:spruce_log", "minecraft:birch_log", "minecraft:jungle_log", "minecraft:acacia_log", "minecraft:dark_oak_log", "minecraft:mangrove_log", "minecraft:cherry_log"]
    leaves = ["minecraft:oak_leaves", "minecraft:spruce_leaves", "minecraft:birch_leaves", "minecraft:jungle_leaves", "minecraft:acacia_leaves", "minecraft:dark_oak_leaves", "minecraft:mangrove_leaves", "minecraft:cherry_leaves"]
    another_tree = False

    # 判断方向
    if direction == "forward":
        z-=1
    elif direction == "backward":
        z+=1
    elif direction == "left":
        x-=1
    elif direction == "right":
        x+=1
    elif direction == "up":
        y+=1
    else:
        if secondary_direction != "backward": another_tree = check_another_tree(x,y,z,dm,fullName,"forward","forward",tertiary_direction,0)
        if another_tree: return True
        if secondary_direction != "forward": another_tree = check_another_tree(x,y,z,dm,fullName,"backward","backward",tertiary_direction,0)
        if another_tree: return True
        if tertiary_direction != "right": another_tree = check_another_tree(x,y,z,dm,fullName,"left",secondary_direction,"left",0)
        if another_tree: return True
        if tertiary_direction != "left": another_tree = check_another_tree(x,y,z,dm,fullName,"right",secondary_direction,"right",0)
        if another_tree: return True
        if direction == None or direction == "up": another_tree = check_another_tree(x,y,z,dm,fullName,"up",None,None,0)
        if another_tree: return True

    # 获取方块信息，判断是否是原木或树叶
    comp = serverApi.GetEngineCompFactory().CreateBlockInfo(levelId)
    blockDict = comp.GetBlockNew((x, y, z), dm)
    name = blockDict["name"]

    if name in leaves:
        leave_num += 1
    elif name in logs and leave_num > 2:
        return True
    elif name == fullName:
        pass
    else: return False
      
    if secondary_direction != "backward": another_tree = check_another_tree(x,y,z,dm,fullName,"forward","forward",tertiary_direction,leave_num)
    if another_tree: return True
    if secondary_direction != "forward": another_tree = check_another_tree(x,y,z,dm,fullName,"backward","backward",tertiary_direction,leave_num)
    if another_tree: return True
    if tertiary_direction != "right": another_tree = check_another_tree(x,y,z,dm,fullName,"left",secondary_direction,"left",leave_num)
    if another_tree: return True
    if tertiary_direction != "left": another_tree = check_another_tree(x,y,z,dm,fullName,"right",secondary_direction,"left",leave_num)
    if another_tree: return True
    if direction == None or direction == "up": another_tree = check_another_tree(x,y,z,dm,fullName,"up",None,0)
    if another_tree: return True
    return False

def destroy_tree(x,y,z,dm,fullName,direction,another_tree,playerId):
    # 初始化
    leaves = ["minecraft:oak_leaves", "minecraft:spruce_leaves", "minecraft:birch_leaves", "minecraft:jungle_leaves", "minecraft:acacia_leaves", "minecraft:dark_oak_leaves", "minecraft:mangrove_leaves", "minecraft:cherry_leaves"]
    
    # 判断方向
    if direction == "forward":
        z-=1
    elif direction == "backward":
        z+=1
    elif direction == "left":
        x-=1
    elif direction == "right":
        x+=1
    elif direction == "up":
        y+=1
    else:
        destroy_tree(x,y,z,dm,fullName,"forward",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"backward",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"left",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"right",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"up",another_tree,playerId)

    # 获取方块信息，判断是否是原木或树叶
    comp = serverApi.GetEngineCompFactory().CreateBlockInfo(levelId)
    blockDict = comp.GetBlockNew((x, y, z), dm)
    name = blockDict["name"]

    # 判断手上斧头耐久度
    axe = ["minecraft:wooden_axe", "minecraft:stone_axe", "minecraft:iron_axe", "minecraft:golden_axe", "minecraft:diamond_axe", "minecraft:netherite_axe"]
    axe_comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
    carried = axe_comp.GetPlayerItem(2, 0)["newItemName"]
    if carried in axe:
        durability = axe_comp.GetItemDurability(2, 1)
        if durability >= 1:
            axe_comp.SetItemDurability(serverApi.GetMinecraftEnum().ItemPosType.INVENTORY, 0, durability-1)
        else: return

    else: return

    # 判断是否需要移除树叶
    if another_tree:
        leaves = []

    # 清除
    if name in leaves or name == fullName:
        destroyTreeBlock(x,y,z,dm)
        destroy_tree(x,y,z,dm,fullName,"forward",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"backward",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"left",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"right",another_tree,playerId)
        destroy_tree(x,y,z,dm,fullName,"up",another_tree,playerId)


def destroyTreeBlock(x,y,z,dm):
    comp = serverApi.GetEngineCompFactory().CreateBlockState(levelId)
    auxValue = comp.GetBlockAuxValueFromStates("minecraft:air",{})

    airBlockDict = {
        'name': 'minecraft:air',
            'aux': auxValue
    }
    comp = serverApi.GetEngineCompFactory().CreateBlockInfo(levelId)
    comp.SetBlockNew((x, y, z), airBlockDict, 1, dm, True)

@Listen(Events.DestroyBlockEvent)
def fallingTree(args):
    # 初始化信息
    x = args["x"]
    y = args["y"]
    z = args["z"]
    playerId = args["playerId"]
    fullName = args["fullName"]
    dm = args["dimensionId"]
    logs = ["minecraft:oak_log", "minecraft:spruce_log", "minecraft:birch_log", "minecraft:jungle_log", "minecraft:acacia_log", "minecraft:dark_oak_log", "minecraft:mangrove_log", "minecraft:cherry_log"]
    axe = ["minecraft:wooden_axe", "minecraft:stone_axe", "minecraft:iron_axe", "minecraft:golden_axe", "minecraft:diamond_axe", "minecraft:netherite_axe"]

    # 判断玩家手持是否为斧头
    comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
    carried = comp.GetPlayerItem(2, 0)["newItemName"]
    if not carried in axe:
        return

    if fullName in logs:        
        is_tree = check_tree(x,y,z,dm,fullName,0)
        if is_tree:
            another_tree = check_another_tree(x,y,z,dm,fullName)
            print(another_tree)
            destroy_tree(x,y,z,dm,fullName,0,another_tree,playerId)