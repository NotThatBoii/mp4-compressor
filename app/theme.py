STYLE = """
QWidget { background: #10141e; color: #edf2ff; font-family: 'Segoe UI'; font-size: 13px; }
QMainWindow { background: #10141e; }
QLabel#logo { font-size: 26px; font-weight: 800; color: #96adff; letter-spacing: 3px; }
QLabel#muted { color: #a2aec6; }
QLabel#dropTitle { font-size: 20px; font-weight: 600; }
QFrame#dropZone { border: 2px dashed #435579; border-radius: 16px; padding: 15px; }
QGroupBox { border: 1px solid #2a354b; border-radius: 12px; margin-top: 14px; padding: 18px 12px 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 5px; color: #b1bfdc; }
QPushButton { background: #273651; border: 1px solid #435575; border-radius: 8px; padding: 10px 20px; font-weight: 600; }
QPushButton:hover { background: #344968; border-color: #809bce; }
QPushButton:pressed { background: #1b2941; }
QPushButton#primary { background: #778fff; color: #0d1428; border: none; }
QPushButton#primary:hover { background: #9baeff; }
QPushButton:disabled { background: #222a3a; color: #69758d; border-color: #2a354b; }
QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background: #1b2435; border: 1px solid #35425c; border-radius: 6px; padding: 7px; min-height: 18px; }
QComboBox:focus, QLineEdit:focus { border-color: #8ba3ff; }
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { color: #626f89; }
QComboBox QAbstractItemView { background: #1b2435; selection-background-color: #405787; }
QProgressBar { background: #202c41; border: none; border-radius: 7px; text-align: center; min-height: 20px; }
QProgressBar::chunk { background: #607bdb; border-radius: 7px; }
QScrollArea { border: none; }
QCheckBox { padding: 6px 0; }
"""
