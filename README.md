# VLM-Scan

# Plans:

* Use Amt. Paid as insurance amount
* Use Codes to identify for audits

# Needs checking system -- PDF to .md?

# Adjudication:
Qwen3-VL 8B (always loaded)
        |
        |
  extraction
        |
        v
Python validators
        |
        |
  disagreement?
        |
       yes
        |
 same VLM:
 "reinspect these fields only"