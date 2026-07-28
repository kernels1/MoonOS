import sys
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QHBoxLayout, QPushButton, QCheckBox, QMessageBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl


class SilentWebPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineID, sourceID):
        pass  # Keeps MoonOS Terminal clean


class MoonNativeBrowser(QMainWindow):
    def __init__(self, start_url, incognito=False):
        super().__init__()
        self.is_incognito = incognito

        # 1. Setup Browser Profile
        if self.is_incognito:
            # Create an "Off-the-Record" profile (No cache/cookies saved)
            self.profile = QWebEngineProfile("MoonIncognito", self)
        else:
            self.profile = QWebEngineProfile.defaultProfile()

        self.browser = QWebEngineView()
        self.web_page = SilentWebPage(self.profile, self.browser)
        self.browser.setPage(self.web_page)
        self.browser.setUrl(QUrl(start_url))

        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton(" < ")
        self.back_btn.setFixedWidth(40)
        self.back_btn.clicked.connect(self.browser.back)

        self.forward_btn = QPushButton(" > ")
        self.forward_btn.setFixedWidth(40)
        self.forward_btn.clicked.connect(self.browser.forward)

        self.reload_btn = QPushButton(" ↻ ")
        self.reload_btn.setFixedWidth(40)
        self.reload_btn.clicked.connect(self.browser.reload)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search Google or type a URL...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        self.history_btn = QPushButton(" History ")
        self.history_btn.clicked.connect(self.show_history)

        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.reload_btn)
        nav_layout.addWidget(self.url_bar)
        nav_layout.addWidget(self.history_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(nav_layout)
        main_layout.addWidget(self.browser)
        main_layout.setContentsMargins(2, 2, 2, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        mode_name = " (INCOGNITO)" if self.is_incognito else ""
        self.setWindowTitle(f"UltraBrowser{mode_name}")
        self.resize(1280, 800)

        self.browser.urlChanged.connect(self.on_url_changed)

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if "." not in text or " " in text:
            url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
        else:
            url = text if text.startswith("http") else "https://" + text
        self.browser.setUrl(QUrl(url))

    def on_url_changed(self, q):
        url_str = q.toString()
        self.url_bar.setText(url_str)

        # Save to history if NOT in incognito
        if not self.is_incognito and "google.com/search" not in url_str:
            with open("MoonDrive/history.log", "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                f.write(f"[{timestamp}] {url_str}\n")

    def show_history(self):
        try:
            # Check if history file exists
            import os
            if not os.path.exists("MoonDrive/history.log"):
                QMessageBox.information(self, "MoonOS History", "No history found yet.")
                return

            with open("MoonDrive/history.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get the last 15 entries for a clean view
                recent_history = "".join(lines[-15:]) if lines else "History is empty."

                # We use a standard Message Box but ensure it is modal (blocks other input)
                msg = QMessageBox(self)
                msg.setWindowTitle("MoonOS Browsing History")
                msg.setText("Your recent activity:")
                msg.setInformativeText(recent_history)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()  # .exec_() is critical; it holds the window open
        except Exception as e:
            print(f"History Error: {e}")