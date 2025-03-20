"""Main layout module for the Media Viewer application.

This module defines the main layout class that organizes the UI components
of the media viewer application, including the media display area, control 
panels, and sidebars.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QFrame, QLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot

class MainLayout(QWidget):
    """Main layout class for the Media Viewer application.
    
    This class is responsible for organizing and managing the main UI
    components and their interactions.
    """
    
    def __init__(self, parent=None):
        """Initialize the main layout.
        
        Args:
            parent: Parent widget, if any.
        """
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the UI components and layouts."""
        # Main layout (vertical)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Central widget and layout (will contain media display and controls)
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.central_layout.setSpacing(0)
        
        # Placeholder for media display (will be replaced later)
        self.media_placeholder = QFrame()
        self.media_placeholder.setFrameShape(QFrame.StyledPanel)
        self.media_placeholder.setStyleSheet("background-color: #212121;")
        self.media_placeholder.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        
        # Placeholder for controls layout (will be replaced later)
        self.controls_placeholder = QFrame()
        self.controls_placeholder.setFrameShape(QFrame.StyledPanel)
        self.controls_placeholder.setMaximumHeight(50)
        self.controls_placeholder.setStyleSheet("background-color: #333333;")
        
        # Add placeholders to central layout
        self.central_layout.addWidget(self.media_placeholder, 1)
        self.central_layout.addWidget(self.controls_placeholder)
        
        # Add central widget to main layout
        self.main_layout.addWidget(self.central_widget)
        
        # Set size policy for the main widget
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def set_media_display(self, media_display):
        """Set the media display widget.
        
        Args:
            media_display: The media display widget to use.
        """
        if media_display:
            # Remove the placeholder
            self.central_layout.removeWidget(self.media_placeholder)
            self.media_placeholder.hide()
            
            # Add the media display widget
            self.central_layout.insertWidget(0, media_display, 1)
            media_display.show()
            
            # Update the reference
            self.media_display = media_display
    
    def set_controls_layout(self, controls_layout):
        """Set the controls layout widget.
        
        Args:
            controls_layout: The controls layout widget to use.
        """
        if controls_layout:
            # Remove the placeholder
            self.central_layout.removeWidget(self.controls_placeholder)
            self.controls_placeholder.hide()
            
            # Add the controls layout widget
            self.central_layout.addWidget(controls_layout)
            controls_layout.show()
            
            # Update the reference
            self.controls_layout = controls_layout
    
    def set_sidebar(self, sidebar_layout):
        """Set the sidebar layout.
        
        Args:
            sidebar_layout: The sidebar layout to use.
        """
        if sidebar_layout:
            # Create a splitter if it doesn't exist
            if not hasattr(self, 'splitter'):
                self.splitter = QSplitter(Qt.Horizontal)
                self.main_layout.removeWidget(self.central_widget)
                self.splitter.addWidget(self.central_widget)
                self.main_layout.addWidget(self.splitter)
            
            # Add the sidebar to the splitter
            self.splitter.addWidget(sidebar_layout)
            sidebar_layout.show()
            
            # Set the stretch factors
            self.splitter.setStretchFactor(0, 4)  # Central widget gets more space
            self.splitter.setStretchFactor(1, 1)  # Sidebar gets less space
            
            # Update the reference
            self.sidebar = sidebar_layout
    
    def resizeEvent(self, event):
        """Handle resize events.
        
        Args:
            event: The resize event.
        """
        super().resizeEvent(event)
        
        # Adjust the splitter sizes if it exists
        if hasattr(self, 'splitter'):
            total_width = self.width()
            self.splitter.setSizes([int(total_width * 0.8), int(total_width * 0.2)])
        
        # Emit a custom resize event that child widgets can connect to
        if hasattr(self, 'media_display'):
            self.media_display.update()
        if hasattr(self, 'controls_layout'):
            self.controls_layout.update()
        if hasattr(self, 'sidebar'):
            self.sidebar.update() 