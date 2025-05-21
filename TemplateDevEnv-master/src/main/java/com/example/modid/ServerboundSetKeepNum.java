package com.example.modid;

import io.netty.buffer.ByteBuf;
import net.minecraft.entity.player.EntityPlayerMP;
import net.minecraft.server.MinecraftServer;
import net.minecraft.tileentity.TileEntity;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import net.minecraftforge.fml.common.network.NetworkRegistry;
import net.minecraftforge.fml.common.network.simpleimpl.IMessage;
import net.minecraftforge.fml.common.network.simpleimpl.IMessageHandler;
import net.minecraftforge.fml.common.network.simpleimpl.MessageContext;
import net.minecraftforge.fml.common.network.simpleimpl.SimpleNetworkWrapper;
import net.minecraftforge.fml.relauncher.Side;

public class ServerboundSetKeepNum implements IMessage {
    private BlockPos pos; //用来读取tileentity
    private int keepNum; //需要保存的数据

    public ServerboundSetKeepNum() {
    }

    public ServerboundSetKeepNum(BlockPos pos, int keepNum) {
        this.pos = pos;
        this.keepNum = keepNum;
    }

    @Override
    public void fromBytes(ByteBuf buf) {
        this.pos = new BlockPos(buf.readInt(), buf.readInt(), buf.readInt());
        this.keepNum = buf.readInt();
    }

    @Override
    public void toBytes(ByteBuf buf) {
        //通常是用mc提供的PacketBuffer,支持直接写string BlockPos.不用进行字节操作
        //fromBytes和toBytes 按同样的顺序处理数据就没问题
        buf.writeInt(pos.getX());
        buf.writeInt(pos.getY());
        buf.writeInt(pos.getZ());
        buf.writeInt(keepNum);
    }

    public static class Handler implements IMessageHandler<ServerboundSetKeepNum, IMessage> {
        @Override
        public IMessage onMessage(ServerboundSetKeepNum message, MessageContext ctx) {
            // 确保在主线程处理
            MinecraftServer server = ctx.getServerHandler().player.getServer();
            server.addScheduledTask(() -> {
                World world = ctx.getServerHandler().player.world;
                if (world.isBlockLoaded(message.pos)) {//区块是否加载
                    TileEntity te = world.getTileEntity(message.pos);
                    if (te instanceof TileBlockNew) {
                        EntityPlayerMP player = ctx.getServerHandler().player;
                        if(player.getDistanceSq(message.pos.getX(),message.pos.getY(),message.pos.getZ())>64)return;
                        TileBlockNew tile = (TileBlockNew) te;
                        tile.setKeepNum(message.keepNum);
                        tile.markDirty();//核心方法,告诉服务器这个实体tileentity数据修改了,需要同步到存档,如果设置了还会同步到客户端.同步用的是nbt机制
                        //这里也是ai生成的,应该是更新BlockState,但我没用到block的BlockState机制,应该不需要. 3 参数其中一个意思是需要同步到客户端,具体忘了
                        //拓展一下,我们在设置材质的时候,有一个blockstates的blocknew.json配置,里面就是设置不同的BlockState的渲染
                        world.notifyBlockUpdate(message.pos, world.getBlockState(message.pos), world.getBlockState(message.pos), 3);
                    }
                }
            });
            return null;
        }
    }

    public static final SimpleNetworkWrapper INSTANCE = NetworkRegistry.INSTANCE.newSimpleChannel(Tags.MOD_ID);

    //注册数据包
    public static void registerPackets() {
        int id = 0;
        INSTANCE.registerMessage(ServerboundSetKeepNum.Handler.class, ServerboundSetKeepNum.class, id++, Side.SERVER);
    }
}

