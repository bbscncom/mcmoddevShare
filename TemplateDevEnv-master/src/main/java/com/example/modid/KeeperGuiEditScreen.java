package com.example.modid;

import net.minecraft.client.gui.GuiButton;
import net.minecraft.client.gui.GuiScreen;
import net.minecraft.client.gui.GuiTextField;
import net.minecraft.client.resources.I18n;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NBTTagCompound;
import net.minecraft.nbt.NBTTagInt;
import net.minecraft.tileentity.TileEntity;
import org.lwjgl.input.Keyboard;

import java.io.IOException;
import java.util.function.Consumer;

public class KeeperGuiEditScreen extends GuiScreen {
    private final TileEntity tile; //保存TileEntity用来操作数据存储
    private GuiTextField inputField; //input组件
    private GuiButton doneButton; //完成按钮,可以不要，这个类基本是ai生成的，懒得删了

    public KeeperGuiEditScreen(TileEntity tile) {
        this.tile = tile; //绑定当前界面和tile，需要用到tile来处理信息保存逻辑
    }

    @Override
    public void initGui() {
        Keyboard.enableRepeatEvents(true); //我也不知道 ai生成的
        //创建一个输入框.GuiTextField是Gui,是GuiScreen里面的组件.gui和guiGuiScreen是组件和容器的关系
        //width heiht是窗口大小,这里的数值计算就像是 html的div里面的居中计算逻辑.200 20是输入框的大小
        this.inputField = new GuiTextField(0, this.fontRenderer, this.width / 2 - 100, this.height / 2 - 30, 200, 20);
        this.inputField.setMaxStringLength(50);
        this.inputField.setFocused(true);

        //从tile读取信息填充到输入框
        TileBlockNew tile1 = (TileBlockNew) tile;
        int keepNum = tile1.getKeepNum();
        this.inputField.setText(keepNum == 0 ? "" : String.valueOf(keepNum));


        //i18n会读取 en_us的文本
        this.doneButton = new GuiButton(1, this.width / 2 - 100, this.height / 2, I18n.format("gui.done"));
        //mc提供的button机制
        this.buttonList.add(doneButton);
    }

    //当界面关闭,发送数据包给服务器,保存这个输入值. 具体逻辑看数据包类
    @Override
    public void onGuiClosed() {
        Keyboard.enableRepeatEvents(false);
        int value = inputField.getText().isEmpty()?0:Integer.parseInt(inputField.getText());
        ServerboundSetKeepNum.INSTANCE.sendToServer(new ServerboundSetKeepNum(tile.getPos(), value));
    }

    //当点击按钮后,mouseClicked调用后,会绕回来这里,判断点击了那个按钮,触发什么逻辑. 这里也是ai生成的,我之前也没用过这个机制.
    //我上一次设置按钮逻辑是将1.20机制照搬到1.12,跳过了1.12的按钮机制
    @Override
    protected void actionPerformed(GuiButton button) throws IOException {
        if (button.id == 1) {
            // 处理输入内容
            this.mc.displayGuiScreen(null); // 关闭GUI
        }
    }

    @Override
    protected void keyTyped(char typedChar, int keyCode) throws IOException {
        // 允许退格、删除、箭头等控制键
        if (Character.isDigit(typedChar) || isControlKey(keyCode)) {
            this.inputField.textboxKeyTyped(typedChar, keyCode);
        } else {
            // 屏蔽非法字符
        }
        super.keyTyped(typedChar, keyCode);
    }

    // 判断是否为允许的控制键（例如退格、箭头等）
    private boolean isControlKey(int keyCode) {
        return keyCode == Keyboard.KEY_BACK
                || keyCode == Keyboard.KEY_DELETE
                || keyCode == Keyboard.KEY_LEFT
                || keyCode == Keyboard.KEY_RIGHT
                || keyCode == Keyboard.KEY_HOME
                || keyCode == Keyboard.KEY_END;
    }


    @Override
    protected void mouseClicked(int mouseX, int mouseY, int mouseButton) throws IOException {
        super.mouseClicked(mouseX, mouseY, mouseButton);
        this.inputField.mouseClicked(mouseX, mouseY, mouseButton);//发送事件给内部组件
    }

    @Override
    public void updateScreen() {
        super.updateScreen();
        this.inputField.updateCursorCounter();//发送事件给内部组件
    }

    @Override
    public void drawScreen(int mouseX, int mouseY, float partialTicks) {
        this.drawDefaultBackground();//画背景,就是黑色透明背景
        this.inputField.drawTextBox();//渲染输入框
        super.drawScreen(mouseX, mouseY, partialTicks);
    }
}

