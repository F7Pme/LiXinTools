from enum import Enum
from PySide6.QtGui import QFont

class ColorPalette(Enum):
    BACKGROUND = "#F3F3F3"
    TITLEBAR_BG = "#F3F3F3"
    HOVER_BG = "#DBDBDB"
    CLOSE_HOVER = "#E81123"
    TEXT = "#333333"
    PRIMARY = "#0078D4"

class FontConfig:
    TITLE = ("Microsoft YaHei", 12)
    BUTTON = ("Segoe UI", 13)
    ICON = ("Segoe MDL2 Assets", 10)
    
    @staticmethod
    def get_high_quality_font(family, size=None, bold=False, pixel_size=None):
        """创建高质量字体对象，自动设置抗锯齿和高质量渲染

        Args:
            family: 字体族名称
            size: 字体点大小（与pixel_size二选一）
            bold: 是否加粗
            pixel_size: 字体像素大小（与size二选一）

        Returns:
            QFont: 配置好的高质量字体对象
        """
        font = QFont(family)
        
        if pixel_size is not None:
            font.setPixelSize(pixel_size)
        elif size is not None:
            font.setPointSize(size)
            
        if bold:
            font.setBold(True)
            
        # 设置高质量渲染策略
        font.setStyleStrategy(QFont.PreferAntialias | QFont.PreferQuality)
        
        return font

class Dimensions:
    WINDOW_RADIUS = 5
    TITLEBAR_HEIGHT = 32
    BUTTON_SIZE = (46, 32)
    SHADOW_BLUR = 12
    INPUT_PADDING = 10

class StyleSheet:
    
    @classmethod
    def window_style(cls):
        return f"""
        QWidget#MainContainer {{
            background: {ColorPalette.BACKGROUND.value};
            border-radius: {Dimensions.WINDOW_RADIUS}px;
        }}
        """
    
    @classmethod
    def titlebar_style(cls):
        return f"""
        background: {ColorPalette.TITLEBAR_BG.value};
        border-top-left-radius: {Dimensions.WINDOW_RADIUS}px;
        border-top-right-radius: {Dimensions.WINDOW_RADIUS}px;
        """
    
    @classmethod
    def button_style(cls):
        return f"""
        QPushButton {{
            background: transparent;
            border: none;
            padding: 0;
            margin: 0;
            min-width: {Dimensions.BUTTON_SIZE[0]}px;
            min-height: {Dimensions.BUTTON_SIZE[1]}px;
            font-family: '{FontConfig.ICON[0]}';
            font-size: {FontConfig.ICON[1]}px;
            color: {ColorPalette.TEXT.value};
            border-radius: 0px;
        }}
        QPushButton:hover {{
            background: {ColorPalette.HOVER_BG.value};
        }}
        """

    @classmethod
    def close_button_style(cls):
        return f"""
        QPushButton {{
            border-top-right-radius: {Dimensions.WINDOW_RADIUS}px;
        }}
        QPushButton:hover {{
            background: {ColorPalette.CLOSE_HOVER.value} !important;
            color: white;
        }}
        """