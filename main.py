from PySide6 import QtCore
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QWidget, QFileDialog, QMessageBox,
                               QGroupBox, QDialog, QLabel, QVBoxLayout, QScrollArea,
                               QTextEdit, QHBoxLayout, QSizePolicy, QListWidget,
                               QListWidgetItem, QMenu)
from PySide6.QtGui import (QColor, QDragEnterEvent, QDropEvent, QPixmap, QImage,
                           QImageReader, QTextDocument, QPainter, QGuiApplication, QAction)
from qfluentwidgets import PushButton, TextBrowser, PlainTextEdit
from ui.Ui_main import Ui_Form
import subprocess
import sys
import os
import tempfile
import zipfile
import time
import binascii
import shutil
import struct


class CommandThread(QThread):
    output_signal = Signal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None
        self.temp_file_path = None
        self._is_running = True

    def run(self):
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            shell=True,
            encoding='utf-8',
            errors='replace'
        )
        for line in self.process.stdout:
            if not self._is_running:
                break
            self.output_signal.emit(line.strip())
        self.process.stdout.close()
        if self._is_running:
            self.process.wait()
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            try:
                os.unlink(self.temp_file_path)
            except:
                pass

    def stop(self):
        self._is_running = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass

    def set_temp_file(self, path):
        self.temp_file_path = path


class FilePreviewWindow(QDialog):
    """文件预览窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件预览")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(35, 35, 35);
            }
            QLabel {
                color: white;
                font-family: Arial;
                font-size: 12pt;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.current_image = None  # 用于保存当前预览的图像

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        # 使用QTextEdit替代QLabel以支持文本选择和复制
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgb(45, 45, 45);
                color: white;
                font-family: Consolas;
                font-size: 10pt;
                border: none;
                padding: 10px;
            }
        """)

        # 图像预览标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("QLabel { padding: 20px; }")

        # 内容堆叠容器
        self.content_stack = QWidget()
        self.stack_layout = QVBoxLayout(self.content_stack)
        self.stack_layout.addWidget(self.text_edit)
        self.stack_layout.addWidget(self.image_label)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.content_stack)
        self.layout.addWidget(self.scroll_area)

        # 设置右键菜单
        self.setup_context_menus()

    def setup_context_menus(self):
        # 文本编辑器的右键菜单
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self.show_text_context_menu)

        # 图像标签的右键菜单
        self.image_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_label.customContextMenuRequested.connect(self.show_image_context_menu)

    def show_text_context_menu(self, pos):
        menu = self.text_edit.createStandardContextMenu()

        # 添加全选和复制按钮
        select_all = QAction("全选", self)
        select_all.triggered.connect(self.text_edit.selectAll)
        menu.insertAction(menu.actions()[0], select_all)

        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.text_edit.copy)
        menu.insertAction(menu.actions()[1], copy_action)

        menu.exec(self.text_edit.mapToGlobal(pos))

    def show_image_context_menu(self, pos):
        if not self.current_image:
            return

        menu = QMenu()
        copy_action = QAction("复制图片", self)
        copy_action.triggered.connect(self.copy_image_to_clipboard)
        menu.addAction(copy_action)
        menu.exec(self.image_label.mapToGlobal(pos))

    def copy_image_to_clipboard(self):
        if self.current_image:
            clipboard = QGuiApplication.clipboard()
            clipboard.setImage(self.current_image)

    def preview_file(self, file_path):
        try:
            self.text_edit.clear()
            self.image_label.clear()
            self.status_label.clear()

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 大于10MB的文件
                raise ValueError("文件过大，请直接查看")

            ext = os.path.splitext(file_path)[1].lower()
            supported_image = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')
            supported_text = ('.txt', '.csv', '.xml', '.json', '.html', '.htm')

            if ext in supported_image:
                self.preview_image(file_path)
                self.text_edit.hide()
                self.image_label.show()
            elif ext in supported_text:
                self.preview_text(file_path)
                self.image_label.hide()
                self.text_edit.show()
            else:
                QMessageBox.warning(
                    self,
                    "不支持的文件格式",
                    f"不支持预览 {ext} 格式的文件",
                    QMessageBox.Ok
                )
                self.close()
                return

            self.status_label.setText(f"正在预览: {os.path.basename(file_path)}")
            self.status_label.setStyleSheet("color: cyan;")

        except Exception as e:
            self.show_error(f"预览失败: {str(e)}")

    def preview_image(self, file_path):
        try:
            reader = QImageReader(file_path)
            reader.setAutoTransform(True)

            max_size = 1600
            if reader.size().width() > max_size or reader.size().height() > max_size:
                reader.setScaledSize(reader.size().scaled(
                    max_size, max_size, Qt.KeepAspectRatio))

            self.current_image = reader.read()
            if self.current_image.isNull():
                raise ValueError(reader.errorString())

            pixmap = QPixmap.fromImage(self.current_image)
            self.image_label.setPixmap(pixmap)
            self.image_label.adjustSize()

            info = f"尺寸: {self.current_image.width()}x{self.current_image.height()} 格式: {reader.format()}"
            self.status_label.setText(info)

        except Exception as e:
            self.show_error(f"无法加载图片: {str(e)}")

    def preview_text(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(4096)

            # 方法1：优先尝试 UTF-8
            try:
                text = raw_data.decode('utf-8')
                self.text_edit.setText(text)
                self.status_label.setText(f"编码: utf-8 | 大小: {os.path.getsize(file_path)} 字节")
                return
            except UnicodeDecodeError:
                pass

            # 方法2：用 本地记事本打开
            try:
                if os.path.exists(file_path):
                    subprocess.Popen(['notepad', file_path])  # 只调用一次
                else:
                    print("文件不存在！")
            except:
                pass

            # 方法3：显示十六进制（终极回退方案）
            hex_data = ' '.join(f'{b:02x}' for b in raw_data[:1000])  # 限制显示前1000字节
            self.text_edit.setText(f"无法解码为文本，Hex 预览:\n{hex_data}...")
            self.status_label.setText(f"编码: 二进制 | 大小: {os.path.getsize(file_path)} 字节")

        except Exception as e:
            self.show_error(f"读取失败: {str(e)}")

    def show_error(self, message):
        self.text_edit.setText("")
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: red;")


class MultiFilePreviewWindow(QDialog):
    """多文件预览窗口（修复版）"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件预览窗口")
        self.setMinimumSize(1000, 700)

        # 主布局
        self.main_layout = QHBoxLayout(self)

        # 左侧文件列表
        self.file_list = QListWidget()
        self.file_list.setFixedWidth(250)
        self.file_list.itemClicked.connect(self.on_file_selected)
        self.main_layout.addWidget(self.file_list)

        # 右侧预览区域（使用独立的FilePreviewWindow）
        self.preview_window = FilePreviewWindow()  # 创建独立的预览窗口实例
        self.preview_window.setMinimumWidth(750)
        self.main_layout.addWidget(self.preview_window)  # 直接添加整个窗口

        # 状态栏
        self.status_bar = QLabel()
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_bar)

        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(35, 35, 35);
            }
            QListWidget {
                background-color: rgb(45, 45, 45);
                color: white;
                border: 1px solid rgb(100, 100, 100);
                font-size: 11pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgb(70, 70, 70);
            }
            QListWidget::item:hover {
                background-color: rgb(60, 60, 60);
            }
            QListWidget::item:selected {
                background-color: rgb(255, 105, 180);
                color: white;
            }
            QLabel#status_bar {
                border-top: 1px solid gray;
                padding: 5px;
                color: white;
            }
        """)
        self.status_bar.setObjectName("status_bar")

    def set_files(self, file_paths):
        """设置要预览的文件列表"""
        self.file_list.clear()
        for path in file_paths:
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.UserRole, path)  # 存储完整路径
            self.file_list.addItem(item)

        # 默认选择第一个文件
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            self.on_file_selected(self.file_list.currentItem())

    def on_file_selected(self, item):
        """当选择文件时更新预览"""
        file_path = item.data(Qt.UserRole)
        try:
            self.preview_window.preview_file(file_path)
        except Exception as e:
            self.status_bar.setText(f"预览失败: {str(e)}")
            self.status_bar.setStyleSheet("color: red;")

