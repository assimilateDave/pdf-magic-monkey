# OCR Preprocessing Configuration Examples

This file shows example configurations for different document types and use cases.

## Configuration for Clean Documents (Minimal Processing)

```yaml
# For clean, high-quality documents
orientation_correction:
  enabled: true  # Keep enabled for scanned documents

basic_preprocessing:
  enabled: true
  adaptive_threshold:
    block_size: 15
    c_value: 11
  median_blur:
    kernel_size: 1  # Minimal blur for clean docs
  sharpen:
    enabled: false  # Disable sharpening for clean docs
  contrast_enhancement:
    factor: 1.2  # Minimal contrast adjustment

noise_removal:
  enabled: false  # Skip for clean documents

morphological_operations:
  enabled: false  # Skip for clean documents

line_removal:
  enabled: false  # Skip for clean documents

debug:
  save_images: false  # Disable to save disk space
```

## Configuration for Born-Digital Documents (Disable Orientation Correction)

```yaml
# For documents that are born-digital (never scanned/rotated)
orientation_correction:
  enabled: false  # Disable for born-digital documents

basic_preprocessing:
  enabled: true
  adaptive_threshold:
    block_size: 11
    c_value: 8
  median_blur:
    kernel_size: 1
  sharpen:
    enabled: false
  contrast_enhancement:
    factor: 1.0  # No enhancement needed

noise_removal:
  enabled: false

morphological_operations:
  enabled: false

line_removal:
  enabled: false

debug:
  save_images: false
```

## Configuration for Noisy Fax Documents (Aggressive Processing)

```yaml
# For noisy, low-quality fax documents
orientation_correction:
  enabled: true  # Essential for faxes that may be rotated

basic_preprocessing:
  enabled: true
  adaptive_threshold:
    block_size: 21  # Larger block for noisy docs
    c_value: 15    # Higher C value for noise
  median_blur:
    kernel_size: 5  # More aggressive blur
  sharpen:
    enabled: true
  contrast_enhancement:
    factor: 2.5  # Strong contrast enhancement

noise_removal:
  enabled: true
  method: "fastNlMeansDenoising"
  h: 15  # Aggressive noise removal
  templateWindowSize: 9
  searchWindowSize: 25

morphological_operations:
  enabled: true
  operations:
    - type: "opening"
      kernel_size: [3, 3]
      kernel_shape: "ellipse"
      iterations: 2  # More iterations for noisy docs
    - type: "closing"
      kernel_size: [2, 2]
      kernel_shape: "ellipse"
      iterations: 1

line_removal:
  enabled: true
  threshold: 80  # Lower threshold to catch more lines
  min_line_length: 30  # Shorter minimum length
  max_line_gap: 15  # Larger gap tolerance
  line_thickness: 5  # Thicker erasure
  angle_tolerance: 15  # More tolerance for skewed lines

debug:
  save_images: true  # Enable for troubleshooting
```

## Configuration for Form Processing (Line Removal Focus)

```yaml
# For forms with table borders and lines to remove
orientation_correction:
  enabled: true  # Important for scanned forms

basic_preprocessing:
  enabled: true

noise_removal:
  enabled: false  # Forms are usually clean

morphological_operations:
  enabled: true
  operations:
    - type: "opening"
      kernel_size: [2, 2]  # Small kernel to preserve text
      kernel_shape: "ellipse"
      iterations: 1

line_removal:
  enabled: true
  threshold: 150  # High threshold for strong lines
  min_line_length: 80  # Long lines typical in forms
  max_line_gap: 5   # Small gap for continuous lines
  line_thickness: 7  # Thick erasure for form lines
  horizontal_lines: true
  vertical_lines: true
  angle_tolerance: 5  # Strict tolerance for clean forms

debug:
  save_images: true
  subfolders:
    lines: "form_lines"  # Custom subfolder name
```