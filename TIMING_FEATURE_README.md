# OCR Preprocessing Timing and Logging Feature

## Overview
The OCR preprocessing pipeline now includes optional timing and logging functionality to help users profile and debug bottlenecks in the preprocessing workflow.

## Configuration
Add the `log_timings` option to the `debug` section in `ocr_preprocess.yaml`:

```yaml
debug:
  save_images: true
  base_folder: "debug_imgs"
  log_timings: false  # Toggle timing log output for pre-processing steps
  subfolders:
    # ... existing subfolder configuration
```

## Usage
1. Set `log_timings: true` in your `ocr_preprocess.yaml` file
2. Run your normal PDF processing
3. Check the `Pre_Proc_logs/` directory for timing information

## Log Format
Timing logs are saved to `Pre_Proc_logs/preprocessing_timings_YYYYMMDD.log` with the format:
```
[YYYY-MM-DD HH:MM:SS] filename_pageN | step_name | duration
```

Example log entries:
```
[2025-08-20 21:15:44] document_page_0 | orientation_correction | 0.020s
[2025-08-20 21:15:44] document_page_0 | basic | 0.012s
[2025-08-20 21:15:44] document_page_0 | noise_removal | 0.095s
[2025-08-20 21:15:44] document_page_0 | morphological_operations | 0.003s
[2025-08-20 21:15:44] document_page_0 | line_removal | 0.090s
```

## Robustness
- The feature is robust and will not break processing if `log_timings` is `false` or missing
- Logging failures are handled gracefully without interrupting the processing workflow
- No performance impact when timing is disabled

## Benefits
- Identify bottlenecks in the preprocessing pipeline
- Compare performance between different configurations
- Monitor processing performance over time
- Debug processing issues by correlating timing with steps