class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setAcceptDrops(True)
        self.ConvertToHexButton.clicked.connect(self.convert_to_hex)
        self.extension_offset_map = {
            'png': '0',
            'exe': '64',
            'xml': '0',
            'pcapng': '6',
            'svg': '0',
            'vmdk': '0',
            'png_plain': '0',
            'exe_plain': '64',
            'xml_plain': '0',
            'pcapng_plain': '6',
            'svg_plain': '0',
            'jpg_plain': '0',
            'license_plain': '0'
        }
        self.compressedZipPath = ''
        self.plainZipPath = ''
        self.plainFilePath = ''
        self.filesToCompress = []
        self.command_thread = None
        self.compression_mode = None  # 存储压缩模式: 'store' 或 'deflate'
        self.bind()

        # 添加粉色预览按钮
        self.PreviewButton = PushButton("预览文件")
        self.PreviewButton.setMinimumHeight(35)
        self.PreviewButton.setProperty("previewButton", "true")
        self.PreviewButton.setStyleSheet("""
            QPushButton[previewButton="true"] {
                background-color: rgb(255, 105, 180);
                color: white;
                border-radius: 5px;
                border: none;
                padding: 10px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton[previewButton="true"]:hover {
                background-color: rgb(255, 130, 200);
            }
            QPushButton[previewButton="true"]:pressed {
                background-color: rgb(220, 80, 150);
            }
        """)
        self.PreviewButton.clicked.connect(self.preview_selected_file)

        # 将预览按钮添加到布局中
        target_file_layout = self.findChild(QHBoxLayout)  # 根据实际情况调整
        if target_file_layout:
            target_file_layout.insertWidget(2, self.PreviewButton)

    def preview_selected_file(self):
        if not self.compressedZipPath:
            QMessageBox.warning(self, "警告", "请先选择加密压缩包")
            return

        # 检查压缩模式
        if not self.compression_mode:
            QMessageBox.warning(self, "警告", "请先查看压缩包信息以确定压缩模式")
            return

        try:
            with zipfile.ZipFile(self.compressedZipPath, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                print("压缩包内文件列表:", file_list)

                if not file_list:
                    QMessageBox.warning(self, "警告", "压缩包中没有文件")
                    return

                temp_dir = tempfile.mkdtemp(prefix="bkcrack_preview_")
                print("临时目录路径:", temp_dir)

                temp_files = []
                key = self.InputKey.toPlainText().strip()

                if self.compression_mode == 'store':
                    # 存储模式 - 使用原有逻辑
                    for file in file_list:
                        temp_path = os.path.join(temp_dir, os.path.basename(file))
                        print("正在处理文件:", file, "=>", temp_path)

                        if key:
                            key_parts = key.split()
                            if len(key_parts) == 3:
                                command = ["bkcrack.exe", "-C", self.compressedZipPath,
                                           "-c", file, "-k", *key_parts, "-d", temp_path]
                                result = subprocess.run(command, capture_output=True, text=True)
                                print("解密命令输出:", result.stdout)
                                if result.returncode != 0:
                                    print("解密失败:", result.stderr)
                                    continue

                        else:
                            with zipfile.ZipFile(self.compressedZipPath, 'r') as zip_ref:
                                zip_ref.extract(file, temp_dir)

                        if os.path.exists(temp_path):
                            temp_files.append(temp_path)
                            print("文件提取成功:", temp_path)
                        else:
                            print("文件提取失败:", temp_path)

                elif self.compression_mode == 'deflate':
                    # 压缩模式 - 使用-U命令创建新压缩包，然后用7-Zip解压
                    output_zip = os.path.join(temp_dir, "1.zip")
                    password = "1"  # 固定密码

                    # 提示用户
                    self.append_colored_output(f"\n检测到压缩模式为: {self.compression_mode}", QColor("cyan"))
                    self.append_colored_output("将自动使用 -U 命令创建新压缩包 (密码:1) ", QColor("cyan"))
                    self.append_colored_output(f"输出路径: {output_zip}", QColor("cyan"))

                    # 执行-U命令
                    key_parts = key.split()
                    if len(key_parts) == 3:
                        command = ["bkcrack.exe", "-C", self.compressedZipPath,
                                   "-c", file_list[0], "-k", *key_parts, "-U", output_zip, password]
                        result = subprocess.run(command, capture_output=True, text=True)
                        print("U命令输出:", result.stdout)

                        if os.path.exists(output_zip):
                            # 使用7-Zip解压
                            seven_zip_path = self.find_7zip()
                            if seven_zip_path:
                                extract_dir = temp_dir
                                seven_zip_command = [
                                    seven_zip_path,
                                    "x",
                                    f"-p{password}",
                                    output_zip,
                                    f"-o{extract_dir}",
                                    "-y"
                                ]

                                try:
                                    result = subprocess.run(
                                        seven_zip_command,
                                        capture_output=True,
                                        text=True
                                    )

                                    if result.returncode == 0:
                                        # 获取解压后的文件列表
                                        for root, _, files in os.walk(extract_dir):
                                            for file in files:
                                                if file != "1.zip":  # 排除压缩包本身
                                                    temp_files.append(os.path.join(root, file))
                                        print("7-Zip解压成功")
                                    else:
                                        print("7-Zip解压失败:", result.stderr)
                                        # 如果7-Zip失败，尝试使用Python的zipfile模块
                                        try:
                                            with zipfile.ZipFile(output_zip, 'r') as zip_ref:
                                                zip_ref.extractall(extract_dir, pwd=password.encode('utf-8'))
                                            # 再次获取文件列表
                                            for root, _, files in os.walk(extract_dir):
                                                for file in files:
                                                    if file != "1.zip":
                                                        temp_files.append(os.path.join(root, file))
                                            print("使用zipfile模块解压成功")
                                        except Exception as e:
                                            print("zipfile解压失败:", str(e))
                                except Exception as e:
                                    print("7-Zip执行出错:", str(e))
                            else:
                                print("未找到7-Zip，尝试使用Python的zipfile模块")
                                try:
                                    with zipfile.ZipFile(output_zip, 'r') as zip_ref:
                                        zip_ref.extractall(temp_dir, pwd=password.encode('utf-8'))
                                    # 获取解压后的文件列表
                                    for root, _, files in os.walk(temp_dir):
                                        for file in files:
                                            if file != "1.zip":
                                                temp_files.append(os.path.join(root, file))
                                    print("使用zipfile模块解压成功")
                                except Exception as e:
                                    print("zipfile解压失败:", str(e))
                        else:
                            print("U命令执行失败，未生成输出文件")

                if not temp_files:
                    raise Exception("没有成功提取任何文件")

                print("最终可预览文件列表:", temp_files)
                preview = MultiFilePreviewWindow(self)
                preview.set_files(temp_files)
                preview.exec()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法预览文件: {str(e)}")
        finally:
            QtCore.QTimer.singleShot(0, lambda: self.cleanup_temp_files(temp_dir))

    def find_7zip(self):
        """查找7-Zip可执行文件路径"""
        # 检查常见安装路径
        possible_paths = [
            "C:\\Program Files\\7-Zip\\7z.exe",
            "C:\\Program Files (x86)\\7-Zip\\7z.exe",
            "D:\\压缩\\7-Zip\\7z.exe",
            os.path.join(os.environ.get("ProgramFiles", ""), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "7-Zip", "7z.exe"),
            os.path.join(os.environ.get("压缩", ""), "7-Zip", "7z.exe"),
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 检查PATH环境变量
        try:
            result = subprocess.run(["where", "7z"], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass

        return None

    def cleanup_temp_files(self, temp_dir):
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"清理临时文件时出错: {str(e)}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.zip'):
                # 检查是否拖拽到压缩包区域
                if self.ViewCompressedZip.geometry().contains(event.position().toPoint()):
                    self.UpdateCompressedFilePath(file_path)
                    self.append_colored_output(f"已拖拽选择加密压缩包(-C): {file_path}", QColor("yellow"))
                    self.get_zip_contents(file_path, is_encrypted=True)
                else:
                    # 拖拽到其他区域视为明文压缩包
                    self.plainZipPath = file_path
                    self.CompressOutputPath.setPlainText(file_path)
                    self.append_colored_output(f"已拖拽选择明文压缩包(-P): {file_path}", QColor("yellow"))
                    self.get_zip_contents(file_path, is_encrypted=False)
            else:
                self.UpdatePlainFilePath(file_path)
                self.append_colored_output(f"已拖拽选择明文文件(-p): {file_path}", QColor("yellow"))
                self.auto_fill_offset_from_path(file_path)
                self.PlainTextContent.setPlainText(os.path.basename(file_path))

    def clear_all(self):
        """清除所有输入和输出"""
        # 清除路径变量
        self.compressedZipPath = ''
        self.plainZipPath = ''
        self.plainFilePath = ''
        self.filesToCompress = []
        self.compression_mode = None

        # 清除UI元素
        self.ViewCompressedZip.clear()
        self.ViewPlainFile.clear()
        self.TargetFileCombo.clear()
        self.OffsetInput.clear()
        self.PlainTextContent.clear()
        self.InputKey.clear()
        self.OutputZipEdit.clear()
        self.NewPasswordEdit.clear()
        self.HexOffsetInput.clear()
        self.HexPatternInput.clear()
        self.DirectHexOffsetInput.clear()
        self.DirectHexPatternInput.clear()
        self.FilesToCompressInput.clear()
        self.CompressPasswordInput.clear()
        self.CompressOutputPath.clear()
        self.PasswordLengthInput.clear()
        self.OutPutArea.clear()

        # 停止正在运行的线程
        if self.command_thread and self.command_thread.isRunning():
            self.command_thread.stop()
            self.command_thread.quit()
            self.command_thread.wait()

        self.append_colored_output("已清除所有输入和输出", QColor("cyan"))

    def stop_attack(self):
        """停止当前正在进行的攻击"""
        if self.command_thread and self.command_thread.isRunning():
            self.command_thread.stop()
            self.command_thread.quit()
            self.command_thread.wait()
            self.append_colored_output("已停止当前攻击", QColor("red"))
        else:
            self.append_colored_output("没有正在运行的攻击", QColor("yellow"))

    def recover_password(self):
        """Recover password using bkcrack's -r option"""
        key = self.InputKey.toPlainText()
        if not key:
            self.append_colored_output("请先输入密钥", QColor("red"))
            return

        key_parts = key.strip().split()
        if len(key_parts) != 3:
            self.append_colored_output("密钥格式不正确，应为3个部分", QColor("red"))
            return

        # Get password length range
        length_range = self.PasswordLengthInput.toPlainText().strip()
        if not length_range:
            self.append_colored_output("请输入密码长度范围 (如: 10 或 8..12)", QColor("red"))
            return

        # Build command
        command = ["bkcrack.exe", "-k", *key_parts, "-r", length_range, "?p"]

        self.append_colored_output("\n正在尝试恢复密码...", QColor("yellow"))
        self.append_colored_output("执行命令: " + " ".join(command), QColor("yellow"))

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True
            )

            output_lines = []
            password = ""
            hex_repr = ""

            while True:
                line = process.stdout.readline()
                if not line:
                    break
                output_lines.append(line.strip())
                self.append_colored_output(line.strip(), QColor("yellow"))

                # 优先从"as text:"行获取完整密码(包含空格)
                if "as text:" in line:
                    password = line.split(":", 1)[1].strip().strip('"\'')
                # 其次从"as bytes:"行获取十六进制表示
                elif "as bytes:" in line:
                    hex_repr = line.split(":", 1)[1].strip()
                # 最后从"Password:"行获取(如果没有找到其他来源)
                elif "Password:" in line and not password:
                    password = line.split(":", 1)[1].strip()

            process.wait()

            if password:
                # 确保从十六进制还原密码(最准确)
                if hex_repr:
                    try:
                        # 从十六进制字符串还原密码(包含空格)
                        hex_chars = hex_repr.split()
                        password_bytes = bytes.fromhex("".join(hex_chars))
                        password = password_bytes.decode('utf-8', errors='replace')
                    except:
                        pass

                self.append_colored_output(f"\n✅ 密码恢复成功!", QColor("lightgreen"))

                # 显示密码(空格显示为[空格])
                display_password = password.replace(" ", "[空格]")
                self.append_colored_output(f"恢复的密码: {display_password}", QColor("lightgreen"))

                if hex_repr:
                    self.append_colored_output(f"十六进制表示: {hex_repr}", QColor("lightgreen"))

                # 密码分析(使用从十六进制还原的密码)
                self.analyze_password(password)
            else:
                self.append_colored_output("\n❌ 无法恢复密码", QColor("red"))

        except Exception as e:
            self.append_colored_output(f"密码恢复过程中出错: {str(e)}", QColor("red"))

    def analyze_password(self, password):
        """Analyze the recovered password and show special characters"""
        self.append_colored_output("\n密码分析:", QColor("cyan"))

        # 显示实际密码内容(空格显示为[空格])
        display_password = password.replace(" ", "[空格]")
        self.append_colored_output(f"显示密码: {display_password}", QColor("cyan"))

        # 特殊字符分析
        special_chars = " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        analyzed = []
        for char in password:
            if char == " ":
                analyzed.append('[空格]')
            elif char in special_chars:
                analyzed.append(f'[{char}]')
            else:
                analyzed.append(char)

        self.append_colored_output(f"字符分析: {''.join(analyzed)}", QColor("cyan"))

        # 十六进制表示
        hex_repr = binascii.hexlify(password.encode('utf-8')).decode('utf-8')
        formatted_hex = ' '.join([hex_repr[i:i + 2] for i in range(0, len(hex_repr), 2)])
        self.append_colored_output(f"完整十六进制: {formatted_hex}", QColor("cyan"))

        # 长度信息
        self.append_colored_output(f"实际长度: {len(password)} 字符", QColor("cyan"))
        self.append_colored_output(f"显示长度: {len(display_password.replace('[空格]', ' '))} 字符", QColor("cyan"))

    def direct_extract_file(self):
        """最终解决方案：智能处理文件名和路径问题"""
        key = self.InputKey.toPlainText()
        if not key:
            self.append_colored_output("请先输入密钥", QColor("red"))
            return

        target_file = self.TargetFileCombo.currentText()
        if not target_file:
            self.append_colored_output("请先输入目标文件(-c)", QColor("red"))
            return

        # 1. 首先验证压缩包内容
        try:
            with zipfile.ZipFile(self.compressedZipPath, 'r') as zip_ref:
                # 获取压缩包内实际文件名列表（考虑大小写）
                real_files = zip_ref.namelist()

                # 查找匹配的文件（不区分大小写）
                matched_files = [f for f in real_files if f.lower() == target_file.lower()]

                if not matched_files:
                    self.append_colored_output("\n❌ 压缩包中找不到匹配的文件", QColor("red"))
                    self.append_colored_output("压缩包实际内容:", QColor("cyan"))
                    for f in real_files:
                        self.append_colored_output(f" - {f}", QColor("cyan"))
                    return

                # 使用压缩包中的实际文件名（保持大小写一致）
                actual_file = matched_files[0]
        except Exception as e:
            self.append_colored_output(f"\n❌ 无法读取压缩包: {str(e)}", QColor("red"))
            return

        # 2. 准备导出参数
        key_parts = key.strip().split()
        if len(key_parts) != 3:
            self.append_colored_output("密钥格式不正确，应为3个部分", QColor("red"))
            return

        # 3. 获取输出路径（当前目录）
        output_dir = os.path.dirname(os.path.abspath(__file__))
        pure_filename = os.path.basename(actual_file)
        output_path = os.path.join(output_dir, pure_filename)

        # 处理重名文件
        counter = 1
        base_name, ext = os.path.splitext(pure_filename)
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base_name}_{counter}{ext}")
            counter += 1

        # 4. 执行导出命令（使用实际文件名）
        original_dir = os.getcwd()
        os.chdir(output_dir)

        try:
            command = ["bkcrack.exe", "-C", self.compressedZipPath,
                       "-c", actual_file, "-k", *key_parts, "-d", pure_filename]

            self.append_colored_output("正在直接导出文件...", QColor("yellow"))
            self.append_colored_output(f"执行命令: {' '.join(command)}", QColor("yellow"))
            self.append_colored_output(f"文件将导出到: {output_path}", QColor("yellow"))

            process = subprocess.run(command, capture_output=True, text=True, cwd=output_dir)

            # 输出结果
            self.append_colored_output(process.stdout, QColor("yellow"))
            if process.stderr:
                self.append_colored_output(process.stderr, QColor("red"))

            # 5. 检查结果
            if os.path.exists(pure_filename):
                # 如果文件名与预期不同（大小写问题），重命名
                if pure_filename != os.path.basename(output_path):
                    os.rename(pure_filename, output_path)
                self.append_colored_output(f"\n✅ 文件已成功导出到: {output_path}", QColor("lightgreen"))
            else:
                self.append_colored_output("\n❌ 导出失败！可能原因:", QColor("red"))
                self.append_colored_output(f"1. 密钥不正确（当前密钥: {' '.join(key_parts)})", QColor("red"))
                self.append_colored_output("2. 压缩包已损坏,如果是两部分，建议第一部分就使用-d", QColor("red"))
                self.append_colored_output("3. 文件权限问题", QColor("red"))

        finally:
            os.chdir(original_dir)

    def update_output_and_check(self, text, output_path):
        """更新输出并检查文件是否成功导出"""
        self.update_output(text)

        if "Writing deciphered data" in text and os.path.exists(output_path):
            self.append_colored_output(f"\n✅ 文件已成功导出到: {output_path}", QColor("lightgreen"))
        elif "Zip error" in text:
            self.append_colored_output("\n❌ 导出失败！可能原因：", QColor("red"))
            self.append_colored_output("1. 目标文件在压缩包中不存在", QColor("red"))
            self.append_colored_output("2. 密钥不正确", QColor("red"))
            self.append_colored_output("3. 压缩包已损坏", QColor("red"))

    def bind(self):
        self.SelectCompressedFile.clicked.connect(self.select_compressed_file)
        self.CompressedZipInfo.clicked.connect(self.GetCompressedZipInfo)
        self.SelectPlainFile.clicked.connect(self.select_plain_file)
        self.StartAttack.clicked.connect(self.Attack)
        self.ExportZip.clicked.connect(self.DoExportZip)
        self.ExecuteHexButton.clicked.connect(self.execute_hex_command)
        self.ChangePasswordButton.clicked.connect(self.change_password)
        self.OutPutArea.setOpenExternalLinks(True)
        self.ReadZipEntriesButton.clicked.connect(self.read_zip_entries)
        self.DirectExtractButton.clicked.connect(self.direct_extract_file)
        self.RecoverPasswordButton.clicked.connect(self.recover_password)

        # Compression functionality
        self.SelectFilesToCompress.clicked.connect(self.select_files_to_compress)
        self.CompressDeflateButton.clicked.connect(lambda: self.compress_files('deflate'))
        self.CompressStoreButton.clicked.connect(lambda: self.compress_files('store'))
        self.UsePlainZipButton.clicked.connect(self.use_plain_zip_for_attack)

        # 添加选择已有压缩包按钮
        self.SelectPlainZipButton = PushButton("选择自己压缩的明文压缩包")
        self.SelectPlainZipButton.setMinimumHeight(35)
        self.SelectPlainZipButton.setProperty("execButton", True)  # 设置相同属性
        self.SelectPlainZipButton.setStyleSheet("""
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
          """)
        self.SelectPlainZipButton.clicked.connect(self.select_existing_plain_zip)

        # 将新按钮添加到布局中
        compress_group = None
        # 查找所有QGroupBox
        for child in self.findChildren(QGroupBox):
            if child.title() == "创建明文压缩包(-P 可选)":
                compress_group = child
                break

        if compress_group:
            compress_layout = compress_group.layout()
            # 在"用作明文压缩包"按钮前添加新按钮
            compress_layout.insertWidget(compress_layout.count() - 1, self.SelectPlainZipButton)

        # Direct hex pattern attack button
        self.DirectHexAttackButton.clicked.connect(self.direct_hex_attack)

        # 新增按钮
        self.ClearAllButton.clicked.connect(self.clear_all)
        self.StopAttackButton.clicked.connect(self.stop_attack)

    def select_existing_plain_zip(self):
        """选择已有的明文压缩包"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择明文压缩包", "", "ZIP Files (*.zip);;All Files (*)")
        if file_path:
            self.plainZipPath = file_path
            self.CompressOutputPath.setPlainText(file_path)
            self.append_colored_output(f"已选择明文压缩包(-P): {file_path}", QColor("yellow"))
            self.get_zip_contents(file_path, is_encrypted=False)

    def select_compressed_file(self):
        """选择加密压缩包文件"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择加密压缩包", "", "ZIP Files (*.zip);;All Files (*)")
        if file_path:
            self.UpdateCompressedFilePath(file_path)
            self.append_colored_output(f"已选择加密压缩包: {file_path}", QColor("yellow"))
            self.get_zip_contents(file_path, is_encrypted=True)

    def select_plain_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择明文文件", "", "All Files (*)")
        if file_path:
            self.UpdatePlainFilePath(file_path)  # 更新明文文件路径
            self.append_colored_output(f"已选择明文文件: {file_path}", QColor("yellow"))
            self.auto_fill_offset_from_path(file_path)
            self.PlainTextContent.setPlainText(os.path.basename(file_path))

    def get_zip_contents(self, zip_path, is_encrypted=False):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if file_list:
                    prefix = "加密" if is_encrypted else "明文"
                    self.append_colored_output(f"{prefix}压缩包内文件列表:", QColor("cyan"))
                    for file in file_list:
                        self.append_colored_output(f" - {file}", QColor("cyan"))

                    # 自动填充目标文件下拉框
                    self.TargetFileCombo.clear()
                    self.TargetFileCombo.addItems(file_list)
                    if file_list:
                        self.append_colored_output(f"已自动填充目标文件列表，当前选择: {file_list[0]}       (友情提醒:在攻击前请注意这个位置的参数部分)", QColor("yellow"))
        except Exception as e:
            self.append_colored_output(f"无法读取压缩包内容: {str(e)}", QColor("red"))

    def read_zip_entries(self):
        """保留此方法以兼容旧代码，但实际功能已整合到get_zip_contents中"""
        zip_path = self.ViewCompressedZip.toPlainText().strip()
        if not zip_path:
            QMessageBox.warning(self, "警告", "请先选择加密压缩包路径")
            return
        self.get_zip_contents(zip_path, is_encrypted=True)

    def GetCompressedZipInfo(self):
        if not self.compressedZipPath:
            self.append_colored_output("请先选择加密压缩包", QColor("red"))
            return

        # 清空输出区域
        self.OutPutArea.clear()

        # 第一部分：运行 bkcrack -L 命令获取压缩包信息
        self.append_colored_output("\n=== bkcrack 信息 ===\n", QColor("cyan"))
        command = ["bkcrack.exe", "-L", self.compressedZipPath]
        try:
            result = subprocess.run(command,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    encoding='utf-8',
                                    errors='replace')

            if result.returncode == 0:
                self.OutPutArea.insertPlainText(result.stdout)

                # 初始化标志变量
                store_detected = False
                deflate_detected = False

                # 检查是否包含特定关键词
                if "Store" in result.stdout:
                    self.append_colored_output("检测到加密存储模式", QColor("white"))
                    store_detected = True
                    self.compression_mode = 'store'
                if "Deflate" in result.stdout:
                    self.append_colored_output("检测到加密压缩模式", QColor("white"))
                    deflate_detected = True
                    self.compression_mode = 'deflate'

                # 如果两种模式都没有检测到
                if not store_detected and not deflate_detected:
                    self.append_colored_output("未检测到加密存储模式和加密压缩模式", QColor("white"))
                    self.compression_mode = None
            else:
                self.append_colored_output(f"bkcrack命令执行失败:\n{result.stderr}", QColor("red"))
                return
        except Exception as e:
            self.append_colored_output(f"执行bkcrack命令时出错: {str(e)}", QColor("red"))
            return

        # 第二部分：自动填充目标文件
        try:
            with zipfile.ZipFile(self.compressedZipPath, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if file_list:
                    self.TargetFileCombo.clear()
                    self.TargetFileCombo.addItems(file_list)
                    self.append_colored_output(f"\n已自动填充目标文件列表，当前选择: {file_list[0]}     (友情提醒:在攻击前请注意这个位置的参数部分)", QColor("yellow"))
        except Exception as e:
            self.append_colored_output(f"\n无法读取压缩包内容: {str(e)}", QColor("red"))

        # 第三部分：显示ZIP创建者信息
        self.append_colored_output("\n=== 压缩包元数据信息 ===\n", QColor("cyan"))
        try:
            creator_info = self.detect_zip_creator(self.compressedZipPath)
            self.OutPutArea.insertPlainText(creator_info)
        except Exception as e:
            self.append_colored_output(f"获取元数据失败: {str(e)}", QColor("red"))

    def detect_zip_creator(self, zip_path):
        """检测ZIP文件的创建者信息"""
        version_map = {
            10: "PKZIP 1.0",
            20: "Bandizip 7.06 / Windows自带",
            21: "PKZIP 2.0",
            25: "PKZIP 2.5",
            27: "PKZIP 2.7",
            31: "WinRAR 4.20 / WinRAR 5.70 ",
            45: "PKZIP 4.5",
            46: "PKZIP 4.6",
            50: "PKZIP 5.0",
            62: "PKZIP 6.2",
            63: "7-Zip / 360压缩"
        }

        os_map = {
            0: "MS-DOS和OS/2",
            1: "Amiga",
            2: "OpenVMS",
            3: "UNIX",
            4: "VM/CMS",
            5: "Atari ST",
            6: "OS/2 HPFS",
            7: "Macintosh",
            8: "Z-System",
            9: "CP/M",
            10: "Windows NTFS",
            11: "MVS",
            12: "VSE",
            13: "Acorn Risc",
            14: "VFAT",
            15: "Alternate MVS",
            16: "BeOS",
            17: "Tandem",
            18: "OS/400",
            19: "OS/X (Darwin)"
        }

        try:
            with open(zip_path, 'rb') as f:
                data = f.read()

            # 查找 Central Directory Header 签名
            signature = b'\x50\x4B\x01\x02'
            index = data.find(signature)
            if index == -1:
                return "未找到 Central Directory Header"

            # 提取 Version Made By 字段 (2字节)
            version_bytes = data[index + 4:index + 6]
            version_value = struct.unpack('<H', version_bytes)[0]

            # 分离高字节(操作系统)和低字节(PKZIP版本)
            os_id = version_value >> 8
            version_number = version_value & 0xFF

            # 获取软件和操作系统信息
            software = version_map.get(version_number, f"未知PKZIP版本 (0x{version_number:02X})")
            os_name = os_map.get(os_id, f"未知操作系统 (0x{os_id:02X})")

            # 检查是否有ZIP64格式
            zip64_signature = b'\x50\x4B\x06\x06'
            is_zip64 = zip64_signature in data

            info = (
                f"Version Made By: 0x{version_value:04X}\n"
                f" - 操作系统: {os_name}\n"
                f" - 压缩软件(可能): {software}\n"
                f" - ZIP64格式: {'是' if is_zip64 else '否'}\n"
            )
            if version_value == 0x001F:
                info += "\n提示：可以使用左上角工具按钮进行压缩(存储)操作"
            return info
        except Exception as e:
            return f"解析ZIP元数据时出错: {str(e)}"

    def _get_zip_os_name(self, os_id):
        """获取操作系统名称"""
        os_map = {
            0: "MS-DOS和OS/2",
            1: "Amiga",
            2: "OpenVMS",
            3: "UNIX",
            4: "VM/CMS",
            5: "Atari ST",
            6: "OS/2 HPFS",
            7: "Macintosh",
            8: "Z-System",
            9: "CP/M",
            10: "Windows NTFS",
            11: "MVS",
            12: "VSE",
            13: "Acorn Risc",
            14: "VFAT",
            15: "Alternate MVS",
            16: "BeOS",
            17: "Tandem",
            18: "OS/400",
            19: "OS/X (Darwin)"
        }
        return os_map.get(os_id, f"未知系统(0x{os_id:X})")

    def select_files_to_compress(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择要压缩的文件(用于-P)", "", "All Files (*)")
        if files:
            self.filesToCompress = files
            self.FilesToCompressInput.setPlainText("\n".join(files))
            self.append_colored_output(f"已选择 {len(files)} 个文件用于创建明文压缩包(-P)", QColor("yellow"))

    def compress_files(self, method):
        if not self.filesToCompress:
            self.append_colored_output("请先选择要压缩的文件", QColor("red"))
            return

        first_file = self.filesToCompress[0]
        dir_path = os.path.dirname(first_file)
        output_path = os.path.join(dir_path, f"{os.path.splitext(os.path.basename(first_file))[0]}.zip")

        password = self.CompressPasswordInput.toPlainText()
        if not password:
            self.append_colored_output("警告：未设置密码，将创建无密码压缩包", QColor("orange"))

        self.append_colored_output(f"开始使用 {method} 方法创建明文压缩包(-P)...", QColor("yellow"))

        try:
            compression = zipfile.ZIP_DEFLATED if method == 'deflate' else zipfile.ZIP_STORED
            compresslevel = 6  # 默认压缩级别

            # 直接处理原文件，按文件名排序
            file_paths = sorted(self.filesToCompress)

            with zipfile.ZipFile(output_path, 'w',
                                 compression=compression,
                                 compresslevel=compresslevel,
                                 strict_timestamps=False) as zipf:

                for file in file_paths:
                    arcname = os.path.basename(file)
                    if password:
                        zipf.setpassword(password.encode('utf-8'))
                        # 使用传统ZIP加密
                        zip_info = zipfile.ZipInfo.from_file(file, arcname)
                        zip_info.flag_bits = 0x800  # 设置标志位表示使用传统加密

                        with open(file, 'rb') as f:
                            data = f.read()
                        zipf.writestr(zip_info, data, compress_type=compression)
                    else:
                        zipf.write(file, arcname=arcname, compress_type=compression)

            self.append_colored_output(f"明文压缩包(-P)创建成功: {output_path}", QColor("lightgreen"))
            self.CompressOutputPath.setPlainText(output_path)
            self.get_zip_contents(output_path, is_encrypted=False)

        except Exception as e:
            self.append_colored_output(f"压缩过程中出错: {str(e)}", QColor("red"))

    def use_plain_zip_for_attack(self):
        plain_zip_path = self.CompressOutputPath.toPlainText()
        if not plain_zip_path:
            self.append_colored_output("请先创建或选择明文压缩包(-P)", QColor("red"))
            return

        self.plainZipPath = plain_zip_path
        self.append_colored_output(f"已设置明文压缩包路径(-P): {plain_zip_path}", QColor("yellow"))

        # 自动设置明文文件为压缩包内第一个文件
        try:
            with zipfile.ZipFile(plain_zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                if file_list:
                    # 按字母排序选择第一个文件（与压缩时一致）
                    file_list.sort()
                    self.PlainTextContent.setPlainText(file_list[0])
                    self.append_colored_output(f"已自动设置明文文件(-p): {file_list[0]}", QColor("yellow"))
                    # 自动填充偏移量
                    self.auto_fill_offset_from_path(file_list[0])
        except Exception as e:
            self.append_colored_output(f"无法读取压缩包内容: {str(e)}", QColor("red"))

    def auto_fill_offset_from_path(self, path):
        """改进的自动填充偏移量方法，处理带_plain后缀的情况"""
        # 获取文件名和扩展名
        filename = os.path.basename(path).lower()
        base, ext = os.path.splitext(filename)
        ext = ext[1:]  # 去掉点

        # 检查是否有_plain后缀
        if '_plain' in base:
            # 提取主扩展名
            main_ext = base.split('_plain')[0]
            # 检查组合扩展名是否在映射表中
            combined_ext = f"{main_ext}_plain"
            if combined_ext in self.extension_offset_map:
                offset = self.extension_offset_map[combined_ext]
                self.OffsetInput.setPlainText(offset)
                self.append_colored_output(f"自动填充偏移量(带_plain后缀): {offset}", QColor("yellow"))
                return

        # 检查普通扩展名
        if ext in self.extension_offset_map:
            offset = self.extension_offset_map[ext]
            self.OffsetInput.setPlainText(offset)
            self.append_colored_output(f"自动填充偏移量: {offset}", QColor("yellow"))
            return

        # 检查文件名中的关键字
        for keyword, offset in self.extension_offset_map.items():
            if keyword in filename:
                self.OffsetInput.setPlainText(offset)
                self.append_colored_output(f"根据关键字 '{keyword}' 自动填充偏移量: {offset}", QColor("yellow"))
                return

    def UpdatePlainFilePath(self, path):
        self.plainFilePath = path
        self.ViewPlainFile.setPlainText(path)

    def UpdateCompressedFilePath(self, path):
        self.compressedZipPath = path
        self.ViewCompressedZip.setPlainText(path)

    def Attack(self):
        target_file = self.TargetFileCombo.currentText().strip()  # 从下拉框获取当前选中的文件
        plain_file_content = self.PlainTextContent.toPlainText().strip()  # 明文文件内容（通常是文件名）
        plain_file_path = self.ViewPlainFile.toPlainText().strip()  # 明文文件路径
        plain_zip_path = self.plainZipPath  # 明文压缩包路径
        offset = self.OffsetInput.toPlainText().strip()

        if not self.compressedZipPath:
            self.append_colored_output("请先选择加密压缩包(-C)", QColor("red"))
            return

        # 验证目标文件是否存在于加密压缩包中
        try:
            with zipfile.ZipFile(self.compressedZipPath, 'r') as zip_ref:
                if target_file not in zip_ref.namelist():
                    self.append_colored_output(f"错误：目标文件 '{target_file}' 不在加密压缩包中", QColor("red"))
                    self.append_colored_output("加密压缩包内文件列表:", QColor("cyan"))
                    for file in zip_ref.namelist():
                        self.append_colored_output(f" - {file}", QColor("cyan"))
                    return
        except Exception as e:
            self.append_colored_output(f"无法验证加密压缩包内容: {str(e)}", QColor("red"))
            return

        # 构建命令
        command = ["bkcrack.exe", "-C", self.compressedZipPath, "-c", target_file]

        # 处理明文来源
        if plain_zip_path:
            # 使用明文压缩包(-P)
            command.extend(["-P", plain_zip_path])

            # 检查明文文件是否在明文压缩包中
            if plain_file_content:
                try:
                    with zipfile.ZipFile(plain_zip_path, 'r') as zip_ref:
                        if plain_file_content not in zip_ref.namelist():
                            self.append_colored_output(f"错误：明文文件 '{plain_file_content}' 不在明文压缩包中", QColor("red"))
                            self.append_colored_output("明文压缩包内文件列表:", QColor("cyan"))
                            for file in zip_ref.namelist():
                                self.append_colored_output(f" - {file}", QColor("cyan"))
                            return
                except Exception as e:
                    self.append_colored_output(f"无法验证明文压缩包内容: {str(e)}", QColor("red"))
                    return

                command.extend(["-p", plain_file_content])
        elif plain_file_path:
            # 使用单独的明文文件(-p)
            if not os.path.exists(plain_file_path):
                self.append_colored_output(f"错误：明文文件 '{plain_file_path}' 不存在", QColor("red"))
                return
            command.extend(["-p", plain_file_path])
        else:
            self.append_colored_output("请提供明文文件(-p)或明文压缩包(-P)", QColor("red"))
            return

        # 添加偏移量
        if offset:
            command.extend(["-o", offset])

        self.OutPutArea.clear()
        self.append_colored_output("正在执行攻击命令: " + " ".join(command), QColor("yellow"))
        self.append_colored_output("正在进行攻击，请稍等...", QColor("yellow"))

        self.command_thread = CommandThread(" ".join(command))
        self.command_thread.output_signal.connect(self.update_output)
        self.command_thread.start()

    def execute_hex_command(self):
        target_file = self.TargetFileCombo.currentText()  # 从下拉框获取当前选中的文件
        hex_offset = self.HexOffsetInput.toPlainText()
        hex_pattern = self.HexPatternInput.toPlainText()

        if not all([target_file, hex_offset, hex_pattern]):
            self.append_colored_output("请确保填写了目标文件(-c)、目标文件偏移地址和部分已知明文值", QColor("red"))
            return

        # 验证目标文件是否存在于压缩包中
        try:
            with zipfile.ZipFile(self.compressedZipPath, 'r') as zip_ref:
                if target_file not in zip_ref.namelist():
                    self.append_colored_output(f"错误：目标文件 '{target_file}' 不在压缩包中", QColor("red"))
                    self.append_colored_output("压缩包内文件列表:", QColor("cyan"))
                    for file in zip_ref.namelist():
                        self.append_colored_output(f" - {file}", QColor("cyan"))
                    return
        except Exception as e:
            self.append_colored_output(f"无法验证压缩包内容: {str(e)}", QColor("red"))
            return

        command = ["bkcrack.exe", "-C", self.compressedZipPath,
                   "-c", target_file, "-x", hex_offset, hex_pattern]

        plain_file_path = self.ViewPlainFile.toPlainText()
        plain_zip_path = self.plainZipPath
        plain_file_content = self.PlainTextContent.toPlainText()

        # 处理明文来源
        if plain_zip_path:
            command.extend(["-P", plain_zip_path])

            if plain_file_content:
                command.extend(["-p", plain_file_content])
        elif plain_file_path:
            command.extend(["-p", plain_file_path])
        elif plain_file_content:
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
                    tmp.write(plain_file_content)
                    temp_file = tmp.name
                command.extend(["-p", temp_file])
            except Exception as e:
                self.append_colored_output(f"创建临时明文文件失败: {str(e)}", QColor("red"))
                return
        else:
            self.append_colored_output("请提供明文文件(-p)或明文压缩包(-P)", QColor("red"))
            return

        # 添加偏移量
        offset = self.OffsetInput.toPlainText()
        if offset.strip():
            command.extend(["-o", offset.strip()])

        self.OutPutArea.clear()
        self.append_colored_output("正在执行攻击命令: " + " ".join(command), QColor("yellow"))
        self.append_colored_output("正在执行(-x)情况下攻击，请稍等...", QColor("yellow"))

        self.command_thread = CommandThread(" ".join(command))
        if 'temp_file' in locals():
            self.command_thread.set_temp_file(temp_file)
        self.command_thread.output_signal.connect(self.update_output)
        self.command_thread.start()

    def direct_hex_attack(self):
        """直接执行 bkcrack -C attachment.zip -c flag.zip -x 172 504B05060000000001000100 模式的攻击"""
        if not self.compressedZipPath:
            self.append_colored_output("请先选择加密压缩包(-C)", QColor("red"))
            return

        target_file = self.TargetFileCombo.currentText().strip()
        if not target_file:
            self.append_colored_output("请选择目标文件(-c)", QColor("red"))
            return

        hex_offset = self.DirectHexOffsetInput.toPlainText().strip()
        hex_pattern = self.DirectHexPatternInput.toPlainText().strip()
        if not hex_offset or not hex_pattern:
            self.append_colored_output("请填写目标文件偏移地址和部分已知明文值", QColor("red"))
            return

        # 分割多个偏移和模式
        offsets = hex_offset.split(';')
        patterns = hex_pattern.split(';')

        if len(offsets) != len(patterns):
            self.append_colored_output("偏移地址和已知明文值的数量不匹配", QColor("red"))
            return

        # 构建基本命令
        command = ["bkcrack.exe", "-C", self.compressedZipPath, "-c", target_file]

        # 添加多个-x参数
        for offset, pattern in zip(offsets, patterns):
            command.extend(["-x", offset.strip(), pattern.strip()])

        self.OutPutArea.clear()
        self.append_colored_output("正在执行(-x)攻击命令: " + " ".join(command), QColor("yellow"))
        self.append_colored_output("正在进行攻击，请稍等...", QColor("yellow"))

        self.command_thread = CommandThread(" ".join(command))
        self.command_thread.output_signal.connect(self.update_output)
        self.command_thread.start()

    def convert_to_hex(self):
        """将输入内容转换为16进制表示"""
        input_text = self.HexConversionInput.toPlainText().strip()
        if not input_text:
            self.append_colored_output("请输入要转换的内容", QColor("red"))
            return

        try:
            # 转换为16进制字符串，不添加空格
            hex_str = input_text.encode('utf-8').hex().upper()

            self.append_colored_output("输入内容: " + input_text, QColor("yellow"))
            self.append_colored_output("16进制表示: " + hex_str, QColor("yellow"))

            # 自动复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(hex_str)
            self.append_colored_output("已复制16进制结果到剪贴板", QColor("yellow"))

        except Exception as e:
            self.append_colored_output(f"转换失败: {str(e)}", QColor("red"))

    def update_output(self, text):
        if "Keys:" in text:
            key = text.split(":", 1)[1].strip()
            self.InputKey.setPlainText(key)
            self.append_colored_output(f"攻击成功，密钥为: {key}", QColor("lightgreen"))
            self.append_colored_output("已自动提取密钥并填入密钥输入框！", QColor("lightgreen"))
            self.command_thread.terminate()
            return
        self.append_colored_output(text, QColor("yellow"))

    def DoExportZip(self):
        key = self.InputKey.toPlainText()
        if not key:
            self.append_colored_output("请先输入密钥", QColor("red"))
            return

        target_file = self.TargetFileCombo.currentText()  # 从下拉框获取当前选中的文件
        if not target_file:
            self.append_colored_output("请先输入目标文件(-c)", QColor("red"))
            return

        key_parts = key.strip().split()
        if len(key_parts) != 3:
            self.append_colored_output("密钥格式不正确，应为3个部分", QColor("red"))
            return

        output_path = os.path.splitext(self.compressedZipPath)[0] + "_NO_PASS.zip"
        command = ["bkcrack.exe", "-C", self.compressedZipPath,
                   "-c", target_file, "-k", *key_parts, "-D", output_path]

        self.append_colored_output("正在导出无密码压缩包...", QColor("yellow"))
        result = subprocess.run(" ".join(command), shell=True, capture_output=True, text=True)
        self.append_colored_output(result.stdout, QColor("yellow"))

        if os.path.exists(output_path):
            self.append_colored_output(f"导出成功！无密码压缩包路径：{output_path}", QColor("lightgreen"))
        else:
            self.append_colored_output("导出失败，请检查输出信息", QColor("red"))

    def change_password(self):
        key = self.InputKey.toPlainText()
        if not key:
            self.append_colored_output("请先输入密钥", QColor("red"))
            return

        target_file = self.TargetFileCombo.currentText()  # 从下拉框获取当前选中的文件
        if not target_file:
            self.append_colored_output("请先输入目标文件(-c)", QColor("red"))
            return

        output_zip = self.OutputZipEdit.toPlainText()
        if not output_zip:
            self.append_colored_output("请输入输出zip文件名", QColor("red"))
            return

        new_password = self.NewPasswordEdit.toPlainText()
        if not new_password:
            self.append_colored_output("请输入新密码", QColor("red"))
            return

        key_parts = key.strip().split()
        if len(key_parts) != 3:
            self.append_colored_output("密钥格式不正确，应为3个部分", QColor("red"))
            return

        output_zip = os.path.abspath(output_zip)

        command = ["bkcrack.exe", "-C", self.compressedZipPath,
                   "-c", target_file, "-k", *key_parts, "-U", output_zip, new_password]

        self.OutPutArea.clear()
        self.append_colored_output("正在修改密码并导出压缩包...", QColor("yellow"))
        result = subprocess.run(" ".join(command), shell=True, capture_output=True, text=True)
        self.append_colored_output(result.stdout, QColor("yellow"))

        if os.path.exists(output_zip):
            abs_path = os.path.abspath(output_zip)
            self.append_colored_output("\n✅ <b>导出成功！</b>", QColor("lightgreen"))
            self.append_colored_output(f"<b>新密码：</b><span style='color:lightgreen'>{new_password}</span>", QColor("lightgreen"))
            self.append_colored_output(f"<b>导出位置：</b><span style='color:cyan'>{abs_path}</span>", QColor("lightgreen"))
        else:
            self.append_colored_output("\n❌ <b>导出失败！</b>", QColor("red"))
            self.append_colored_output("请检查以下可能的问题：", QColor("red"))
            self.append_colored_output("1. 密钥是否正确", QColor("red"))
            self.append_colored_output("2. 目标文件路径是否正确", QColor("red"))
            self.append_colored_output("3. 输出路径是否有写入权限", QColor("red"))
            self.append_colored_output("4. 查看上方命令输出获取更多信息", QColor("red"))

    def append_colored_output(self, text, color):
        self.OutPutArea.setTextColor(color)
        self.OutPutArea.append(text)
        self.OutPutArea.setTextColor(QColor("yellow"))

    def append_output(self, text):
        self.OutPutArea.append(f"<span style='color:white;'>{text}</span>")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1200, 800)
    window.setWindowTitle("bkcrack-gui v0.92  Author: 星辰不及阁下")
    window.show()
    sys.exit(app.exec())