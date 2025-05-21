---
layout: default
title: 给ae写拓展
nav_order: 5
---



# 给ae写拓展

https://github.com/bbscncom/AeuelKeeperCard



我个人学习mod就是为了超级工厂mod 1.20 移植到1.12

然后我又给ae写了个小拓展

可以说目标驱动很明显,就是学来干活的, 甚至就是整合包玩的时候用到的

所以这里介绍的就是我给ae写拓展时整个学习过程 ,分析过程



## 分析问题

我现在的问题是保持ae接口里面的样板配方的合成的物品的数量

这个需求怎么来的呢, 因为1.12的ae分支uel的ae接口支持36个配方

现在有36种矿想要保持数量1000个怎么操作?

原版操作是发信器加合成卡,配合存储总线或者ae接口. 总之就是特麻烦

lazyae里面有一个level controller可以设置5个物品保持特定数量

现在我就想有一张升级卡可以直接插在ae接口, 直接读取ae接口的配方

然后每一个配方保持一定的数量, 这个数量就由这张升级卡右键打开一个界面设置

前面之所以介绍如何打开方块保存一个数字, 就是因为我刚刚写过这个功能, 直接就趁热拿来用罢了



## 下载mod

首先考虑那些mod可以借鉴, 自己琢磨不是可取的方法, 特别是ae这种大型mod, 里面肯定各种封装,作为一个新手肯定看不懂

比如nae2有新的内存卡, 可以借鉴如何创建内存卡

然后是lazyae, 里面有level controller可以借鉴



~~~bash
implementation rfg.deobf('curse.maven:aeuel-570458:6302098')
implementation rfg.deobf('curse.maven:nael-884359:5380800')


implementation 'curse.maven:lazyae-322347:3254160'
implementation 'curse.maven:libnine-322344:3509087'
~~~

## 物品保存数据的方法

和上一章介绍的方块保存一样, 物品保存差不多只有一些不同, 操作的是ItemStack 而不是 TileEntity



## 开始创建内存卡



首先看打开游戏看升级卡的id是啥, 然后在ae的jar包中找, 一般mod的物品分类都很好很容易找

找到发现是ItemMaterial, 这个类一看就是很多材料共用一个id, 这个类弯弯绕绕的根本看不到原版item的影子

只能找关键词speed upgrade, 发现一个getType方法, 这个方法看出升级卡是一个枚举类, 也就是说升级卡的种类是写死的

~~~java
@Override
public Upgrades getType(final ItemStack itemstack) {
    switch (this.getTypeByStack(itemstack)) {
        case CARD_CAPACITY:
            return Upgrades.CAPACITY;
        case CARD_FUZZY:
            return Upgrades.FUZZY;
        case CARD_REDSTONE:
            return Upgrades.REDSTONE;
        case CARD_SPEED:
            return Upgrades.SPEED;
        case CARD_INVERTER:
            return Upgrades.INVERTER;
        case CARD_CRAFTING:
            return Upgrades.CRAFTING;
        case CARD_PATTERN_EXPANSION:
            return Upgrades.PATTERN_EXPANSION;
        case CARD_MAGNET:
            return Upgrades.MAGNET;
        case CARD_QUANTUM_LINK:
            return Upgrades.QUANTUM_LINK;
        case CARD_STICKY:
            return Upgrades.STICKY;
        default:
            return null;
    }
}
~~~

看到枚举类的时候我心是死的, 改起来特麻烦

也就是说大概率判断一个升级卡是否能放进ae接口是需要用到这个枚举类, 根本无法常规方法添加一个新的升级卡.

现在只能去看实际放升级卡进ae接口的最直接的方法, 看有什么方法破局

然后就是猛猛打断点, 看放进去的时候有没有被拦截

通过getType发现UpgradeInventory这个类里面有一个allowInsert最终被拦截了

逻辑

~~~java
public boolean allowInsert(IItemHandler inv, int slot, ItemStack itemstack) {
    if (itemstack.isEmpty()) {
        return false;
    }
    final Item it = itemstack.getItem();
    if (it instanceof IUpgradeModule) {
        final Upgrades u = ((IUpgradeModule) it).getType(itemstack);
        if (u != null) {
            return UpgradeInventory.this.getInstalledUpgrades(u) < UpgradeInventory.this.getMaxInstalled(u);
        }
    }
    return false;
}
~~~

这核心就是IUpgradeModule, 这个接口只有一个方法就是getType, 得了绕回来破案了

也就是说想要新的升级卡可以放进去, 那就必须继承这个类修改这个方法,

但修改可以, 但修改不太可能, ae这种大型mod的核心类, 你要继承没有多少可操作性

所以只能用字节码修改, 在mc里, 字节码修改有现成的成熟工具 mixin

到这里, 基本已经超出我的能力范围了, 所以就需要借鉴了,这里借鉴的是nae2的代码



你知道的这个mod不出意料的又有各种封装, 简直给我看花眼了, 还好类的分类做得很好

我直接把升级卡相关mixin的代码直接全部复制过来进行删减



## mixin的使用实现新增升级卡

原理就是将在所有插入升级卡的代码, 进行拓展加入新的升级卡的相关逻辑

怎么说呢, 枚举当然好用, 但附属开发就头疼了

总之就是在本来该返回false的地方, 判断是否新升级卡, 然后将返回修改成true

实现这个功能需要使用mixin创建一系列新字段新方法

也没什么好说的, 我提供项目地址, 有需要可以去看一下,总共不到10个mixin类

我也基本是一边问ai 一边改的



## 给升级卡添加功能

功能是定时判断 循环ae里所有ae接口, 所有有这张新内存卡的ae接口, 循环所有样板, 判断数量, 发送合成请求

**考虑定时器怎么加**

