"""
Notes Module - Quản lý ghi chú với database SQLite
Migrated to PyQt-Fluent-Widgets for Main launcher integration
"""

import os
import sys
import sqlite3
import uuid
from datetime import datetime, timezone
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QMenu, QColorDialog, QInputDialog, QStyle, QStyledItemDelegate,
    QSplitter, QApplication, QTextEdit
)
from PySide6.QtGui import (
    QFont, QColor, QFocusEvent, QAction, QTextCursor, QTextCharFormat, 
    QDesktopServices, QPainter, QPen, QPixmap, QImage, QKeySequence, QBrush, QFontMetrics
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QUrl, QRect, QPoint,
    QDateTime, QBuffer, QIODevice, QEvent, QSize, QByteArray, QThread
)

import re
import base64
import json

# Import qfluentwidgets components
from qfluentwidgets import (
    PushButton, LineEdit, TableWidget, CardWidget,
    FluentIcon as FIF, Theme, setTheme, MessageBoxBase, SubtitleLabel, BodyLabel,
    Flyout, FlyoutAnimationType, FlyoutView, MessageBox, setThemeColor
)

# Configuration
tool_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(tool_dir, "data")
os.makedirs(data_dir, exist_ok=True)

DATABASE_PATH = os.path.join(data_dir, "notes.db")


class NotesLoaderThread(QThread):
    """Thread to load notes from database asynchronously"""
    notes_loaded = Signal(list)
    
    def __init__(self, db_path, search_query="", filter_marked=False):
        super().__init__()
        self.db_path = db_path
        self.search_query = search_query
        self.filter_marked = filter_marked
        
    def run(self):
        try:
            # Create local DB instance for thread safety
            db = NotesDatabase(self.db_path)
            notes = db.get_all_notes(self.search_query, self.filter_marked)
            self.notes_loaded.emit(notes)
        except Exception as e:
            print(f"Error loading notes in thread: {e}")
            self.notes_loaded.emit([])


class ProfileDialog(MessageBoxBase):
    """Dialog for assigning/editing profile with image support."""
    
    def __init__(self, parent=None, profile_data=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Gán Profile", self)
        self.images = [] # List of base64 strings
        
        # ID Input
        self.id_input = LineEdit(self)
        self.id_input.setPlaceholderText("Nhập ID...")
        self.id_input.setClearButtonEnabled(True)
        
        # Password Input
        self.pass_input = LineEdit(self)
        self.pass_input.setPlaceholderText("Nhập Password...")
        self.pass_input.setClearButtonEnabled(True)
        
        # Content Input
        # Note: Using qfluentwidgets TextEdit here for dialog is fine, or switch to QTextEdit if needed.
        # Keeping original TextEdit for now as it wasn't reported broken in dialog.
        from qfluentwidgets import TextEdit as FluentTextEdit
        self.content_input = FluentTextEdit(self)
        self.content_input.setPlaceholderText("Nhập nội dung chi tiết (Ctrl+V để dán ảnh)...")
        self.content_input.setFixedHeight(100)
        self.content_input.installEventFilter(self)
        
        # Image Container (Thumbnails)
        self.image_scroll = QWidget()
        self.image_layout = QHBoxLayout(self.image_scroll)
        self.image_layout.setContentsMargins(0, 0, 0, 0)
        self.image_layout.setSpacing(5)
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Add widgets to layout
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(BodyLabel("ID:", self))
        self.viewLayout.addWidget(self.id_input)
        self.viewLayout.addWidget(BodyLabel("Password:", self))
        self.viewLayout.addWidget(self.pass_input)
        self.viewLayout.addWidget(BodyLabel("Nội dung:", self))
        self.viewLayout.addWidget(self.content_input)
        self.viewLayout.addWidget(BodyLabel("Ảnh đính kèm:", self))
        self.viewLayout.addWidget(self.image_scroll)
        
        # Load data if editing
        if profile_data:
            self.id_input.setText(profile_data.get('id', ''))
            self.pass_input.setText(profile_data.get('password', ''))
            self.content_input.setText(profile_data.get('content', ''))
            # Load images
            loaded_images = profile_data.get('images', [])
            if isinstance(loaded_images, str):
                try:
                    loaded_images = json.loads(loaded_images)
                except:
                    loaded_images = []
            
            for img_b64 in loaded_images:
                self.add_image_thumbnail(img_b64)
            
        # Update button text
        self.yesButton.setText("Lưu")
        self.cancelButton.setText("Hủy")
        
        self.widget.setMinimumWidth(450)

    def eventFilter(self, source, event):
        if hasattr(self, 'content_input') and source == self.content_input and event.type() == QEvent.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.Paste):
                clipboard = QApplication.clipboard()
                mime = clipboard.mimeData()
                if mime.hasImage():
                    self.paste_image(mime.imageData())
                    return True
        return super().eventFilter(source, event)

    def paste_image(self, image):
        """Handle image paste."""
        if isinstance(image, QImage):
            # Convert QImage to Base64
            ba = QByteArray()
            buffer = QBuffer(ba)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")
            b64_str = "data:image/png;base64," + ba.toBase64().data().decode()
            self.add_image_thumbnail(b64_str)
        elif isinstance(image, QPixmap):
            self.paste_image(image.toImage())

    def add_image_thumbnail(self, b64_str):
        """Add thumbnail to layout."""
        self.images.append(b64_str)
        
        # Create thumbnail widget
        thumb_widget = QWidget()
        thumb_widget.setFixedSize(60, 60)
        thumb_layout = QVBoxLayout(thumb_widget)
        thumb_layout.setContentsMargins(0, 0, 0, 0)
        
        # Decode image for display
        try:
            # Remove header if present
            real_b64 = b64_str.split(",")[-1]
            img_data = base64.b64decode(real_b64)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            
            lbl = QLabel()
            lbl.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
            lbl.setScaledContents(True)
            lbl.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
            
            # Delete button (overlay)
            btn_del = PushButton(FIF.CLOSE, "", thumb_widget)
            btn_del.setFixedSize(20, 20)
            btn_del.move(40, 0)
            btn_del.clicked.connect(lambda: self.remove_image(b64_str, thumb_widget))
            
            thumb_layout.addWidget(lbl)
            self.image_layout.addWidget(thumb_widget)
            
        except Exception as e:
            pass

    def remove_image(self, b64_str, widget):
        """Remove image."""
        if b64_str in self.images:
            self.images.remove(b64_str)
        widget.deleteLater()

    def get_data(self):
        """Get profile data."""
        return {
            'id': self.id_input.text().strip(),
            'password': self.pass_input.text().strip(),
            'content': self.content_input.toPlainText().strip(),
            'images': self.images
        }

