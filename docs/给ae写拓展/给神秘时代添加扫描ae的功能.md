---
layout: default
title: 给神秘时代添加扫描ae的功能
parent: 给ae写拓展
nav_order: 7
---

# 给神秘时代添加扫描ae的功能


这个只是我单机用的, 服务器用可能会卡服

思路很简单, 之前我们已经知道ae的基本工作原理了

只要我们获取到grid, 然后遍历一遍ae的所有物品就行了



ae解决了现在解决神秘时代

神秘时代1.12的扫描镜 自带扫描容器前100个物品的功能

只要找到相关代码然后改改就行,直接上代码





~~~java
//mixin修改ScanningManager
@Mixin(value = ScanningManager.class, remap = false)
public class MixinScanningManager {

    //在scanTheThing这个方法的最前面插入字节码(mixin是基于字节码操作的)
    //可以装一个idea 的插件, 搜minecraft就看到了, 有很多方便的功能提示
    @Inject(method = "scanTheThing", at = @At(
            value = "HEAD"
    ), cancellable = true)
    private static void scanTheThing(EntityPlayer player, Object object, CallbackInfo ci) {
        try{
            //神秘时代6 的scanTheThing方法写的很奇怪, 可能是反编译的问题吧
            //这里是直接在scanTheThing最前面拦截了BlockPos类型的参数进行操作
            //如果是ae方块才处理,如果不是就放行, 不影响原来的逻辑
            if (object instanceof BlockPos pos) {
                TileEntity tileEntity = player.world.getTileEntity(pos);
                if (tileEntity == null) return;
                //TileCableBus是ae线缆的tile, 可以通过它获取各个方向的终端
                //如果没有找到终端就不处理
                if (tileEntity instanceof TileCableBus cable) {
                    IGrid grid = null;
                    try {
                        for (AEPartLocation value : AEPartLocation.values()) {
                            IGridNode gridNode = cable.getGridNode(value);
                            if (gridNode != null) {
                                grid = gridNode.getGrid();
                                break;
                            }
                        }
                    } catch (Exception e) {
                        return;
                    }
                    if (grid == null) return;

                    IMEMonitor<IAEItemStack> storageGrid = ((IStorageGrid) grid.getCache(IStorageGrid.class)).getInventory(AEApi.instance().storage().getStorageChannel(IItemStorageChannel.class));
                    for (IAEItemStack iaeItemStack : storageGrid.getStorageList()) {
                        ItemStack stack = iaeItemStack.getCachedItemStack(1);

                        if (stack != null && !stack.isEmpty()) {
                            //这里就是神秘时代处理某个物品的逻辑, 直接调用
                            ScanningManager.scanTheThing(player, stack);
                        }
                    }
                    //如果成功处理, 就是用mixin的return 功能, 跳过原来的逻辑
                    ci.cancel();
                    //神秘时代的成功信息弹出, 其实这里有bug, 但单机用没问题
                    player.sendStatusMessage(new TextComponentString("§a§o" + I18n.translateToLocal("tc.knownobject")), true);
                }
            }
        }catch(Exception e){
            Main.LOGGER.error("scan in ae error",e);
        }
    }
}
~~~

可见只是很简单就小改动