首先我们需要判断卡是否在me接口里面, 然后判断 me接口是否在ae网络里面, 这个网络是否通电了等

假如身上有100张卡,哪岂不是得100个定时器一直在不断判断, 就算每一组卡一个定时器. 结论就是定时器不可能加在卡上



那只能加在ae接口上, 按我的理解ae本来就有输出接口, 接口还能设置速度卡, 那就肯定会有任务定时执行机制来处理

只要找到这个机制,应该就很方便了.



所以最终通过ai 和 努力, 找到 一个IGridTickable, 由名字可以看出是grid(ae网络)的定时任务

发现这个类在存储总线等方块上被使用, 去看存储总线的实现看起来是定时刷新, 基本可以判断就是这个类



类有一个注释说是Implement on IGridHosts  which want to use AE's Network Ticking Feature.

那就ctrl H看继承关系, 直接展开所有, 发现大部分常用ae机器都是IGridProxyable下的tile类

发现大部分都是tile, 是block特有的, 也就是说只能绑定在block上, 不能绑定在 卡上, 到底是不是呢 , 我选择问ai

得到的结果是肯定




现在的问题是我没有方块只有一个升级卡, 那就只能创建一个

先创建一个白板方块, 给他的tileentity加上IGridTickable, 怎么加呢

IGridTickable一个方法返回AENetworkProxy这个类, 通过ai可以知道这个类可以帮我们解决连接ae网络的所有问题

发现IGridTickable有几个看起来是通用实现类, 那就只能问ai, 然后一个一个试了

试出来AENetworkTile好使, 方块直接连接进了ae网络, 现象是导线的变化





**扫描所有ae接口**

扫描怎么扫, 肯定是通过ae网络获取所有ae接口, ae肯定自带这个功能, 就好像人需要呼吸一样理所当然

ae网络的接口是IGrid, 里面有一个方法getMachines, 一看就知道有戏, 进游戏 打断点

你会看发现整个网络的的所有机器, 以class为key set为value



grid.getMachines(TileInterface.class)我们拿到了所有ae接口

现在就要判断每个接口是否含有我们这张新卡



**判断是否插有新卡**

这一步倒是简单, 因为之前mixin实现插入新卡的时候, 已经对升级卡这块的逻辑有一定了解

知道DualityInterface是关键类, 找这个类发现 getInventoryByName("upgrades") 可以获得4个升级槽位数据

循环一遍判断就能知道是否有新卡了, 有新卡就要扫描所有样板进行合成发送了



**读取样板数据**

当你指样板的时候,会显示配方信息, 里面就有我们需要的合成结果, 只要找到item类的信息设置方法, 就能获得ae自带的nbt读取合成信息的方法

这里肯定是先通过id 找到物品的class, 然后分析nbt组成结构 从中提取合成信息

这里有一坑就是 空白样板和 编码样板的 两个物品id不一样

空白样板 到 有编码样板 之间的转换流程  被封装得妈都不认得

最后发现是ItemEncodedPattern, 这个类就那么几个方法, 很容易知道 关键方法是 getPatternForItem

随便看看就知道是那几个方法是我们想要的



**发送合成请求**

不用说, 先找现成的代码看一下, 最先想到的就是lazyae的请求器

一个block也就那么几个类, 研究一下执行流程, 然后就开始写自己的逻辑, 一步一步查

总之就是问ai ,借鉴一下代码 ,写几行代码, 一直循环

最终发现请求功能 只需要tile实现ICraftingRequester接口, 然后用grid发送合成请求

~~~java
//stacks是所有合成配方的输出, stackInSlot是合成卡用来获取需要保持的数量
protected void tick(IGrid grid, IAEItemStack[] stacks, ItemStack stackInSlot) {

//ae网络的合成管理类
ICraftingGrid crafting = (ICraftingGrid) grid.getCache(ICraftingGrid.class); 
//ae网络的存储类
IMEMonitor<IAEItemStack> storageGrid = ((IStorageGrid) grid.getCache(IStorageGrid.class)).getInventory(AEApi.instance().storage().getStorageChannel(IItemStorageChannel.class));
for (IAEItemStack stack : stacks) {
    //获取数量, ae特有的stack IAEItemStack, 数量没有64限制
    IAEItemStack storage = storageGrid.getStorageList().findPrecise(stack);
    //计算需要合成多少物品
    int keepNum = ItemKeeperUpgrade.getKeepNum(stackInSlot);
    long storageNumber = storage.getStackSize();
    long shouldCraft = Math.max(0, keepNum - storageNumber);
    if (shouldCraft == 0) continue;
    IAEItemStack copy = stack.copy();
    copy.setStackSize(shouldCraft);
    //合成封装, 其实还是grid的使用
    //里面有两个步骤, 一个是创建job就是我们游戏里合成数量下一步计算合成所需材料
    //然后用这个job 去实际创建任务, 这时会返回一个link
    //总之就是通过返回的job 和link判断任务执行状态, 决定下一步干嘛
    this.craftingTracker.requestCrafting(copy, world, grid, crafting, this.actionSource);
}
~~~



**结束**

流程已经结束, 看起来并不算很复杂. 但我学的时候理清思路也花了不少时间

而且整个逻辑还有很大优化空间

写的思考流程和我学的时候实际流程相差甚远, 可以说是过来人复习的时候发现了更好的方法

不知道有没有人有这种感觉, 不是实际想问题的时候逻辑清晰, 通过线索一步步很快找到下一步的关键, 但当实际解决问题时, 脑子一团浆糊根本动不了. 

对于我个人来说有一个很明显的例子就是 高中坐着的时候脑袋一团浆糊, 但一旦休息时间站起来 整个状态就好起来了, 没走一步脑子就越清醒 想不通的问题思路一下就清晰了. 






