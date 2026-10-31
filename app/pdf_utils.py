
import io

import pdfplumber


# --------------------------------------------------
# Configuration
# --------------------------------------------------

MAX_SIZE = 5 * 1024 * 1024  # 5 MB

MAX_PAGES = 30

MIN_CHARS = 50

MAX_EXTRACTED_CHARS = 100_000


# --------------------------------------------------
# Custom errors
# --------------------------------------------------

class ResumeError(Exception):

    def __init__(self, code, message):
        self.code = code
        self.message = message

        super().__init__(message)


# --------------------------------------------------
# PDF extraction
# --------------------------------------------------

def _read_pdf(data):
    """
    Extract text from a PDF file.

    Limitations:
    - Maximum 30 pages.
    - Maximum 100,000 extracted characters.
    - Scanned PDFs without a text layer are not supported.
    """

    try:

        pages_text = []

        with pdfplumber.open(io.BytesIO(data)) as pdf:

            if len(pdf.pages) > MAX_PAGES:
                raise ResumeError(
                    "TOO_MANY_PAGES",
                    f"PDF files must not exceed {MAX_PAGES} pages."
                )

            for page in pdf.pages:

                page_text = page.extract_text()

                if not page_text:
                    continue

                pages_text.append(page_text)

                current_length = sum(
                    len(text) for text in pages_text
                )

                if current_length > MAX_EXTRACTED_CHARS:
                    raise ResumeError(
                        "TEXT_TOO_LONG",
                        "The extracted document text is too long."
                    )

        return "\n".join(pages_text)

    except ResumeError:
        raise

    except Exception as error:

        error_info = (
            str(error) + " " + type(error).__name__
        ).lower()

        if (
            "password" in error_info
            or "pdfpasswordincorrect" in error_info
        ):
            raise ResumeError(
                "PDF_PASSWORD",
                "This PDF is password-protected. "
                "Please upload an unlocked file."
            ) from error

        raise ResumeError(
            "PDF_UNREADABLE",
            "We couldn't open this PDF. "
            "The file may be corrupted or invalid."
        ) from error


# --------------------------------------------------
# Main extraction function
# --------------------------------------------------

def extract_text_from_bytes(data, filename):
    """
    Extract text from PDF or TXT file bytes.

    Supported formats:
    - PDF
    - TXT (UTF-8)

    Returns extracted text or raises ResumeError.
    """

    if not isinstance(data, (bytes, bytearray)):
        raise ResumeError(
            "INVALID_FILE",
            "Invalid file data."
        )

    if len(data) == 0:
        raise ResumeError(
            "EMPTY_FILE",
            "The uploaded file is empty."
        )

    if len(data) > MAX_SIZE:
        raise ResumeError(
            "FILE_TOO_LARGE",
            "The file must not exceed 5 MB."
        )

    filename = (filename or "").lower()

    if filename.endswith(".txt"):

        try:
            text = bytes(data).decode("utf-8-sig")

        except UnicodeDecodeError as error:
            raise ResumeError(
                "BAD_ENCODING",
                "The TXT file must use UTF-8 encoding."
            ) from error

    elif filename.endswith(".pdf"):

        if not bytes(data).startswith(b"%PDF"):
            raise ResumeError(
                "NOT_A_PDF",
                "The uploaded file is not a valid PDF."
            )

        text = _read_pdf(bytes(data))

    else:
        raise ResumeError(
            "UNSUPPORTED_TYPE",
            "Only PDF and TXT files are supported."
        )

    text = text.strip()

    if len(text) < MIN_CHARS:
        raise ResumeError(
            "NO_TEXT",
            "We couldn't extract enough text from this file. "
            "Scanned PDFs and image-only documents are not supported."
        )

    if len(text) > MAX_EXTRACTED_CHARS:
        raise ResumeError(
            "TEXT_TOO_LONG",
            "The extracted document text is too long."
        )

    return text


# --------------------------------------------------
# Path-based helper
# --------------------------------------------------

def extract_text_from_pdf(path):
    """
    Extract text from a PDF file using its path.

    Reads at most MAX_SIZE + 1 bytes to avoid
    loading an oversized file completely.
    """

    with open(path, "rb") as file:
        data = file.read(MAX_SIZE + 1)

    return extract_text_from_bytes(
        data,
        "file.pdf"
    )
