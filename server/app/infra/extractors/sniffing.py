"""Identifies an upload from its own bytes.

The Content-Type header comes from the caller and cannot be trusted, and the extractor has
to know the real format before it decodes anything.
"""

import struct

# The leading bytes of each format's own signature. A short prefix is enough to tell a real
# file from the text a mislabelled control sends, and the decoder catches the rest.
_JPEG = b"\xff\xd8"
_PNG = b"\x89PNG"
_PDF = b"%PDF-"
_RIFF = b"RIFF"
_WEBP = b"WEBP"

# A phone photo is 12-50 megapixels; past this a small file describes an image that would
# cost more memory to decode than the free instance has.
MAX_IMAGE_PIXELS = 50_000_000


def sniff_type(content: bytes) -> str | None:
    if content.startswith(_JPEG):
        return "image/jpeg"
    if content.startswith(_PNG):
        return "image/png"
    if content.startswith(_PDF):
        return "application/pdf"
    if content[:4] == _RIFF and content[8:12] == _WEBP:
        return "image/webp"
    return None


def image_size(content: bytes) -> tuple[int, int] | None:
    """Width and height from the format's own header, without decoding any pixels."""
    kind = sniff_type(content)
    if kind == "image/png":
        return _png_size(content)
    if kind == "image/jpeg":
        return _jpeg_size(content)
    if kind == "image/webp":
        return _webp_size(content)
    return None


def too_many_pixels(content: bytes) -> bool:
    size = image_size(content)
    return size is not None and size[0] * size[1] > MAX_IMAGE_PIXELS


def _png_size(content: bytes) -> tuple[int, int] | None:
    if content[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", content[16:24])


def _jpeg_size(content: bytes) -> tuple[int, int] | None:
    end = len(content)
    index = 2
    while index + 9 <= end:
        if content[index] != 0xFF:
            index += 1
            continue
        marker = content[index + 1]
        if marker == 0x01 or 0xD0 <= marker <= 0xD9:
            index += 2
            continue
        segment = int.from_bytes(content[index + 2 : index + 4], "big")
        # The frame headers (SOF0-SOF15, minus DHT/JPG/DAC) are the ones carrying the size.
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height = int.from_bytes(content[index + 5 : index + 7], "big")
            width = int.from_bytes(content[index + 7 : index + 9], "big")
            return width, height
        if segment < 2:
            return None
        index += 2 + segment
    return None


def _webp_size(content: bytes) -> tuple[int, int] | None:
    if len(content) < 30:
        return None
    chunk = content[12:16]
    if chunk == b"VP8X":
        width = int.from_bytes(content[24:27], "little") + 1
        height = int.from_bytes(content[27:30], "little") + 1
        return width, height
    if chunk == b"VP8L":
        bits = int.from_bytes(content[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if chunk == b"VP8 " and content[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(content[26:28], "little") & 0x3FFF
        height = int.from_bytes(content[28:30], "little") & 0x3FFF
        return width, height
    return None
