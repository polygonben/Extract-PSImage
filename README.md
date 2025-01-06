# Extract-PSImage

A Python utility to extract PowerShell scripts hidden in PNG images by [Invoke-PSImage](https://github.com/peewpw/Invoke-PSImage).

**Invoke-PSImage** is a PowerShell script by [Barrett Adams (@peewpw)](https://twitter.com/peewpw) that performs steganography. It reads a `.ps1` script, converts it into a byte array, and then encodes those bytes into a PNG image. When run, it also generates a one-liner that can recover and execute that hidden script in memory.

## How Invoke-PSImage Encodes Data

Invoke-PSImage supports **two** main ways to place script bytes into the image. This Python script will attempt **both** decoding methods automatically.

1. **Embedding Method (LSB-based)**  
   - When you provide an **existing** image with the `-Image` parameter, Invoke-PSImage *embeds* the script using the *least significant bits* (LSB) of certain color channels.  
   - Concretely, it uses:
     - **Blue channel** & 0x0F → becomes the *high nibble*  
     - **Green channel** & 0x0F → becomes the *low nibble*  
   - Each pixel thus contributes one byte of the script. The Red channel is sometimes used for random filler to minimize image distortion.

2. **New Image Method (Raw BGR)**  
   - When you **do not** provide an existing image, Invoke-PSImage creates a **new** PNG that’s just big enough to hold the script bytes.  
   - Each pixel stores 3 full bytes in the order: `(Blue, Green, Red)`.  
   - Because it’s a brand-new image, distortion is irrelevant. The script is essentially stored “as-is” within each pixel’s color channels.

## Why There’s Trailing Garbage

Invoke-PSImage **does not** record the exact length of the hidden script. It just fills the rest of the image with random bytes. Consequently, **when decoding**, you can end up with some garbled data at the end.

## What This Script Does

1. **Loads the PNG** using the Python Pillow library.  
2. **Decodes** via both:
   - **LSB-based** (Method A) – tries `(B & 0x0F) << 4 | (G & 0x0F)`.  
   - **Raw BGR** (Method B) – reads each pixel’s `(Blue, Green, Red)` as three separate bytes.  
3. **Attempts to remove** any trailing garbage by scanning for a stretch of ASCII text at the end.  
4. **Writes** two output files for each method:
   - A **“.full.txt”** containing **all** bytes after decoding (no trimming).  
   - A **“.txt”** that attempts to remove the trailing gibberish.  

In many cases, **one** of these outputs will contain the clean PowerShell script you’re looking for.

## Usage

1. **Install dependencies**:  
   ```bash
   pip install Pillow
   ```
2. **Run**:  
   ```bash
   python extract_ps_image.py <encoded_image.png>
   ```
3. **Check** the output files:  
   - `decoded_embedded.full.txt` / `decoded_embedded.txt` (LSB approach)  
   - `decoded_raw.full.txt` / `decoded_raw.txt` (Raw BGR approach)

If you still see junk, you can manually edit or tweak the `strip_trailing_garbage` function in the script.
