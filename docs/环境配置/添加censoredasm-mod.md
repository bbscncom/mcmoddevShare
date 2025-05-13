---
layout: default
title: 添加CensoredASM mod
parent: 环境配置
nav_order: 2
---

# 添加CensoredASM mod


```bash
#崩溃返回主菜单mod而不是整个游戏崩掉，当然不是百分百生效，有时候还是会崩掉

#添加maven仓库
repositories {
    maven {
        name 'CleanroomMC Maven'
        url 'https://maven.cleanroommc.com'
    }
    maven {
        name 'CurseMaven'
        url 'https://www.cursemaven.com'
        content {
            includeGroup 'curse.maven'
        }
    }
}
#build.gradle里面的dependencies添加mod
implementation rfg.deobf('curse.maven:CensoredASM-460609:6333774')
CensoredASM是自定义名称，自己看的。460609是curseforge mod页面右面的projectid，6333774是具体某个版本的mod文件下载页面的url路径的最后的数字

#重点来了
不知道是idea还是gradle还是cleanroom的问题，你添加的依赖在可能依赖仓库找不到，需要退出idea删除根目录的.idea后启动idea。或许还有其他好方法，我也不知道
你手动下载再引入也不是不行

#rfg.deobf的意思应该是反混淆，有些mod需要用到，不然会显示找不到类啥的
如果你用的其他开发环境可能关键词不是rfg.deobf，这个我也是去discord问人才知道的，是个坑
普通mod使用implementation 'curse.maven:CensoredASM-460609:6333774'
```





