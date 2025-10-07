main_window = """
            QMainWindow {
                background-color: #161616;
            }
            QComboBox {
                background-color: rgba(255,255,255,120);
                color: white;
            }
            QLineEdit {
                background-color: rgba(255,255,255,120);
                color: white;
            }
            QListView {
                background-color: rgba(255,255,255,0.4);
                color: white;
            }
                QListView::item {
                    background-color: transparent;
                    padding: 5px;
                        border: none;  /* 移除边框 */
                        outline: none;  /* 移除轮廓 */
                }
                QListView::item:selected {
                    background-color: #6B69D6;
                    color: white;
                        border: none;  /* 移除边框 */
                        outline: none;  /* 移除轮廓 */
                }
                QListView::item:hover {
                    background-color: rgba(107, 105, 214, 0.4);
                }
            QTabWidget {
                background-color: transparent;
                color: white;
            }
            QWidget {
                background-color: transparent;
                color: white;
            }
            QLabel {
                border: none;
            }
            QPushButton {
                background-color: #242424aa;
                color: white;
            }
            QPushButton:hover {
                background-color: #807EDC;
            }
            /* 设置垂直滚动条 */
            QScrollBar:vertical {
                border: none;           /* 去除边框 */
                background: #eeeeee;    /* 设置滚动条背景色与主窗口一致 */
                width: 15px;            /* 设置滚动条宽度 */
                margin: 0px;            /* 去除外边距 */
            }
            
            /* 设置垂直滚动条的滑块 */
            QScrollBar::handle:vertical {
                background: #6B69D6;    /* 设置滑块颜色与你的主题色一致 */
                border-radius: 0px;     /* 可根据需要调整滑块圆角，0px为直角 */
                min-height: 20px;       /* 设置滑块最小高度 */
            }
            
            /* 设置垂直滚动条滑块悬停样式 */
            QScrollBar::handle:vertical:hover {
                background: #807EDC;    /* 滑块悬停颜色 */
            }
            
            /* 设置垂直滚动条的上方和下方按钮（箭头区域） */
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                border: none;           /* 去除箭头区域边框 */
                background: #161616;    /* 设置箭头区域背景色 */
                height: 15px;           /* 设置箭头区域高度 */
                subcontrol-origin: margin;
            }
            
            /* 设置垂直滚动条的上箭头图标 */
            QScrollBar::up-arrow:vertical {
                background-color: transparent;
                width: 0px;
                height: 0px;
            }
            
            /* 设置垂直滚动条的下箭头图标 */
            QScrollBar::down-arrow:vertical {
                background-color: transparent;
                width: 0px;
                height: 0px;
            }
            
            /* 设置垂直滚动条的上方和下方扩展区域（滑块移动的剩余空间） */
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {
                background: none;       /* 设置扩展区域背景为透明 */
            }
"""

button1 = """
            QPushButton {
                background-color: #6B69D6;  /* 背景色 */
                color: white;               /* 文字颜色 */
                /* border: 1px solid #6B69D6; 边框 */
            }
            QPushButton:hover {
                background-color: #6257C9;  /* 鼠标悬停时的背景色 */
            }
            QPushButton:pressed {
                background-color: #5841BB;  /* 按下时的背景色 */
            }
        """