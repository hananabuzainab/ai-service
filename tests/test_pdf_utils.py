
from unittest.mock import MagicMock

import pytest

from app.pdf_utils import (
    extract_text_from_bytes,
    extract_text_from_pdf,
    ResumeError,
    MAX_SIZE,
    MAX_PAGES,
)


def test_extract_txt():
    content = (
        "Python developer with experience in Django "
        "and PostgreSQL database systems."
    )

    result = extract_text_from_bytes(
        content.encode("utf-8"),
        "resume.txt"
    )

    assert "Python" in result


def test_extract_txt_with_bom():
    content = (
        "\ufeffPython developer with experience in Django "
        "and PostgreSQL database systems."
    )

    result = extract_text_from_bytes(
        content.encode("utf-8"),
        "resume.txt"
    )

    assert result.startswith("Python")


def test_empty_file():
    with pytest.raises(ResumeError) as error:
        extract_text_from_bytes(
            b"",
            "resume.pdf"
        )

    assert error.value.code == "EMPTY_FILE"


def test_file_too_large():
    data = b"A" * (MAX_SIZE + 1)

    with pytest.raises(ResumeError) as error:
        extract_text_from_bytes(
            data,
            "resume.txt"
        )

    assert error.value.code == "FILE_TOO_LARGE"


def test_unsupported_file_type():
    with pytest.raises(ResumeError) as error:
        extract_text_from_bytes(
            b"some content",
            "resume.docx"
        )

    assert error.value.code == "UNSUPPORTED_TYPE"


def test_invalid_pdf_signature():
    with pytest.raises(ResumeError) as error:
        extract_text_from_bytes(
            b"NOT A PDF FILE",
            "resume.pdf"
        )

    assert error.value.code == "NOT_A_PDF"


def test_bad_txt_encoding():
    with pytest.raises(ResumeError) as error:
        extract_text_from_bytes(
            b"\xff\xfe\xfa",
            "resume.txt"
        )

    assert error.value.code == "BAD_ENCODING"


def test_short_text_rejected():
    with pytest.raises(ResumeError) as error:
        extract_text_from_bytes(
            b"Short text",
            "resume.txt"
        )

    assert error.value.code == "NO_TEXT"


def test_too_many_pdf_pages(monkeypatch):
    fake_pdf = MagicMock()

    fake_pdf.__enter__.return_value = fake_pdf
    fake_pdf.__exit__.return_value = False

    fake_pdf.pages = [MagicMock()] * (MAX_PAGES + 1)

    monkeypatch.setattr(
        "app.pdf_utils.pdfplumber.open",
        lambda *args, **kwargs: fake_pdf
    )

    with pytest.raises(ResumeError) as error:
        from app.pdf_utils import _read_pdf

        _read_pdf(b"%PDF fake content")

    assert error.value.code == "TOO_MANY_PAGES"


def test_pdf_password_error(monkeypatch):
    def fake_open(*args, **kwargs):
        raise Exception("PDFPasswordIncorrect")

    monkeypatch.setattr(
        "app.pdf_utils.pdfplumber.open",
        fake_open
    )

    from app.pdf_utils import _read_pdf

    with pytest.raises(ResumeError) as error:
        _read_pdf(b"%PDF fake content")

    assert error.value.code == "PDF_PASSWORD"


def test_extract_pdf_from_path(tmp_path):
    file_path = tmp_path / "resume.pdf"

    file_path.write_bytes(
        b"A" * (MAX_SIZE + 1)
    )

    with pytest.raises(ResumeError) as error:
        extract_text_from_pdf(str(file_path))

    assert error.value.code == "FILE_TOO_LARGE"
