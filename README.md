# VLM-Scan

# Plans:

* Use Amt. Paid as insurance amount
* Use Codes to identify for audits
* Make sorting system with specific prompts

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