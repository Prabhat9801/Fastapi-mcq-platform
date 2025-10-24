"""
Advanced Document Processing Service
Handles OCR for scanned documents, image extraction, table parsing
"""

import os
import io
from typing import List, Dict, Optional, Tuple
from PIL import Image
import fitz  # PyMuPDF
import logging

from app.core.config import settings
from app.core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)

# Optional imports - only needed for OCR
try:
    from pdf2image import convert_from_path
    import pytesseract
    import cv2
    import numpy as np
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR dependencies not available. Only digital PDF processing will work.")

# Optional table extraction
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logger.warning("Camelot not available. Table extraction disabled.")


class DocumentProcessor:
    """Advanced document processor with OCR and intelligent content extraction"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.docx']
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Detect if PDF is scanned (image-based) or digital (text-based)
        """
        try:
            doc = fitz.open(pdf_path)
            text_ratio = 0
            total_pages = min(3, len(doc))  # Check first 3 pages
            
            for page_num in range(total_pages):
                page = doc[page_num]
                text = page.get_text()
                text_length = len(text.strip())
                
                # Get page dimensions
                rect = page.rect
                page_area = rect.width * rect.height
                
                # Calculate text density
                if page_area > 0:
                    text_ratio += text_length / page_area
            
            doc.close()
            
            # If average text ratio is very low, likely scanned
            avg_ratio = text_ratio / total_pages
            return avg_ratio < 0.01
            
        except Exception as e:
            logger.error(f"Error detecting PDF type: {e}")
            return False
    
    def extract_text_from_digital_pdf(self, pdf_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        """
        Extract text from digital (non-scanned) PDF
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            if page_range:
                start, end = page_range
                pages = range(start - 1, min(end, len(doc)))
            else:
                pages = range(len(doc))
            
            for page_num in pages:
                page = doc[page_num]
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page.get_text()
            
            doc.close()
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from digital PDF: {e}")
            raise DocumentProcessingError(f"Failed to extract text: {str(e)}")
    
    def extract_text_from_scanned_pdf(self, pdf_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        """
        Extract text from scanned PDF using OCR
        """
        if not OCR_AVAILABLE:
            raise DocumentProcessingError(
                "OCR processing requires Tesseract. Please install Tesseract OCR or use a text-based PDF. "
                "Visit: https://github.com/UB-Mannheim/tesseract/wiki for installation instructions."
            )
        
        try:
            # Convert PDF pages to images
            if page_range:
                first_page, last_page = page_range
                images = convert_from_path(
                    pdf_path,
                    first_page=first_page,
                    last_page=last_page,
                    dpi=300
                )
            else:
                images = convert_from_path(pdf_path, dpi=300)
            
            text = ""
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self.preprocess_image_for_ocr(image)
                
                # Perform OCR
                page_text = pytesseract.image_to_string(processed_image)
                text += f"\n--- Page {i + 1} ---\n"
                text += page_text
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from scanned PDF: {e}")
            raise DocumentProcessingError(f"OCR processing failed: {str(e)}")
    
    def preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy
        """
        if not OCR_AVAILABLE:
            return image
        
        try:
            # Convert PIL Image to OpenCV format
            img_array = np.array(image)
            
            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )
            
            # Convert back to PIL Image
            return Image.fromarray(thresh)
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {e}")
            return image
    
    def extract_images_from_pdf(self, pdf_path: str, output_dir: str) -> List[Dict[str, any]]:
        """
        Extract all images from PDF
        Returns list of image metadata
        """
        try:
            doc = fitz.open(pdf_path)
            images_info = []
            
            os.makedirs(output_dir, exist_ok=True)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Save image
                        image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                        image_path = os.path.join(output_dir, image_filename)
                        
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)
                        
                        # Get OCR text from image
                        try:
                            if OCR_AVAILABLE:
                                img_pil = Image.open(io.BytesIO(image_bytes))
                                processed_img = self.preprocess_image_for_ocr(img_pil)
                                ocr_text = pytesseract.image_to_string(processed_img)
                            else:
                                ocr_text = "[OCR not available - install Tesseract]"
                        except:
                            ocr_text = ""
                        
                        images_info.append({
                            "page": page_num + 1,
                            "index": img_index + 1,
                            "filename": image_filename,
                            "path": image_path,
                            "extension": image_ext,
                            "ocr_text": ocr_text
                        })
            
            doc.close()
            return images_info
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
            return []
    
    def extract_tables_from_pdf(self, pdf_path: str, pages: str = 'all') -> List[Dict]:
        """
        Extract tables from PDF using Camelot
        """
        if not CAMELOT_AVAILABLE:
            logger.warning("Camelot not available, skipping table extraction")
            return []
        
        try:
            tables_info = []
            
            # Try lattice method first (for bordered tables)
            try:
                tables = camelot.read_pdf(pdf_path, pages=pages, flavor='lattice')
                
                for i, table in enumerate(tables):
                    tables_info.append({
                        "table_number": i + 1,
                        "page": table.page,
                        "parsing_method": "lattice",
                        "accuracy": table.parsing_report.get('accuracy', 0),
                        "data": table.df.to_dict('records'),
                        "csv": table.df.to_csv(index=False)
                    })
            except:
                pass
            
            # Try stream method (for borderless tables)
            if not tables_info:
                try:
                    tables = camelot.read_pdf(pdf_path, pages=pages, flavor='stream')
                    
                    for i, table in enumerate(tables):
                        tables_info.append({
                            "table_number": i + 1,
                            "page": table.page,
                            "parsing_method": "stream",
                            "accuracy": table.parsing_report.get('accuracy', 0),
                            "data": table.df.to_dict('records'),
                            "csv": table.df.to_csv(index=False)
                        })
                except:
                    pass
            
            return tables_info
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def process_document(
        self,
        file_path: str,
        extract_images: bool = True,
        extract_tables: bool = True,
        page_range: Optional[Tuple[int, int]] = None
    ) -> Dict[str, any]:
        """
        Main document processing method
        Returns comprehensive document analysis
        """
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in self.supported_formats:
                raise DocumentProcessingError(f"Unsupported file format: {file_ext}")
            
            result = {
                "file_path": file_path,
                "file_type": file_ext,
                "is_scanned": False,
                "text": "",
                "images": [],
                "tables": [],
                "processing_method": ""
            }
            
            if file_ext == '.pdf':
                is_scanned = self.is_scanned_pdf(file_path)
                result["is_scanned"] = is_scanned
                
                # Extract text
                if is_scanned:
                    result["text"] = self.extract_text_from_scanned_pdf(file_path, page_range)
                    result["processing_method"] = "OCR"
                else:
                    result["text"] = self.extract_text_from_digital_pdf(file_path, page_range)
                    result["processing_method"] = "Digital"
                
                # Extract images
                if extract_images:
                    output_dir = os.path.join(settings.UPLOAD_DIR, "extracted_images")
                    result["images"] = self.extract_images_from_pdf(file_path, output_dir)
                
                # Extract tables
                if extract_tables:
                    pages_str = 'all' if not page_range else f"{page_range[0]}-{page_range[1]}"
                    result["tables"] = self.extract_tables_from_pdf(file_path, pages_str)
            
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                # Process image with OCR
                if not OCR_AVAILABLE:
                    raise DocumentProcessingError(
                        "Image processing requires Tesseract OCR. Please install Tesseract or use text-based PDFs."
                    )
                
                image = Image.open(file_path)
                processed_image = self.preprocess_image_for_ocr(image)
                result["text"] = pytesseract.image_to_string(processed_image)
                result["processing_method"] = "OCR"
            
            return result
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            raise DocumentProcessingError(f"Failed to process document: {str(e)}")
    
    def chunk_text_intelligently(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        Chunk text intelligently by preserving sentence boundaries
        """
        # Split into sentences
        sentences = text.split('.')
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip() + "."
            
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += " " + sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap
                if chunks and overlap > 0:
                    words = current_chunk.split()
                    overlap_text = " ".join(words[-overlap:]) if len(words) > overlap else current_chunk
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


# Singleton instance
document_processor = DocumentProcessor()
