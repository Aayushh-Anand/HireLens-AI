
from io import BytesIO
from pathlib import Path

import pymupdf
from docx import Document


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class DocumentParsingError(Exception):
    """Raised when a resume cannot be parsed safely."""


def extract_resume_text(filename: str, content: bytes) -> str:
    """
    Extract text from a PDF or DOCX resume held in memory.
    The uploaded document is not saved to disk.
    """
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DocumentParsingError(
            "Unsupported file type. Upload a PDF or DOCX file."
        )

    if not content:
        raise DocumentParsingError("The uploaded file is empty.")

    try:
        if extension == ".pdf":
            text = _extract_pdf_text(content)
        else:
            text = _extract_docx_text(content)
    except DocumentParsingError:
        raise
    except Exception as exc:
        raise DocumentParsingError(
            "The document could not be read. Check that it is a valid PDF or DOCX."
        ) from exc

    cleaned_text = _clean_text(text)

    if not cleaned_text:
        raise DocumentParsingError(
            "No readable text was found. Scanned PDFs may require OCR, "
            "which is not included in this phase."
        )

    return cleaned_text


def _extract_pdf_text(content: bytes) -> str:
    with pymupdf.open(stream=content, filetype="pdf") as pdf:
        if pdf.needs_pass:
            raise DocumentParsingError(
                "Password-protected PDFs are not supported."
            )

        if len(pdf) == 0:
            raise DocumentParsingError("The PDF contains no pages.")

        if len(pdf) > 20:
            raise DocumentParsingError(
                "The resume exceeds the 20-page limit."
            )

        pages = [page.get_text("text") for page in pdf]
        return "\n".join(pages)


def _extract_docx_text(content: bytes) -> str:
    document = Document(BytesIO(content))

    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    # Include text from tables, which are common in resumes.
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            non_empty_cells = [cell for cell in cells if cell]
            if non_empty_cells:
                paragraphs.append(" | ".join(non_empty_cells))

    return "\n".join(paragraphs)


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in lines if line]
    return "\n".join(non_empty_lines)
