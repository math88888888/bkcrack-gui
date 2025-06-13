# -*- coding: utf-8 -*-
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton,
    QTextBrowser, QPlainTextEdit, QScrollArea, QGroupBox, QComboBox
)
from qfluentwidgets import PushButton, TextBrowser, PlainTextEdit


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName("Form")
        Form.resize(1200, 800)
        Form.setMinimumHeight(800)
        Form.setStyleSheet("""
            QWidget {
                background-color: rgb(0, 0, 0);
                color: rgb(255, 255, 127);
                font-family: 华文中宋;
                font-size: 10pt;
                font-weight: bold;
            }

            /* 普通按钮样式 */
            PushButton {
                background-color: rgb(197, 0, 99);
                color: white;
                border-radius: 5px;
                border: none;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
            }

            /* 执行类按钮 */
            QPushButton[execButton="true"] {
                background-color: rgb(197, 0, 99);
                color: white;
                border-radius: 5px;
                border: none;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
            }

            QPushButton[execButton="true"]:hover {
                background-color: rgb(227, 0, 129);
            }

            PushButton:hover {
                background-color: rgb(167, 0, 79);
            }

            QTextBrowser {
                background-color: rgb(35, 35, 35);
                color: rgb(255, 255, 127);
                border: 2px solid rgb(255, 170, 255);
                border-radius: 8px;
                padding: 12px;
                font-size: 10pt;
                font-family: Cascadia Code;
            }

            QPlainTextEdit {
                background-color: rgb(35, 35, 35);
                color: rgb(255, 255, 127);
                border: 1px solid rgb(255, 170, 255);
                border-radius: 5px;
                padding: 6px;
                font-size: 10pt;
                font-family: Cascadia Code;
            }

            QLabel {
                color: rgb(255, 255, 127);
                font-family: 华文中宋;
                font-size: 10pt;
                font-weight: bold;
            }

            QGroupBox {
                border: 1px solid rgb(255, 170, 255);
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
        """)

        main_layout = QHBoxLayout(Form)

        # 创建可滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(15)

        # 添加压缩功能区域
        compress_group = QGroupBox("创建明文压缩包(-P 可选)")
        compress_layout = QVBoxLayout(compress_group)

        label = QLabel("选择要压缩的文件(用于-P)")
        compress_layout.addWidget(label)

        file_layout = QHBoxLayout()
        self.SelectFilesToCompress = PushButton("选择文件")
        self.SelectFilesToCompress.setMinimumHeight(35)
        self.SelectFilesToCompress.setProperty("execButton", True)
        self.FilesToCompressInput = TextBrowser()
        self.FilesToCompressInput.setMinimumHeight(35)
        file_layout.addWidget(self.SelectFilesToCompress)
        file_layout.addWidget(self.FilesToCompressInput)
        compress_layout.addLayout(file_layout)

        label = QLabel("设置密码 (不建议使用)")
        compress_layout.addWidget(label)
        self.CompressPasswordInput = PlainTextEdit()
        self.CompressPasswordInput.setMinimumHeight(35)
        compress_layout.addWidget(self.CompressPasswordInput)

        button_layout = QHBoxLayout()
        self.CompressDeflateButton = QPushButton("压缩 (Deflate)")
        self.CompressDeflateButton.setProperty("execButton", True)
        self.CompressDeflateButton.setMinimumHeight(35)
        self.CompressStoreButton = QPushButton("压缩 (Store)")
        self.CompressStoreButton.setProperty("execButton", True)
        self.CompressStoreButton.setMinimumHeight(35)
        button_layout.addWidget(self.CompressDeflateButton)
        button_layout.addWidget(self.CompressStoreButton)
        compress_layout.addLayout(button_layout)

        label = QLabel("输出路径")
        compress_layout.addWidget(label)
        self.CompressOutputPath = PlainTextEdit()
        self.CompressOutputPath.setMinimumHeight(35)
        compress_layout.addWidget(self.CompressOutputPath)

        self.UsePlainZipButton = QPushButton("用作明文压缩包(-P)")
        self.UsePlainZipButton.setProperty("execButton", True)
        self.UsePlainZipButton.setMinimumHeight(35)
        compress_layout.addWidget(self.UsePlainZipButton)

        control_layout.addWidget(compress_group)

        label = QLabel("加密的压缩包(-C)")
        control_layout.addWidget(label)

        file_layout = QHBoxLayout()
        self.SelectCompressedFile = PushButton("选择文件")
        self.SelectCompressedFile.setMinimumHeight(35)
        self.SelectCompressedFile.setProperty("execButton", True)
        self.ViewCompressedZip = TextBrowser()
        self.ViewCompressedZip.setMinimumHeight(35)
        file_layout.addWidget(self.SelectCompressedFile)
        file_layout.addWidget(self.ViewCompressedZip)
        control_layout.addLayout(file_layout)

        self.CompressedZipInfo = QPushButton("查看压缩包信息")
        self.CompressedZipInfo.setProperty("execButton", True)
        self.CompressedZipInfo.setMinimumHeight(35)
        control_layout.addWidget(self.CompressedZipInfo)

        label = QLabel("要解密的文件(-c)")
        control_layout.addWidget(label)

        file_layout = QHBoxLayout()
        self.TargetFileCombo = QComboBox()
        self.TargetFileCombo.setMinimumHeight(35)
        self.TargetFileCombo.setStyleSheet(
            "QComboBox { background-color: rgb(35,35,35); color: rgb(255,255,127); font-size: 10pt; }")
        self.ReadZipEntriesButton = PushButton("读取条目名")
        self.ReadZipEntriesButton.setMinimumHeight(35)
        self.ReadZipEntriesButton.setProperty("execButton", True)
        file_layout.addWidget(self.TargetFileCombo)
        file_layout.addWidget(self.ReadZipEntriesButton)
        control_layout.addLayout(file_layout)

        label = QLabel("明文文件(-p) 预制的明文在plains文件夹下")
        control_layout.addWidget(label)
        file_layout = QHBoxLayout()
        self.SelectPlainFile = PushButton("选择文件")
        self.SelectPlainFile.setMinimumHeight(35)
        self.SelectPlainFile.setProperty("execButton", True)
        self.ViewPlainFile = TextBrowser()
        self.ViewPlainFile.setMinimumHeight(35)
        file_layout.addWidget(self.SelectPlainFile)
        file_layout.addWidget(self.ViewPlainFile)
        control_layout.addLayout(file_layout)

        label = QLabel("偏移量(-o 可选)")
        control_layout.addWidget(label)
        self.OffsetInput = PlainTextEdit()
        self.OffsetInput.setMinimumHeight(35)
        control_layout.addWidget(self.OffsetInput)

        label = QLabel(" -p 参数的内容(自动添加)")
        control_layout.addWidget(label)
        self.PlainTextContent = PlainTextEdit()
        self.PlainTextContent.setMinimumHeight(35)
        control_layout.addWidget(self.PlainTextContent)

        # Add direct hex attack section
        direct_hex_group = QGroupBox("(没有-P,-p的时候）只有(-x)")
        direct_hex_layout = QVBoxLayout(direct_hex_group)

        label = QLabel("目标文件偏移地址")
        direct_hex_layout.addWidget(label)
        self.DirectHexOffsetInput = PlainTextEdit()
        self.DirectHexOffsetInput.setMinimumHeight(35)
        direct_hex_layout.addWidget(self.DirectHexOffsetInput)

        label = QLabel("部分已知明文值")
        direct_hex_layout.addWidget(label)
        self.DirectHexPatternInput = PlainTextEdit()
        self.DirectHexPatternInput.setMinimumHeight(35)
        direct_hex_layout.addWidget(self.DirectHexPatternInput)

        self.DirectHexAttackButton = QPushButton("开始攻击")
        self.DirectHexAttackButton.setProperty("execButton", True)
        self.DirectHexAttackButton.setMinimumHeight(35)
        direct_hex_layout.addWidget(self.DirectHexAttackButton)

        control_layout.addWidget(direct_hex_group)

        label = QLabel("额外的明文(-x 可选)")
        control_layout.addWidget(label)
        xlayout = QHBoxLayout()
        self.HexOffsetInput = PlainTextEdit()
        self.HexOffsetInput.setMaximumWidth(100)
        self.HexOffsetInput.setMinimumHeight(30)
        self.HexPatternInput = PlainTextEdit()
        self.HexPatternInput.setMinimumHeight(30)
        xlayout.addWidget(QLabel("目标文件偏移地址"))
        xlayout.addWidget(self.HexOffsetInput)
        xlayout.addWidget(QLabel("部分已知明文值"))
        xlayout.addWidget(self.HexPatternInput)
        control_layout.addLayout(xlayout)

        self.ExecuteHexButton = QPushButton("执行-x情况下攻击")
        self.ExecuteHexButton.setProperty("execButton", True)
        self.ExecuteHexButton.setMinimumHeight(35)
        control_layout.addWidget(self.ExecuteHexButton)

        self.StartAttack = QPushButton("开始攻击")
        self.StartAttack.setProperty("execButton", True)
        self.StartAttack.setMinimumHeight(35)
        control_layout.addWidget(self.StartAttack)

        label = QLabel("密钥")
        control_layout.addWidget(label)
        self.InputKey = PlainTextEdit()
        self.InputKey.setMinimumHeight(35)
        control_layout.addWidget(self.InputKey)

        # Add password recovery section
        recovery_group = QGroupBox("密码恢复(-r)")
        recovery_layout = QVBoxLayout(recovery_group)

        label = QLabel("密码长度范围 (如: 10 或 8..12)")
        recovery_layout.addWidget(label)
        self.PasswordLengthInput = PlainTextEdit()
        self.PasswordLengthInput.setMinimumHeight(35)
        recovery_layout.addWidget(self.PasswordLengthInput)

        self.RecoverPasswordButton = QPushButton("恢复密码")
        self.RecoverPasswordButton.setProperty("execButton", True)
        self.RecoverPasswordButton.setMinimumHeight(35)
        recovery_layout.addWidget(self.RecoverPasswordButton)

        control_layout.addWidget(recovery_group)

        self.DirectExtractButton = QPushButton("直接导出文件(-d)")
        self.DirectExtractButton.setProperty("execButton", True)
        self.DirectExtractButton.setMinimumHeight(35)
        control_layout.addWidget(self.DirectExtractButton)

        self.ExportZip = QPushButton("导出无密码压缩包")
        self.ExportZip.setProperty("execButton", True)
        self.ExportZip.setMinimumHeight(35)
        control_layout.addWidget(self.ExportZip)

        label = QLabel("修改密码并导出(-U)")
        control_layout.addWidget(label)

        password_layout = QHBoxLayout()

        zip_group = QWidget()
        zip_layout = QVBoxLayout(zip_group)
        zip_layout.setContentsMargins(0, 0, 0, 0)
        zip_layout.addWidget(QLabel("输出zip"))
        self.OutputZipEdit = PlainTextEdit()
        self.OutputZipEdit.setMinimumHeight(35)
        zip_layout.addWidget(self.OutputZipEdit)
        password_layout.addWidget(zip_group)

        pass_group = QWidget()
        pass_layout = QVBoxLayout(pass_group)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        pass_layout.addWidget(QLabel("新密码"))
        self.NewPasswordEdit = PlainTextEdit()
        self.NewPasswordEdit.setMinimumHeight(35)
        pass_layout.addWidget(self.NewPasswordEdit)
        password_layout.addWidget(pass_group)

        control_layout.addLayout(password_layout)

        self.ChangePasswordButton = QPushButton("修改密码并导出")
        self.ChangePasswordButton.setProperty("execButton", True)
        self.ChangePasswordButton.setMinimumHeight(35)
        control_layout.addWidget(self.ChangePasswordButton)

        # Add control buttons
        control_buttons_layout = QHBoxLayout()
        self.ClearAllButton = QPushButton("一键清除")
        self.ClearAllButton.setProperty("execButton", True)
        self.ClearAllButton.setMinimumHeight(35)

        self.StopAttackButton = QPushButton("停止攻击")
        self.StopAttackButton.setProperty("execButton", True)
        self.StopAttackButton.setMinimumHeight(35)

        control_buttons_layout.addWidget(self.ClearAllButton)
        control_buttons_layout.addWidget(self.StopAttackButton)
        control_layout.addLayout(control_buttons_layout)

        control_layout.addStretch()

        scroll.setWidget(control_panel)

        output_panel = QWidget()
        output_layout = QVBoxLayout(output_panel)
        self.OutPutArea = QTextBrowser()
        output_layout.addWidget(self.OutPutArea)

        main_layout.addWidget(scroll, 40)
        main_layout.addWidget(output_panel, 60)

    def retranslateUi(self, Form):
        Form.setWindowTitle("bkcrack-gui v0.9   Author: 星辰不及阁下")
