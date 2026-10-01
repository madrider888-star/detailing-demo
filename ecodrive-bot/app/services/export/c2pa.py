"""Перенос C2PA Content Credentials (JUMBF) при перекодировании в JPEG.

Модуль ничего не подписывает и не подделывает: он лишь не даёт перекодированию
молча потерять манифест происхождения. Поскольку пиксели изменены, валидаторы
C2PA покажут, что файл редактировался после подписи, — это ожидаемо и честно.
"""

from __future__ import annotations

import struct
import zlib

_APP11 = 0xEB
_MAX_SEGMENT_PAYLOAD = 0xFFFF - 2  # длина сегмента включает 2 байта самого поля длины
_JPEG_STANDALONE = {0x01, *range(0xD0, 0xD8)}


def _iter_jpeg_segments(data: bytes) -> list[tuple[int, int, int]]:
    """(marker, начало сегмента, конец сегмента) до начала скана."""
    segments: list[tuple[int, int, int]] = []
    if not data.startswith(b"\xff\xd8"):
        return segments
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            break
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker in _JPEG_STANDALONE:
            pos += 2
            continue
        length = struct.unpack(">H", data[pos + 2 : pos + 4])[0]
        end = pos + 2 + length
        segments.append((marker, pos, end))
        if marker == 0xDA:  # SOS — дальше данные изображения
            break
        pos = end
    return segments


def _box_header_len(box: bytes) -> int:
    lbox = struct.unpack(">I", box[:4])[0] if len(box) >= 8 else 0
    return 16 if lbox == 1 else 8


def _extract_from_jpeg(data: bytes) -> bytes | None:
    groups: dict[bytes, list[tuple[int, bytes]]] = {}
    for marker, start, end in _iter_jpeg_segments(data):
        if marker != _APP11:
            continue
        payload = data[start + 4 : end]
        if len(payload) < 16 or payload[:2] != b"JP":
            continue
        instance = payload[2:4]
        seq = struct.unpack(">I", payload[4:8])[0]
        groups.setdefault(instance, []).append((seq, payload[8:]))
    for parts in groups.values():
        parts.sort(key=lambda item: item[0])
        first = parts[0][1]
        header_len = _box_header_len(first)
        box = first + b"".join(chunk[header_len:] for _, chunk in parts[1:])
        if b"c2pa" in box[: header_len + 64]:
            return box
    return None


def _extract_from_png(data: bytes) -> bytes | None:
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        if ctype == b"caBX":
            return data[pos + 8 : pos + 8 + length]
        if ctype == b"IEND":
            break
        pos += 12 + length
    return None


def extract_c2pa(data: bytes) -> bytes | None:
    """Возвращает JUMBF-хранилище манифестов C2PA, если оно есть в JPEG или PNG."""
    return _extract_from_jpeg(data) or _extract_from_png(data)


def _app11_segments(jumbf: bytes, instance: int = 1) -> list[bytes]:
    header_len = _box_header_len(jumbf)
    header, body = jumbf[:header_len], jumbf[header_len:]
    first_room = _MAX_SEGMENT_PAYLOAD - 8 - header_len
    next_room = _MAX_SEGMENT_PAYLOAD - 8 - header_len
    chunks = [body[:first_room]]
    rest = body[first_room:]
    while rest:
        chunks.append(rest[:next_room])
        rest = rest[next_room:]
    segments = []
    for seq, chunk in enumerate(chunks, start=1):
        payload = b"JP" + struct.pack(">HI", instance, seq) + header + chunk
        segments.append(b"\xff\xeb" + struct.pack(">H", len(payload) + 2) + payload)
    return segments


def embed_c2pa_jpeg(jpeg: bytes, jumbf: bytes) -> bytes:
    """Вставляет JUMBF в JPEG сразу после APP-сегментов (EXIF, ICC)."""
    if not jpeg.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG")
    if _extract_from_jpeg(jpeg) is not None:
        return jpeg  # уже есть — не дублируем
    insert_at = 2
    for marker, _start, end in _iter_jpeg_segments(jpeg):
        if 0xE0 <= marker <= 0xEF:
            insert_at = end
        else:
            break
    return jpeg[:insert_at] + b"".join(_app11_segments(jumbf)) + jpeg[insert_at:]


def make_test_jumbf(payload: bytes = b"test-manifest") -> bytes:
    """Минимальный JUMBF-бокс с меткой c2pa — для тестов."""
    label = b"c2pa\x00"
    desc_content = b"\x00" * 16 + b"\x03" + label  # UUID + toggles + label
    jumd = struct.pack(">I", 8 + len(desc_content)) + b"jumd" + desc_content
    data_box = struct.pack(">I", 8 + len(payload)) + b"json" + payload
    inner = jumd + data_box
    return struct.pack(">I", 8 + len(inner)) + b"jumb" + inner


def embed_c2pa_png(png: bytes, jumbf: bytes) -> bytes:
    """Добавляет caBX-чанк (C2PA) в PNG сразу после IHDR."""
    if _extract_from_png(png) is not None:
        return png
    ihdr_end = 8 + 12 + struct.unpack(">I", png[8:12])[0]
    chunk = struct.pack(">I", len(jumbf)) + b"caBX" + jumbf
    chunk += struct.pack(">I", zlib.crc32(b"caBX" + jumbf) & 0xFFFFFFFF)
    return png[:ihdr_end] + chunk + png[ihdr_end:]
