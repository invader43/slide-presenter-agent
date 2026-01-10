"""PDF-based slide viewer using PyMuPDF for rendering."""

import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image, ImageTk
from loguru import logger


@dataclass
class PageData:
    """Data for a single PDF page."""
    page_number: int  # 1-based index
    title: str
    text: str
    image: Optional[Image.Image] = None


class PDFSlideViewer:
    """Tkinter UI for displaying PDF slides with rendered images."""
    
    def __init__(self, pdf_file: str = "./slides.pdf", dpi: int = 150):
        self.pdf_file = Path(pdf_file)
        self.dpi = dpi
        self.current_index = 0
        self.pages: List[PageData] = []
        self.doc: Optional[fitz.Document] = None
        
        # UI components
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.info_label: Optional[tk.Label] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None
        
        # Load PDF
        self._load_pdf()
    
    def _load_pdf(self) -> None:
        """Load PDF document and extract page data."""
        if not self.pdf_file.exists():
            logger.error(f"PDF file not found: {self.pdf_file}")
            return
        
        try:
            self.doc = fitz.open(str(self.pdf_file))
            logger.info(f"Loading PDF with {len(self.doc)} pages")
            
            for idx, page in enumerate(self.doc):
                page_data = self._parse_page(idx + 1, page)
                self.pages.append(page_data)
                logger.info(f"Loaded page {idx + 1}: {page_data.title[:50]}...")
            
            logger.info(f"Successfully loaded {len(self.pages)} pages")
            
        except Exception as e:
            logger.error(f"Error loading PDF: {e}")
    
    def _parse_page(self, page_num: int, page: fitz.Page) -> PageData:
        """Parse a single PDF page and return PageData."""
        # Extract text
        text = page.get_text("text").strip()
        
        # Generate title from first line or page number
        lines = text.split("\n")
        title = lines[0].strip() if lines and lines[0].strip() else f"Slide {page_num}"
        title = title[:100]  # Limit title length
        
        # Render page to image
        image = self._render_page(page)
        
        return PageData(
            page_number=page_num,
            title=title,
            text=text if text else "No text content",
            image=image
        )
    
    def _render_page(self, page: fitz.Page) -> Image.Image:
        """Render a PDF page to a PIL Image."""
        # Calculate zoom factor for desired DPI
        zoom = self.dpi / 72  # PDF base is 72 DPI
        matrix = fitz.Matrix(zoom, zoom)
        
        # Render to pixmap
        pixmap = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        
        return img
    
    @property
    def slides(self) -> List[PageData]:
        """Alias for pages for compatibility with existing code."""
        return self.pages
    
    def start(self) -> None:
        """Start the Tkinter UI in a separate thread."""
        thread = threading.Thread(target=self._run_ui, daemon=True)
        thread.start()
    
    def _run_ui(self) -> None:
        """Run the Tkinter main loop."""
        self.root = tk.Tk()
        self._configure_window()
        self._create_widgets()
        
        # Display first page if available
        if self.pages:
            self.display_current_slide()
        
        self.root.mainloop()
    
    def _configure_window(self) -> None:
        """Configure the main window."""
        self.root.title("🎤 Voice Controlled PDF Slide Viewer")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a2e")
        
        # Bind resize event
        self.root.bind("<Configure>", self._on_resize)
    
    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        self._create_app_title()
        self._create_canvas()
        self._create_info_label()
        self._create_navigation_buttons()
    
    def _create_app_title(self) -> None:
        """Create the application title."""
        app_title = tk.Label(
            self.root,
            text="🎤 Voice Controlled PDF Slide Viewer",
            font=("Segoe UI", 18, "bold"),
            bg="#1a1a2e",
            fg="#e94560"
        )
        app_title.pack(pady=12)
    
    def _create_canvas(self) -> None:
        """Create the canvas for displaying slide images."""
        # Container frame for the canvas
        canvas_frame = tk.Frame(self.root, bg="#16213e", relief=tk.FLAT)
        canvas_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#16213e",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_info_label(self) -> None:
        """Create the slide info label."""
        self.info_label = tk.Label(
            self.root,
            text="No slides loaded",
            font=("Segoe UI", 11),
            bg="#1a1a2e",
            fg="#a0a0a0"
        )
        self.info_label.pack(pady=8)
    
    def _create_navigation_buttons(self) -> None:
        """Create navigation buttons."""
        button_frame = tk.Frame(self.root, bg="#1a1a2e")
        button_frame.pack(pady=12)
        
        style = ttk.Style()
        style.configure("Nav.TButton", font=("Segoe UI", 11), padding=8)
        
        prev_btn = ttk.Button(
            button_frame, 
            text="← Previous", 
            command=self.previous_slide,
            style="Nav.TButton"
        )
        prev_btn.pack(side=tk.LEFT, padx=8)
        
        next_btn = ttk.Button(
            button_frame, 
            text="Next →", 
            command=self.next_slide,
            style="Nav.TButton"
        )
        next_btn.pack(side=tk.LEFT, padx=8)
    
    def _on_resize(self, event=None) -> None:
        """Handle window resize by redrawing the current slide."""
        if self.pages and self.canvas:
            # Use after_idle to avoid excessive redraws
            self.root.after_idle(self._redraw_slide)
    
    def _redraw_slide(self) -> None:
        """Redraw the current slide image on the canvas."""
        if not self.pages or not self.canvas:
            return
        
        page = self.pages[self.current_index]
        if page.image is None:
            return
        
        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Scale image to fit canvas while maintaining aspect ratio
        img_width, img_height = page.image.size
        scale = min(canvas_width / img_width, canvas_height / img_height, 1.0)
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        resized = page.image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(resized)
        
        # Clear canvas and draw new image centered
        self.canvas.delete("all")
        x = canvas_width // 2
        y = canvas_height // 2
        self.canvas.create_image(x, y, anchor=tk.CENTER, image=self.photo_image)
    
    def display_current_slide(self) -> None:
        """Display the current slide."""
        if not self.pages:
            return
        
        try:
            page = self.pages[self.current_index]
            
            if self.root and self.canvas:
                # Update window title with slide title
                self.root.title(f"🎤 {page.title[:60]}")
                
                # Redraw slide image
                self._redraw_slide()
                
                # Update info label
                self.info_label.config(
                    text=f"Slide {page.page_number} of {len(self.pages)}"
                )
            
            logger.info(f"Displaying page {page.page_number}: {page.title[:50]}")
            
        except Exception as e:
            logger.error(f"Error displaying slide: {e}")
    
    def next_slide(self) -> Optional[Dict[str, Any]]:
        """Move to the next slide."""
        if not self.pages:
            return None
        
        self.current_index = (self.current_index + 1) % len(self.pages)
        self.display_current_slide()
        return self.get_current_slide_info()
    
    def previous_slide(self) -> Optional[Dict[str, Any]]:
        """Move to the previous slide."""
        if not self.pages:
            return None
        
        self.current_index = (self.current_index - 1) % len(self.pages)
        self.display_current_slide()
        return self.get_current_slide_info()
    
    def goto_slide(self, slide_number: int) -> Dict[str, Any]:
        """Go to a specific slide by number (1-based)."""
        if not self.pages:
            return {"error": "No slides available"}
        
        # Convert to 0-based index
        index = slide_number - 1
        
        if 0 <= index < len(self.pages):
            self.current_index = index
            self.display_current_slide()
            return self.get_current_slide_info()
        else:
            return {"error": f"Invalid slide number. Please choose between 1 and {len(self.pages)}"}
    
    def get_current_slide_info(self) -> Dict[str, Any]:
        """Get information about the current slide including full text."""
        if not self.pages:
            return {"error": "No slides available"}
        
        page = self.pages[self.current_index]
        return {
            "slide_number": page.page_number,
            "total_slides": len(self.pages),
            "title": page.title,
            "content": page.text,  # Full text for AI to present
            "has_next": self.current_index < len(self.pages) - 1,
            "has_previous": self.current_index > 0
        }
    
    def close(self) -> None:
        """Close the PDF document and UI."""
        if self.doc:
            self.doc.close()
        if self.root:
            self.root.quit()
