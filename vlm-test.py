import fitz
import ollama
import base64


def pdf_to_image(pdf_path):
    doc = fitz.open(pdf_path)

    page = doc[0]

    pix = page.get_pixmap(
        dpi=300
    )

    path = "sensitive/page.png"
    pix.save(path)

    return path


def ask_vlm(image_path):

    with open(image_path, "rb") as f:
        image = base64.b64encode(
            f.read()
        ).decode()

    response = ollama.chat(
        model="qwen3-vl:8b",
        messages=[
            {
                "role": "user",
                "content":
                """
                Extract:
                - all_human_names
                - claim_number
                - procedure_blocks
                - evidence (including row and column number of table, if present) of all reported data

                NOTE:
                A procedure block is an object containing three key features: the ADA code of the procedure, the corresponding amount that was paid by the insurance provider, and the 3-digit EOB code for this procedure.

                General JSON Schema:

                {
                    "(field name)": {
                        "value": "X",
                        "evidence": [
                        {
                            "table": "X",
                            "row": "X",
                            "column": "X",
                            "page_location_relative": "X"
                        }
                        ]
                    }
                }

                Procedure Block Json Schema:
                {
                    "count": "X",
                    "values": [
                    {
                        "ada_code": "X",
                        "amt_paid": "X",
                        "eob_code": "X"
                    }
                    ]
                }

                Human Names Schema:
                {
                    "ranked_names": [
                    {
                        "name": "X",
                        "confidence": "X%",
                        "reasoning": "Why this name is likely the patient name",
                        "evidence": [
                        {
                            "table": "X",
                            "row": "X",
                            "column": "X",
                            "page_location_relative": "X"
                        }
                        ]
                    }
                    ]
                }

                Return a VALID JSON BLOCK, followed by a hashtag on a new line. The hashtag should fall after all JSON is complete. Additional comments may come anywhere after the hashtag.

                NOTES: 
                This is an Explanation of Benefits (EOB) document from an insurance provider.   
                If any field is blank or cannot be identified, report the contents as null.
                Be specific and extract values exactly as they appear on the document.
                Ensure amt_paid is NOT the amount the patient is responsible for. There will be a specific row or column labeled "AMOUNT PAID" or similar -- Find amt_paid there.
                
                Human Names Ranking Guidelines:
                - Look for names near "Patient:", "Name:", "Patient Name:", or similar labels
                - Names in the header/top of the document are more likely to be the patient
                - Names in billing/payment sections are less likely to be the patient
                - Consider names that appear with addresses or contact information
                - Rank by proximity to patient-related labels and document section context
                """,
                "images":[image]
            }
        ],
        options={
        'num_ctx': 8192
        }
    )

    return response["message"]["content"]



image = 'sensitive/EOB/page-25.png'

result = ask_vlm(image)

print(result)