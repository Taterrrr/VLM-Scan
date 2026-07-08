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
                - patient name
                - claim number
                - each amount the patient is responsible for
                - evidence (including row and column number of table, if present) of all reported data

                JSON Schema:

                {
                    "field name": {
                        "value": "X",
                        "evidence": [
                        {
                            "table": "X",
                            "row": "X",
                            "column": "X"
                        }
                        ]
                    }
                }

                Return a VALID JSON BLOCK, followed by a hashtag on a new line. Additional comments may come anywhere after the hashtag.

                NOTES:
                Patient name must not be Jason Barganier, or similar.     
                If any field is blank or cannot be identified, report the contents as null. 
                """,
                "images":[image]
            }
        ],
        options={
        'num_ctx': 8192
        }
    )

    return response["message"]["content"]


#image = pdf_to_image("sensitive/page-25.pdf")

image = 'sensitive/EOB/page-25.png'

result = ask_vlm(image)

print(result)