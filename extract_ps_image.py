#!/usr/bin/env python3
"""
Decode PowerShell scripts hidden by Invoke-PSImage (both embedding methods),
then try to strip trailing garbage from the decoded data.

Requirements:
    pip install Pillow

Usage:
    python3 decode_psimage.py encoded_image.png

Outputs (for each method):
    decoded_embedded.full.txt  (all raw decoded data, no trimming)
    decoded_embedded.txt       (trimmed attempt)
    decoded_raw.full.txt       (all raw decoded data, no trimming)
    decoded_raw.txt            (trimmed attempt)
"""

import sys
from PIL import Image

def decode_method_a_embedded_lsb(img):
    """
    Decodes the 'embedded' variant of Invoke-PSImage.
    Each pixel's (Blue & 0x0F) is the high nibble,
    and (Green & 0x0F) is the low nibble => one byte.
    """
    width, height = img.size
    pixels = img.load()
    
    byte_array = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            high_nibble = (b & 0x0F) << 4
            low_nibble  = (g & 0x0F)
            one_byte    = high_nibble | low_nibble
            byte_array.append(one_byte)
    
    return bytes(byte_array)

def decode_method_b_raw_bgr(img):
    """
    Decodes the 'new image' variant of Invoke-PSImage.
    Each pixel's channels are stored in the order (Blue, Green, Red).
    We'll read them out as [B, G, R].
    """
    width, height = img.size
    pixels = img.load()
    
    byte_array = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            # PIL gives us (R, G, B), but script expects B, G, R
            byte_array.append(b)
            byte_array.append(g)
            byte_array.append(r)
    
    return bytes(byte_array)

def is_printable_or_whitespace(ch: int) -> bool:
    """
    Rough check if a byte might be part of normal ASCII text or whitespace.
    - ASCII range 32..126 (printable) plus 9..13 for whitespace, plus 10 (LF), etc.
    """
    if 32 <= ch <= 126:
        return True
    # tab/newline/carriage return, etc.
    if ch in (9, 10, 13):
        return True
    return False

def strip_trailing_garbage(decoded_bytes: bytes, min_clean_tail=50) -> bytes:
    """
    Attempt to remove trailing garbage from an ASCII-based script.
    
    Strategy:
      1. We'll walk backwards from the end.
      2. Keep track of how many consecutive valid chars we see.
      3. Once we see a chunk of valid text (e.g. 50 chars in a row) while scanning backward,
         we assume everything from that point to the end is good text (or close enough).
      4. Return everything up to that point.
    
    Adjust 'min_clean_tail' if your script ends with fewer ASCII chars or
    if you want a more/less strict approach.
    """
    # If the entire buffer is short, just return it.
    if len(decoded_bytes) < min_clean_tail:
        return decoded_bytes
    
    good_end = len(decoded_bytes) - 1
    consecutive_printable = 0
    
    for i in reversed(range(len(decoded_bytes))):
        if is_printable_or_whitespace(decoded_bytes[i]):
            consecutive_printable += 1
        else:
            consecutive_printable = 0
        
        # Once we've encountered enough consecutive "clean" ASCII chars,
        # assume we've reached the real end of the script.
        if consecutive_printable >= min_clean_tail:
            good_end = i + consecutive_printable
            break
    
    return decoded_bytes[:good_end]

def decode_and_save(img_path, out_prefix, decode_func):
    """
    Decode using the supplied decode_func,
    save full content plus stripped content to files.
    """
    img = Image.open(img_path).convert("RGB")
    raw_data = decode_func(img)
    img.close()
    
    # Always write full data as .full.txt
    full_path = f"{out_prefix}.full.txt"
    with open(full_path, "wb") as f:
        f.write(raw_data)
    
    # Attempt ASCII decode and strip trailing garbage
    truncated = strip_trailing_garbage(raw_data)
    
    try:
        truncated_text = truncated.decode("ascii", errors="replace")
    except UnicodeDecodeError:
        # fallback
        truncated_text = repr(truncated)
    
    trimmed_path = f"{out_prefix}.txt"
    with open(trimmed_path, "w", encoding="utf-8") as f:
        f.write(truncated_text)
    
    print(f"[+] Wrote {full_path} (full) and {trimmed_path} (trimmed)")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <encoded_image.png>")
        sys.exit(1)
    
    img_path = sys.argv[1]
    
    # 1) Method A: LSB-based
    print("[*] Decoding (Method A) LSB-based ...")
    decode_and_save(img_path, "decoded_embedded", decode_method_a_embedded_lsb)
    
    # 2) Method B: raw BGR
    print("[*] Decoding (Method B) raw BGR ...")
    decode_and_save(img_path, "decoded_raw", decode_method_b_raw_bgr)
    
    print("\nDone! Check .full.txt for the raw decoded data, and .txt for trimmed results.")
    print("If needed, adjust the strip_trailing_garbage() logic or manually edit the output.\n")

if __name__ == "__main__":
    main()
