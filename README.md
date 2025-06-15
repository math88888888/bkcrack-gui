# 🚀bkcrack-gui：bkcrack 的可视化压缩包明文攻击工具

**✨一款专为 bkcrack.exe 打造的图形化操作工具**

欢迎加入交流群，共同探讨！本工具完全免费开源，开发者实力有限，恳请各位大佬手下留情，哈哈哈！🚫 未经授权禁止转载。期待您的宝贵建议，助力工具不断完善！若觉得好用，欢迎前往 GitHub 点亮 ⭐ Star 支持～

如果有师傅需要测试题wp的，欢迎进群查看



![image](https://github.com/user-attachments/assets/deff1f05-82be-4a85-99f8-871a2935e4c6)

## 运行
安装依赖
```
pip install -r requirements.txt
如果有缺少别的库，自己安装即可
```
启动程序
```
第一种方式：python main.py
第二种方式：运行run.bat
```

## 🌟核心功能

- 初始界面：简洁布局，核心功能入口一目了然
- 压缩包信息页：结构化展示文件元数据，支持目录树展开
- 攻击执行页：实时日志输出与进度可视化，关键参数动态更新

![image-20250615104353696](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615104353696.png)

### 🛡️加密压缩包处理

加密压缩包可以**拖拽**进去，也可进行**文件选择**，能够实现**自动填充**

![image-20250615104424523](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615104424523.png)

支持**查看压缩包信息**，读取文件目录

压缩包信息包含加密zip中的文件目录，大小，加密方式，以及压缩方式（部分题目会考查**压缩方式**）

![image-20250615104447672](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615104447672.png)



### 🧩明文压缩包构建

轻松构建明文压缩包！选择明文文件后，可根据不同压缩方式生成压缩包，并支持将其用于攻击加密压缩包，自动填充明文文件路径。

![image-20250615104829613](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615104829613.png)

### ⚡执行-x攻击

快速启动攻击，操作简单，效果显著！

![image-20250615112953450](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615112953450.png)

### 🔑密码恢复

支持高效密码恢复，可通过测试用例验证功能。

![image-20250615113040528](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615113040528.png)

效果如下

![image-20250614203415638](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250614203415638.png)

### 🛠️辅助功能模块

提供**密码修改**、**一键清除**及**停止攻击**等实用功能，操作更便捷。

![image-20250615113129000](https://cdn.jsdelivr.net/gh/F0T0ne/Image/image-20250615113129000.png)
