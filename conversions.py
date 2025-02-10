# conversions.py

import os
import subprocess
import shutil
from pdf2docx import Converter as PDF2DocxConverter
from docx2pdf import convert as docx2pdf_convert
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image, ImageEnhance
import cairosvg
import docx

def convert_docx_to_pdf(input_path, output_path=None):
    """docx -> pdf via docx2pdf."""
    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = base + ".pdf"
    docx2pdf_convert(input_path, output_path)
    return output_path

def convert_pdf_to_docx(input_pdf, output_docx=None):
    """pdf -> docx via pdf2docx."""
    if not output_docx:
        base, _ = os.path.splitext(input_pdf)
        output_docx = base + ".docx"
    pdf2docx = PDF2DocxConverter(input_pdf)
    pdf2docx.convert(output_docx, start=0, end=None)
    pdf2docx.close()
    return output_docx

def convert_docx_to_txt(input_docx, output_txt=None):
    """docx -> txt usando python-docx."""
    if not output_txt:
        base, _ = os.path.splitext(input_docx)
        output_txt = base + ".txt"
    d = docx.Document(input_docx)
    text_paragraphs = [para.text for para in d.paragraphs]
    full_text = "\n".join(text_paragraphs)
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write(full_text)
    return output_txt

def convert_pdf_to_txt(input_pdf, output_txt=None):
    """pdf -> txt usando `pdftotext` (richiede poppler)."""
    if not output_txt:
        base, _ = os.path.splitext(input_pdf)
        output_txt = base + ".txt"
    cmd = ["pdftotext", input_pdf, output_txt]
    process = subprocess.run(cmd, capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"Errore conversione pdf->txt: {process.stderr}")
    return output_txt

def convert_image(input_img, output_path):
    """Converte immagini raster e SVG in vari formati."""
    ext_in = os.path.splitext(input_img)[1].lower()
    ext_out = os.path.splitext(output_path)[1].lower()

    if ext_in == ".svg":
        if ext_out == ".png":
            cairosvg.svg2png(url=input_img, write_to=output_path)
        elif ext_out == ".pdf":
            cairosvg.svg2pdf(url=input_img, write_to=output_path)
        elif ext_out == ".svg":
            shutil.copy(input_img, output_path)
        elif ext_out in [".jpg", ".jpeg"]:
            temp_png = output_path + "_temp.png"
            cairosvg.svg2png(url=input_img, write_to=temp_png)
            with Image.open(temp_png) as im:
                rgb_im = im.convert("RGB")
                rgb_im.save(output_path, "JPEG")
            os.remove(temp_png)
        elif ext_out == ".webp":
            temp_png = output_path + "_temp.png"
            cairosvg.svg2png(url=input_img, write_to=temp_png)
            with Image.open(temp_png) as im:
                im.save(output_path, "WEBP")
            os.remove(temp_png)
        else:
            raise ValueError("Formato di output non gestito per file SVG.")
    else:
        with Image.open(input_img) as im:
            if ext_out in [".jpg", ".jpeg"]:
                im = im.convert("RGB")
                im.save(output_path, "JPEG")
            elif ext_out == ".webp":
                im.save(output_path, "WEBP")
            else:
                im.save(output_path)
    return output_path

def merge_pdfs(pdf_list, output_pdf):
    """Unisce più PDF in uno solo."""
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_pdf)
    merger.close()
    return output_pdf

def convert_pdf_to_pages(pdf_file, output_pages=None):
    """PDF -> .pages (via PDF->DOCX->PAGES)."""
    docx_temp = convert_pdf_to_docx(pdf_file)
    if not output_pages:
        base, _ = os.path.splitext(pdf_file)
        output_pages = base + ".pages"
    docx_to_pages(docx_temp, output_pages)
    return output_pages

def docx_to_pages(docx_file, pages_file=None):
    """docx -> pages via AppleScript (macOS + Pages)."""
    if not pages_file:
        base, _ = os.path.splitext(docx_file)
        pages_file = base + ".pages"
    docx_abs = os.path.abspath(docx_file).replace('"', '\\"')
    pages_abs = os.path.abspath(pages_file).replace('"', '\\"')
    script = f'''
    tell application "Pages"
        activate
        open "{docx_abs}"
        set theDoc to document 1
        tell theDoc to save as "com.apple.iwork.pages.sffpages" in "{pages_abs}"
        close theDoc
    end tell
    '''
    process = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if process.returncode != 0:
        raise RuntimeError(f"Errore AppleScript: {process.stderr}")
    return pages_file

def split_pdf(input_pdf, output_pdf, pages_string):
    """Estrae pagine definite in pages_string (es: '1-3,5,7-9')."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    pages_to_extract = parse_page_ranges(pages_string)
    for p in pages_to_extract:
        idx = p - 1
        if 0 <= idx < len(reader.pages):
            writer.add_page(reader.pages[idx])
    with open(output_pdf, "wb") as f:
        writer.write(f)
    return output_pdf

def parse_page_ranges(pages_string):
    """Converte es: '1-3,5,7-9' in [1,2,3,5,7,8,9]."""
    result = []
    parts = pages_string.split(",")
    for part in parts:
        part = part.strip()
        if "-" in part:
            start, end = part.split("-")
            start, end = int(start), int(end)
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return sorted(set(result))
