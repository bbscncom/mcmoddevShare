package com.example.modid;

import net.minecraft.block.Block;
import net.minecraft.block.material.Material;
import net.minecraft.block.state.IBlockState;
import net.minecraft.client.Minecraft;
import net.minecraft.client.renderer.block.model.ModelResourceLocation;
import net.minecraft.creativetab.CreativeTabs;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.item.Item;
import net.minecraft.item.ItemBlock;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.tileentity.TileEntity;
import net.minecraft.util.EnumFacing;
import net.minecraft.util.EnumHand;
import net.minecraft.util.ResourceLocation;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import net.minecraftforge.client.model.ModelLoader;
import net.minecraftforge.fml.common.registry.ForgeRegistries;
import net.minecraftforge.fml.common.registry.GameRegistry;
import net.minecraftforge.fml.relauncher.Side;
import net.minecraftforge.fml.relauncher.SideOnly;

import javax.annotation.Nullable;

public class BlockNew extends Block {
    public static CreativeTabs tabs = new CreativeTabs(Tags.MOD_ID) { //创建一个新的创造标签，内部进行管理，不用注册
        @Override
        public ItemStack createIcon() {
            return new ItemStack(blockNewItem);//设置标签显示的图标，这里使用这个方块的图标
        }
    };

    public BlockNew() {
        super(Material.ROCK); //方块基础属性，点进去就看到有什么了
        this.setHardness(2.0F); //硬度
        this.setCreativeTab(tabs);
    }

    public static Block blockNew; //单例，可以通过注解让forge注入，我这里直接保存
    public static ItemBlock blockNewItem;

    public static void reg() {
        blockNew = new BlockNew();
        blockNewItem = register("blocknew", blockNew);
        registerItemModels();
        //注册tileentity
        GameRegistry.registerTileEntity(TileBlockNew.class, new ResourceLocation(Tags.MOD_ID, "blocknew"));
    }

    @SideOnly(Side.CLIENT)
    private static void registerItemModels() { //这个作用是给item绑定材质，这里的重点是block也需要设置，不然会出现方块放出来有材质，但背包物品显示没有材质，通过ItemBlock实现block转item
        ModelLoader.setCustomModelResourceLocation(
                blockNewItem,    // 你的物品对象
                0,                     // metadata
                new ModelResourceLocation(Tags.MOD_ID + ":blocknew", "inventory")
        );
    }

    private static <T> T register(String name, Object obj) {
        if (obj instanceof Block block) {
            block.setRegistryName(Tags.MOD_ID, name);
            block.setTranslationKey(Tags.MOD_ID + "." + name);
            ForgeRegistries.BLOCKS.register(block); //告诉mc有一个方块

            ItemBlock itemBlock = new ItemBlock(block);
            itemBlock.setRegistryName(Tags.MOD_ID, name); //注册id，游戏里看到的物品id
            itemBlock.setTranslationKey(Tags.MOD_ID + "." + name); //翻译id，en_us.lang 会读取里面配置的翻译
            ForgeRegistries.ITEMS.register(itemBlock); //告诉mc这里有一个这样的物品

            return (T) itemBlock;

        } else if (obj instanceof Item) {
            Item item = (Item) obj;
            item.setRegistryName(Tags.MOD_ID, name);
            item.setTranslationKey(Tags.MOD_ID + "." + name);
            ForgeRegistries.ITEMS.register(item);
            return (T) item;
        }
        throw new IllegalArgumentException("不支持的对象类型: " + obj.getClass().getName());
    }


    @Override
    public boolean onBlockActivated(World worldIn, BlockPos pos, IBlockState state, EntityPlayer playerIn, EnumHand hand, EnumFacing facing, float hitX, float hitY, float hitZ) {
        // 只在客户端打开 GUI
        // 某些逻辑只在客户端执行，像是这里打开界面，服务器根本不需要界面渲染逻辑。
        // 如果要打开熔炉，服务器会通过IGuiHandler配置读取打开那个Container，Container包含客户端和服务区都需要的逻辑。
        // 由于我这没有用Container，不需要服务器逻辑，所以当你打开这个界面服务器根本不知道你打开了，这个界面只存在与客户端，服务器只知道你发送了一个保存信息的数据包
        if (worldIn.isRemote) {
            TileEntity tile = worldIn.getTileEntity(pos);
            Minecraft.getMinecraft().displayGuiScreen(new KeeperGuiEditScreen(tile));
            return true;
        }
        return true;
    }


    @Nullable
    @Override
    public TileEntity createTileEntity(World world, IBlockState state) {//绑定block和tileentity
        return new TileBlockNew();
    }


    @Override
    public boolean hasTileEntity(IBlockState state) {//mc先调用这个判断有，才会创建
        return true;
    }
}
