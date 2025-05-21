package com.example.modid;

import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.tileentity.TileEntity;

public class TileBlockNew extends TileEntity {


    private int keepNum; //需要保存的数据

    //这里的意思是给nbt添加你想要保存的数据. 这个方法是mc内部调用的，调用链的最外层通常是new一个NBTTagCompound，每一级把想要保存的数据写进去
    //mc拿到返回就代表这个实体需要保存进存档的所有数据
    @Override
    public NBTTagCompound writeToNBT(NBTTagCompound compound) {
        super.writeToNBT(compound);
        compound.setInteger("keepnum", keepNum);
        return compound;
    }

    @Override
    public void readFromNBT(NBTTagCompound compound) {
        super.readFromNBT(compound);
        this.keepNum = compound.getInteger("keepnum");
    }

    public int getKeepNum() {
        return keepNum;
    }

    public void setKeepNum(int keepNum) {
        this.keepNum = keepNum;
    }

    //这两方法是mc判断nbt是否需要同步到客户端，如果不重写这个方法，客户端不会更新信息
    //可能是这个作用，我也没删过
    @Override
    public NBTTagCompound getUpdateTag() {
        return writeToNBT(new NBTTagCompound());
    }

    @Override
    public void handleUpdateTag(NBTTagCompound tag) {
        readFromNBT(tag);
    }
}