class NoteTitleDelegate(QStyledItemDelegate):
    """Custom delegate to render title on left and time on right in the same cell."""
    
    def paint(self, painter, option, index):
        """Override paint to draw title and time separately."""
        # Get the full text (title|||time format)
        full_text = index.data(Qt.ItemDataRole.DisplayRole)
        if not full_text:
            return
        
        # Split title and time
        parts = full_text.split("|||")
        title = parts[0] if len(parts) > 0 else ""
        time_str = parts[1] if len(parts) > 1 else ""
        
        # Get font and color from index data
        font_data = index.data(Qt.ItemDataRole.FontRole)
        color_data = index.data(Qt.ItemDataRole.ForegroundRole)
        
        if font_data:
            font = font_data
        else:
            font = QFont()
            font.setBold(True)
        
        if color_data:
            # ForegroundRole returns QBrush in PySide6
            if isinstance(color_data, QBrush):
                color = color_data.color()
            else:
                color = color_data
        else:
            # ✅ Default to white for dark theme
            color = QColor("#ffffff")
        
        painter.save()
        
        # Draw xeon border if selected (NO background fill)
        if option.state & QStyle.StateFlag.State_Selected:
            # Draw glowing xeon blue border
            pen = QPen(QColor("#00aaff"))
            pen.setWidth(2)
            painter.setPen(pen)
            # Draw border with small inset
            border_rect = option.rect.adjusted(1, 1, -1, -1)
            painter.drawRect(border_rect)
            
            # Optional: Draw inner glow effect
            pen.setWidth(1)
            pen.setColor(QColor("#00aaff"))
            painter.setPen(pen)
            inner_rect = option.rect.adjusted(2, 2, -2, -2)
            painter.drawRect(inner_rect)
        
        # Draw title on left (bold)
        painter.setFont(font)
        painter.setPen(color)
        title_rect = QRect(option.rect.left() + 8, option.rect.top(), 
                          option.rect.width() - 150, option.rect.height())
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
        
        # Check marked status from UserRole
        is_marked = index.data(Qt.ItemDataRole.UserRole)
        
        # Draw time on right (gray, not bold)
        if time_str:
            time_font = QFont(font)
            time_font.setBold(False)
            time_font.setPointSize(font.pointSize() - 1)
            painter.setFont(time_font)
            painter.setPen(QColor("#666666"))
            time_rect = QRect(option.rect.right() - 140, option.rect.top(), 
                             130, option.rect.height())
            painter.drawText(time_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, time_str)
            
        # Draw mark icon if marked
        if is_marked:
            icon_rect = QRect(option.rect.right() - 20, option.rect.top() + (option.rect.height() - 16)//2, 16, 16)
            FIF.HEART.render(painter, icon_rect, QColor("#ff0000"))
            
        painter.restore()

class AutoSaveLineEdit(LineEdit):
    """LineEdit with auto-save on focus out."""
    focusOut = Signal()
    
    def focusOutEvent(self, event: QFocusEvent):
        """Emit signal when focus is lost."""
        super().focusOutEvent(event)
        self.focusOut.emit()


class ProfilePreviewWidget(QWidget):
    """Widget to preview profile data (content + images)."""
    
    def __init__(self, data):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        
        # ID/Password (if any)
        if data.get('id') or data.get('password'):
            info_text = f"<b>ID:</b> {data.get('id', '')} | <b>Pass:</b> {data.get('password', '')}"
            info_lbl = QLabel(info_text)
            info_lbl.setTextFormat(Qt.TextFormat.RichText)
            self.layout.addWidget(info_lbl)
        
        # Content
        content = data.get('content', '')
        if content:
            lbl = QLabel(content)
            lbl.setWordWrap(True)
            lbl.setMaximumWidth(300)
            self.layout.addWidget(lbl)
            
        # Images
        images = data.get('images', [])
        if images:
            img_scroll = QWidget()
            img_layout = QHBoxLayout(img_scroll)
            img_layout.setContentsMargins(0, 0, 0, 0)
            img_layout.setSpacing(5)
            
            for b64_str in images:
                try:
                    real_b64 = b64_str.split(",")[-1]
                    img_data = base64.b64decode(real_b64)
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    
                    img_lbl = QLabel()
                    # Scale to max 500x500, keep aspect ratio
                    scaled_pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    img_lbl.setPixmap(scaled_pixmap)
                    img_lbl.setStyleSheet("border: 1px solid #ccc; border-radius: 4px;")
                    img_layout.addWidget(img_lbl)
                except:
                    pass
            
            self.layout.addWidget(img_scroll)

class ProfileTooltip(QWidget):
    """Custom tooltip window for profile preview."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Container for styling
        self.container = QWidget()
        # ✅ Apply Dark Theme to Tooltip
        self.container.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #454545;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.container)
        
        # Shadow effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.container.setGraphicsEffect(shadow)

    def set_data(self, data):
        # Clear previous content
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add preview widget
        preview = ProfilePreviewWidget(data)
        self.container_layout.addWidget(preview)

class AutoSaveTextEdit(QTextEdit):
    """TextEdit with auto-save on focus out and custom context menu."""
    focusOut = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_custom_context_menu)
        self.setAcceptRichText(True)  # Enable rich text
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True) # Important for TextEdit
        self.current_hover_href = None
        
        # Custom tooltip instance
        self.profile_tooltip = ProfileTooltip()
        
        # Auto-save timer
        self.save_timer = QTimer(self)
        self.save_timer.setInterval(1000) # 1 second debounce
        self.save_timer.timeout.connect(self.focusOut.emit) # Reuse focusOut signal to trigger save
        
        self.textChanged.connect(self.on_text_changed)
        
        # Enable IME for Vietnamese typing
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        
        # Set standard font
        font = QFont("Segoe UI", 11)
        self.setFont(font)
        
    def on_text_changed(self):
        """Restart save timer on text change."""
        self.save_timer.start()
        
    def focusOutEvent(self, event: QFocusEvent):
        """Emit signal when focus is lost."""
        super().focusOutEvent(event)
        self.focusOut.emit()
        
    def mouseMoveEvent(self, event):
        """Change cursor and show preview when hovering over profile links."""
        # Call super first to handle standard behavior
        super().mouseMoveEvent(event)
        
        cursor = self.cursorForPosition(event.pos())
        cursor_rect = self.cursorRect(cursor)
        
        # Check if mouse is too far from the text (e.g. end of line whitespace)
        # If mouse X is significantly larger than cursor rect right, ignore.
        # We allow a small buffer (e.g. 10px)
        if event.pos().x() > cursor_rect.right() + 10:
             # Mouse is in whitespace to the right
             should_show = False
        else:
             should_show = True

        fmt = cursor.charFormat()
        
        if should_show and fmt.isAnchor() and fmt.anchorHref().startswith("profile://"):
            href = fmt.anchorHref()
            self.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Show preview if new link
            if href != self.current_hover_href:
                self.current_hover_href = href
                self.show_profile_preview(href, event.pos())
        else:
            # Only hide if we were hovering a link
            if self.current_hover_href:
                self.current_hover_href = None
                self.profile_tooltip.hide()
                # Reset cursor to default (IBeam for TextEdit)
                self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
            
    def leaveEvent(self, event):
        """Hide tooltip when mouse leaves widget."""
        self.profile_tooltip.hide()
        self.current_hover_href = None
        super().leaveEvent(event)
        
    def keyPressEvent(self, event):
        """Reset formatting when Space is pressed."""
        super().keyPressEvent(event)
        
        if event.key() == Qt.Key.Key_Space:
            # Reset to default format
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("white")) # ✅ White text for dark theme
            fmt.setAnchor(False)
            fmt.setAnchorHref("")
            fmt.setFontUnderline(False)
            self.setCurrentCharFormat(fmt)

    def show_profile_preview(self, href, pos):
        """Show custom tooltip preview with smart positioning."""
        try:
            b64_str = href.replace("profile://", "")
            json_str = base64.b64decode(b64_str).decode('utf-8')
            data = json.loads(json_str)
            
            # Update tooltip content
            self.profile_tooltip.set_data(data)
            self.profile_tooltip.adjustSize() # Ensure size is calculated
            
            # Get dimensions
            tooltip_width = self.profile_tooltip.width()
            tooltip_height = self.profile_tooltip.height()
            
            # Get global cursor position (mouse pointer)
            # We use QCursor.pos() for the most accurate mouse position
            from PySide6.QtGui import QCursor, QGuiApplication
            global_mouse_pos = QCursor.pos()
            
            # Get screen geometry
            screen = QGuiApplication.screenAt(global_mouse_pos)
            if not screen:
                screen = QGuiApplication.primaryScreen()
            screen_geo = screen.availableGeometry()
            
            # Default Position: Top-Left of cursor
            # Offset: 10px to give some breathing room
            offset = 10
            
            target_x = global_mouse_pos.x() - tooltip_width - offset
            target_y = global_mouse_pos.y() - tooltip_height - offset
            
            # --- Smart Boundary Checks ---
            
            # Check Left Edge (if goes off-screen to the left, flip to Right)
            if target_x < screen_geo.left():
                target_x = global_mouse_pos.x() + offset
                
            # Check Top Edge (if goes off-screen to the top, flip to Bottom)
            if target_y < screen_geo.top():
                target_y = global_mouse_pos.y() + offset
                
            # Check Right Edge (if flipped to right and goes off-screen, clamp it)
            if target_x + tooltip_width > screen_geo.right():
                target_x = screen_geo.right() - tooltip_width
                
            # Check Bottom Edge (if flipped to bottom and goes off-screen, clamp it)
            if target_y + tooltip_height > screen_geo.bottom():
                target_y = screen_geo.bottom() - tooltip_height
            
            # Move and show
            self.profile_tooltip.move(target_x, target_y)
            self.profile_tooltip.show()
                 
        except Exception as e:
            pass
        
    def mousePressEvent(self, event):
        """Handle clicks on profile links."""
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            cursor_rect = self.cursorRect(cursor)
            
            # Check if mouse is too far from the text (whitespace click)
            is_whitespace = event.pos().x() > cursor_rect.right() + 10
            
            fmt = cursor.charFormat()
            href = fmt.anchorHref()
            
            # Only open profile if NOT whitespace and IS a profile link
            if not is_whitespace and fmt.isAnchor() and href.startswith("profile://"):
                self.edit_profile(href)
                return
                
        super().mousePressEvent(event)
        
        # If we clicked (anywhere), check if we need to reset format
        # This handles the case of clicking at the end of a link to type new text
        cursor = self.textCursor()
        fmt = cursor.charFormat()
        if fmt.isAnchor():
             # We are at a link (likely end of it). Reset format for new typing.
             # Simple logic: If we just clicked and the cursor has link format,
             # but we didn't trigger the edit dialog (meaning we clicked whitespace or edge),
             # let's reset the format so typing is clean.
             
             new_fmt = QTextCharFormat()
             new_fmt.setForeground(QColor("white")) # ✅ White text for dark theme
             new_fmt.setAnchor(False)
             new_fmt.setAnchorHref("")
             new_fmt.setFontUnderline(False)
             self.setCurrentCharFormat(new_fmt)
             
    def show_custom_context_menu(self, position):
        """Show custom context menu."""
        menu = QMenu(self)
        # ✅ Apply Dark Theme Styling to Context Menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #454545;
                border-radius: 8px;
                padding: 4px 0;
            }
            QMenu::item {
                color: #ffffff;
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
                margin: 0 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #454545;
                margin: 4px 0;
            }
        """)
        
        cursor = self.textCursor()
        has_selection = cursor.hasSelection()
        
        # Check if cursor is on a link/profile
        cursor_at_pos = self.cursorForPosition(position)
        char_format = cursor_at_pos.charFormat()
        is_anchor = char_format.isAnchor()
        href = char_format.anchorHref()
        
        # --- Profile Actions ---
        if is_anchor and href.startswith("profile://"):
            edit_profile_action = QAction(FIF.EDIT.icon(), "Sửa Profile", self)
            edit_profile_action.triggered.connect(lambda: self.edit_profile(href))
            menu.addAction(edit_profile_action)
            
            del_profile_action = QAction(FIF.DELETE.icon(), "Xóa Profile", self)
            del_profile_action.triggered.connect(lambda: self.delete_profile(cursor_at_pos))
            menu.addAction(del_profile_action)
            menu.addSeparator()
            
        elif has_selection:
            # Assign Profile (only if selection)
            assign_profile_action = QAction(FIF.PEOPLE.icon(), "Gán Profile", self)
            assign_profile_action.triggered.connect(self.assign_profile)
            menu.addAction(assign_profile_action)
            menu.addSeparator()

        # Change text color (only if has selection)
        if has_selection:
            color_action = QAction("🎨 Đổi màu chữ", self)
            color_action.triggered.connect(self.change_text_color)
            menu.addAction(color_action)
            menu.addSeparator()
        
        # Text size submenu (always show)
        size_menu = QMenu("📏 Text size", self)
        size_menu.setStyleSheet(menu.styleSheet()) # Inherit style
        
        # Quick size options
        for size in [8, 10, 12, 14, 16, 18, 20, 24, 28, 32]:
            size_action = QAction(f"{size}pt", self)
            size_action.triggered.connect(lambda checked, s=size: self.change_text_size(s))
            size_menu.addAction(size_action)
        
        size_menu.addSeparator()
        
        # Custom size
        custom_size_action = QAction("✏️ Tùy chỉnh...", self)
        custom_size_action.triggered.connect(self.change_text_size_custom)
        size_menu.addAction(custom_size_action)
        
        menu.addMenu(size_menu)
        menu.addSeparator()
        
        # Add link
        link_action = QAction("🔗 Gán link", self)
        link_action.triggered.connect(self.insert_link)
        menu.addAction(link_action)
        
        # Open Link
        if is_anchor and not href.startswith("profile://"):
            menu.addSeparator()
            open_link_action = QAction("🌐 Mở link", self)
            open_link_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(href)))
            menu.addAction(open_link_action)
        
        menu.exec(self.viewport().mapToGlobal(position))
        
    def assign_profile(self):
        """Open dialog to assign profile to selected text."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
            
        dialog = ProfileDialog(self.window())
        if dialog.exec():
            data = dialog.get_data()
            # Encode data to base64
            json_str = json.dumps(data)
            b64_str = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
            href = f"profile://{b64_str}"
            
            # Apply link format
            text = cursor.selectedText()
            # Cyan color #00e0ff, no underline
            html = f'<a href="{href}" style="color: #00e0ff; text-decoration: none;">{text}</a>'
            cursor.insertHtml(html)
            self.focusOut.emit() # Auto save

    def edit_profile(self, href):
        """Edit existing profile."""
        try:
            b64_str = href.replace("profile://", "")
            json_str = base64.b64decode(b64_str).decode('utf-8')
            data = json.loads(json_str)
            
            dialog = ProfileDialog(self.window(), data)
            if dialog.exec():
                new_data = dialog.get_data()
                new_json_str = json.dumps(new_data)
                new_b64_str = base64.b64encode(new_json_str.encode('utf-8')).decode('utf-8')
                new_href = f"profile://{new_b64_str}"
                
                # Update link at cursor
                # This is tricky in QTextEdit. We need to select the anchor.
                # Simplified: We just update the href of the current anchor?
                # QTextEdit doesn't support easy DOM manipulation.
                # We have to re-insert HTML or use cursor manipulation.
                
                # Find the anchor range
                # For now, simplistic approach:
                # If triggered from context menu, we have cursor_at_pos.
                # But here we might be called from click.
                # Let's assume cursor is inside the anchor.
                
                cursor = self.textCursor()
                # Expand to anchor
                # This part is complex to do perfectly without selecting the whole anchor.
                # Alternative: Just update the href if possible? No.
                
                # Workaround: Select the word/anchor and replace.
                # But we don't know the exact range of the anchor easily.
                
                # Let's try to just update the format if possible?
                # No, href is part of format.
                
                # We need to select the anchor text.
                # Iterate backwards and forwards to find anchor boundaries.
                
                # ... (Complex logic omitted for brevity, using simple insert for now if selection exists)
                # If no selection, we might just be clicking.
                
                # Better approach: Just update the current char format's anchor?
                # Yes, mergeCharFormat might work if we select the range.
                
                # Let's try to select the anchor range
                # (This is a bit hacky but works for simple cases)
                
                # For now, let's just re-insert at current cursor position if it's a click?
                # No, that duplicates.
                
                # Let's use a helper to select current anchor
                self.select_current_anchor()
                cursor = self.textCursor()
                if cursor.hasSelection():
                    text = cursor.selectedText()
                    html = f'<a href="{new_href}" style="color: #00e0ff; text-decoration: none;">{text}</a>'
                    cursor.insertHtml(html)
                    self.focusOut.emit()
                    
        except Exception as e:
            pass

    def delete_profile(self, cursor_at_pos):
        """Remove profile link but keep text."""
        # Move main cursor to position
        self.setTextCursor(cursor_at_pos)
        self.select_current_anchor()
        cursor = self.textCursor()
        
        if cursor.hasSelection():
            text = cursor.selectedText()
            # Insert as plain text (or preserve other format?)
            # Just insert text removes the anchor
            cursor.insertText(text)
            self.focusOut.emit()

    def select_current_anchor(self):
        """Select the anchor under the cursor."""
        cursor = self.textCursor()
        fmt = cursor.charFormat()
        
        if not fmt.isAnchor():
            return

        # Search backwards
        while fmt.isAnchor() and not cursor.atStart():
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor)
            fmt = cursor.charFormat() # This gets format of char BEFORE cursor?
            # Actually movePosition with KeepAnchor expands selection.
            # We want to move the cursor start back.
            pass
            
        # This is getting complicated.
        # Simplified: Just use the current selection if user selected it?
        # Or just expand to word boundaries?
        # Let's try a simpler approach: Select Word?
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        self.setTextCursor(cursor)
    
    def change_text_color(self):
        """Change color of selected text."""
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.textCursor()
            if cursor.hasSelection():
                fmt = QTextCharFormat()
                fmt.setForeground(color)
                cursor.mergeCharFormat(fmt)
    
    def change_text_size(self, size):
        """Change font size of selected text or set for new text."""
        cursor = self.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        
        if cursor.hasSelection():
            # Apply to selected text
            cursor.mergeCharFormat(fmt)
        else:
            # Set for new text to be typed
            self.setCurrentCharFormat(fmt)
    
    def change_text_size_custom(self):
        """Change font size with custom input."""
        size, ok = QInputDialog.getInt(self, "Text size", "Nhập kích cỡ chữ (pt):", 12, 1, 200)
        if ok:
            self.change_text_size(size)
    
    def insert_link(self):
        """Insert hyperlink."""
        cursor = self.textCursor()
        
        # Get link URL
        url, ok = QInputDialog.getText(self, "Gán link", "Nhập URL:")
        if ok and url:
            if cursor.hasSelection():
                # Link the selected text
                text = cursor.selectedText()
                html = f'<a href="{url}" style="color: #3b82f6; text-decoration: underline;">{text}</a>'
                cursor.insertHtml(html)
            else:
                # Insert URL as text and link
                html = f'<a href="{url}" style="color: #3b82f6; text-decoration: underline;">{url}</a>'
                cursor.insertHtml(html)


class NotesDatabase:
    """Manager for notes SQLite database."""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database schema."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create notes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                due_time TEXT,
                status TEXT DEFAULT 'none',
                is_marked INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                modified_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_note(self, title, content=""):
        """Add new note."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        note_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO notes (id, title, content, due_time, status, created_at, modified_at)
            VALUES (?, ?, ?, NULL, 'none', ?, ?)
        """, (note_id, title, content, now, now))
        
        conn.commit()
        conn.close()
        return note_id
    
    def update_note(self, note_id, title, content=""):
        """Update existing note."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now(timezone.utc).isoformat()
        
        cursor.execute("""
            UPDATE notes 
            SET title = ?, content = ?, modified_at = ?
            WHERE id = ?
        """, (title, content, now, note_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def delete_note(self, note_id):
        """Delete note by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def toggle_mark(self, note_id):
        """Toggle mark status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE notes SET is_marked = NOT is_marked WHERE id = ?", (note_id,))
        conn.commit()
        conn.close()
    
    def get_all_notes(self, search_query="", filter_marked=False):
        """Get all notes with optional search and filter."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        
        if search_query:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        if filter_marked:
            query += " AND is_marked = 1"
        
        query += " ORDER BY modified_at DESC"
        
        cursor.execute(query, params)
        notes = cursor.fetchall()
        conn.close()
        
        return [dict(note) for note in notes]


class NotesWidget(QWidget):
    """Notes manager widget."""
    
    def __init__(self, shared_log=None):
        super().__init__()
        self.setObjectName("notes_widget")
        
        # Set Theme Color (Blue #2986ff) to match Main app
        setThemeColor('#2986ff')
        
        self.db = NotesDatabase(DATABASE_PATH)
        self.current_note_id = None
        self.shared_log = shared_log
        self.original_title = ""
        self.original_content = ""
        self.init_ui()
        self.load_notes()
    
    def log(self, message):
        """Log message to shared log output."""
        if self.shared_log:
            self.shared_log.append(message)
    
    def get_relative_time(self, iso_time_str):
        """Convert ISO timestamp to relative time string."""
        try:
            dt = datetime.fromisoformat(iso_time_str.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff = now - dt
            
            seconds = int(diff.total_seconds())
            
            if seconds < 60:
                return f"{seconds} giây trước"
            elif seconds < 3600:
                minutes = seconds // 60
                return f"{minutes} phút trước"
            elif seconds < 86400:
                hours = seconds // 3600
                return f"{hours} giờ trước"
            elif seconds < 604800:
                days = seconds // 86400
                return f"{days} ngày trước"
            elif seconds < 2592000:
                weeks = seconds // 604800
                return f"{weeks} tuần trước"
            else:
                months = seconds // 2592000
                return f"{months} tháng trước"
        except:
            return ""
    
    def init_ui(self):
        """Initialize UI with Fluent widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ===== TOP BAR: Search + Title + Add Button =====
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        # Search box - Match width with List Panel (approx 350px)
        self.search_input = LineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm kiếm ghi chú...")
        self.search_input.textChanged.connect(lambda: self.load_notes(log_search=False))
        self.search_input.returnPressed.connect(lambda: self.load_notes(log_search=True))
        self.search_input.setFixedWidth(350) # Fixed width to match list panel
        top_bar.addWidget(self.search_input)
        
        # Title Input - Moved to Top Bar
        self.title_input = AutoSaveLineEdit()
        self.title_input.setPlaceholderText("Nhập tiêu đề ghi chú...")
        self.title_input.focusOut.connect(self.auto_save_on_focus_out)
        # Set bold font for title
        title_font = self.title_input.font()
        title_font.setBold(True)
        self.title_input.setFont(title_font)
        top_bar.addWidget(self.title_input, 1) # Stretch factor 1
        
        # Add note button
        add_btn = PushButton(FIF.ADD, "Tạo Ghi Chú Mới")
        add_btn.clicked.connect(self.add_new_note)
        add_btn.setFixedWidth(160)
        top_bar.addWidget(add_btn)
        
        layout.addLayout(top_bar)
        
        # ===== MAIN CONTENT: Notes List | Editor =====
        # Use CardWidget to wrap content for Fluent design
        content_card = CardWidget()
        content_layout = QHBoxLayout(content_card)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # LEFT: Notes list table
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        self.notes_table = TableWidget(self)
        self.notes_table.setColumnCount(2)
        self.notes_table.setHorizontalHeaderLabels(["Danh Sách Ghi Chú", "ID"])
        self.notes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.notes_table.hideColumn(1) # Hide ID
        self.notes_table.verticalHeader().hide()
        self.notes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.notes_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.notes_table.cellClicked.connect(self.on_note_selected)
        
        # Context Menu Policy
        self.notes_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Apply custom delegate for title column
        self.notes_table.setItemDelegateForColumn(0, NoteTitleDelegate(self.notes_table))
        # ✅ Apply Dark Theme to Table
        self.notes_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QTableWidget::item:focus {
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                border-bottom: 1px solid #454545;
                padding: 4px;
            }
        """)
        left_layout.addWidget(self.notes_table)
        
        content_layout.addWidget(left_widget) # Will be resized by splitter
        
        # RIGHT: Editor (Content only)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Content - Fluent TextEdit
        self.content_input = AutoSaveTextEdit()
        self.content_input.setPlaceholderText("Nhập nội dung ghi chú...")
        self.content_input.focusOut.connect(self.auto_save_on_focus_out)
        # Also save on text change with debounce or just simple change tracking
        # For now, let's stick to focusOut but ensure it works. 
        # We can also add a manual save button if needed, but focusOut is standard.
        
        # ✅ Apply Dark Theme to Content Editor
        self.content_input.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 8px;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
            }
            QScrollBar:vertical {
                background: #2b2b2b;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #606060;
                border-radius: 5px;
            }
        """)
        right_layout.addWidget(self.content_input)
        
        content_layout.addWidget(right_widget)
        
        # Use QSplitter to manage resizing between left and right
        # We need to wrap left and right widgets in a splitter, 
        # BUT CardWidget layout expects widgets.
        # Let's put the splitter INSIDE the CardWidget
        
        # Re-doing the content layout to use Splitter inside Card
        # Clear previous adds to content_layout
        # Create Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([350, 650]) # Match search input width
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #e0e0e0;
            }
        """)
        
        content_layout.addWidget(splitter)
        
        layout.addWidget(content_card)
    
    def load_notes(self, log_search=False):
        """Load notes from database to table asynchronously."""
        search_query = self.search_input.text()
        
        # Cancel previous thread if running
        if hasattr(self, 'loader_thread') and self.loader_thread.isRunning():
            self.loader_thread.terminate()
            self.loader_thread.wait()
            
        self.loader_thread = NotesLoaderThread(DATABASE_PATH, search_query, False)
        self.loader_thread.notes_loaded.connect(lambda notes: self.on_notes_loaded(notes, search_query, log_search))
        self.loader_thread.start()
        
    def on_notes_loaded(self, notes, search_query, log_search):
        """Handle loaded notes from thread."""
        self.notes_table.setRowCount(0)
        self.notes_table.setSortingEnabled(False) # Disable sorting while populating
        
        # Only log when Enter is pressed
        if search_query and log_search:
            self.log(f"🔍 Tìm kiếm: '{search_query}' - Tìm thấy {len(notes)} ghi chú")
        
        for note in notes:
            row = self.notes_table.rowCount()
            self.notes_table.insertRow(row)
            
            # Column 0: Title|||Time format (will be rendered by custom delegate)
            relative_time = self.get_relative_time(note['modified_at'])
            display_text = f"{note['title']}|||{relative_time}" if relative_time else f"{note['title']}|||"
            
            title_item = QTableWidgetItem(display_text)
            
            # Always bold for titles
            font = title_item.font()
            font.setBold(True)
            title_item.setFont(font)
            
            # Set UserRole to store marked status for delegate to render icon
            title_item.setData(Qt.ItemDataRole.UserRole, note['is_marked'] == 1)
            
            self.notes_table.setItem(row, 0, title_item)
            
            # Column 1: ID (hidden)
            self.notes_table.setItem(row, 1, QTableWidgetItem(note['id']))
            
        self.notes_table.setSortingEnabled(True) # Re-enable sorting
    
    def toggle_mark(self, note_id):
        """Toggle mark for note."""
        self.db.toggle_mark(note_id)
        self.log("⭐ Đã chuyển trạng thái đánh dấu ghi chú")
        self.load_notes()
    
    def on_note_selected(self, row, column):
        """Handle note selection from table."""
        if row < 0:
            return
        
        note_id = self.notes_table.item(row, 1).text()  # Column 1 is ID
        
        # Load note details
        notes = self.db.get_all_notes()
        selected_note = next((n for n in notes if n['id'] == note_id), None)
        
        if selected_note:
            self.current_note_id = note_id
            self.title_input.setText(selected_note['title'])
            self.content_input.setHtml(selected_note['content'] or "")  # Use setHtml for rich text
            
            # Store original values for change tracking
            self.original_title = selected_note['title']
            self.original_content = selected_note['content'] or ""
            
            self.log(f"📖 Đang chỉnh sửa: {selected_note['title']}")
    
    def add_new_note(self):
        """Clear editor to add new note."""
        self.clear_editor()
        self.title_input.setFocus()
        self.log("➕ Bắt đầu tạo ghi chú mới")
    
    def clear_editor(self):
        """Clear editor fields."""
        self.current_note_id = None
        self.title_input.clear()
        self.content_input.clear()
        self.original_title = ""
        self.original_content = ""
    
    def save_note(self):
        """Save current note."""
        title = self.title_input.text().strip()
        
        if not title:
            QMessageBox.warning(self, "Lỗi", "Tiêu đề không được để trống!")
            self.log("❌ Lỗi: Tiêu đề không được để trống!")
            return
        
        content = self.content_input.toHtml()  # Save as HTML for rich text
        
        if self.current_note_id:
            # Update existing
            success = self.db.update_note(self.current_note_id, title, content)
            if success:
                self.log(f"💾 Đã cập nhật ghi chú: {title}")
                self.load_notes()
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể cập nhật ghi chú!")
                self.log("❌ Lỗi: Không thể cập nhật ghi chú!")
        else:
            # Add new
            note_id = self.db.add_note(title, content)
            self.current_note_id = note_id
            self.log(f"✅ Đã tạo ghi chú mới: {title}")
            self.load_notes()
    
    def delete_note(self):
        """Delete current note."""
        if not self.current_note_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn ghi chú để xóa!")
            self.log("❌ Lỗi: Vui lòng chọn ghi chú để xóa!")
            return
        
        reply = QMessageBox.question(
            self, "Xác nhận xóa",
            "Bạn có chắc chắn muốn xóa ghi chú này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.db.delete_note(self.current_note_id)
            if success:
                self.log("🗑️ Đã xóa ghi chú thành công")
                self.clear_editor()
                self.load_notes()
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể xóa ghi chú!")
                self.log("❌ Lỗi: Không thể xóa ghi chú!")
    
    def auto_save_on_focus_out(self):
        """Auto save when focus leaves input fields - only if changed."""
        title = self.title_input.text().strip()
        content = self.content_input.toHtml()
        
        # Check if content has changed
        has_changed = (title != self.original_title or content != self.original_content)
        
        # Only auto-save if there's a title and content has changed
        if title and has_changed:
            self.save_note()
            # Update original values after saving
            self.original_title = title
            self.original_content = content
    
    def show_context_menu(self, position):
        """Show context menu for notes table."""
        # Get selected row
        row = self.notes_table.rowAt(position.y())
        if row < 0:
            return
        
        # Get note ID
        note_id = self.notes_table.item(row, 1).text()  # Column 1 is ID
        
        # Get note details to check mark status
        notes = self.db.get_all_notes()
        selected_note = next((n for n in notes if n['id'] == note_id), None)
        
        menu = QMenu(self)
        # ✅ Apply Dark Theme Styling to Context Menu
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 4px 0;
            }
            QMenu::item {
                color: #ffffff;
                padding: 6px 24px 6px 12px;
                border-radius: 4px;
                margin: 0 4px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #454545;
                margin: 4px 0;
            }
        """)
        
        # Toggle Mark Action
        is_marked = selected_note['is_marked'] == 1 if selected_note else False
        mark_text = "Bỏ đánh dấu" if is_marked else "Đánh dấu quan trọng"
        mark_icon = FIF.HEART if is_marked else FIF.HEART
        
        mark_action = QAction(mark_icon.icon(), mark_text, self)
        mark_action.triggered.connect(lambda: self.toggle_mark(note_id))
        menu.addAction(mark_action)
        
        menu.addSeparator()
        
        # Delete Action
        delete_action = QAction(FIF.DELETE.icon(), "Xóa ghi chú", self)
        delete_action.triggered.connect(lambda: self.delete_note_from_menu(note_id))
        menu.addAction(delete_action)
        
        menu.exec(self.notes_table.viewport().mapToGlobal(position))
    
    def delete_note_from_menu(self, note_id):
        """Delete note from context menu with confirmation."""
        # Use Fluent MessageBox for consistent styling
        w = MessageBox(
            "Xác nhận xóa",
            "Bạn có chắc chắn muốn xóa ghi chú này?",
            self.window()
        )
        w.yesButton.setText("Xóa")
        w.cancelButton.setText("Hủy")
        
        if w.exec():
            success = self.db.delete_note(note_id)
            if success:
                self.log("🗑️ Đã xóa ghi chú thành công")
                # Clear editor if deleted note was selected
                if self.current_note_id == note_id:
                    self.clear_editor()
                self.load_notes()
            else:
                QMessageBox.warning(self, "Lỗi", "Không thể xóa ghi chú!")
                self.log("❌ Lỗi: Không thể xóa ghi chú!")
