#July 11; first prompt

message_1_all = """this is a testing prompt. respond with 'hi'."""

message_1_all_temp=  """      
                Analyze this EOB (Explanation of Benefits) document and extract all claim data. Each table contains a separate claim.

                For each claim, extract:
                - claim_number
                - ada_codes
                    - alphanumeric_code
                    - amount_paid
                
                TABLE IDENTIFICATION:
                - Number tables sequentially from top to bottom: table 1, table 2, table 3, etc.
                - A single image may contain multiple tables (1 to 3 tables per scan)
                - Each table will have its own claim number

                Before extracting data:
                1. Identify every separate claim table on the page.
                2. Count the tables.
                3. Extract every table independently.
                Do not merge information between tables.

                OUTPUT FORMAT - Array of Claim Objects:
                Return a JSON object with a top-level "claims" array. Each element in the array represents ONE complete claim object from ONE table. Do not add any additional keys, fields, explanations, or markdown formatting. Structure the JSON as follows:

                {
                    "claims": [
                        {
                            "claim_number": "X",
                            "ada_codes": [
                                {
                                    "alphanumeric_code": "X",
                                    "amount_paid": "X"
                                }
                            ]
                        }
                    ]
                }


                KEY REQUIREMENTS:
                - Return ALL claims found in the image, each in its own object within the "claims" array
                - If a field is blank or cannot be identified, report the field as null.
                - Be specific and extract values exactly as they appear on the document. Do not infer uncertain values from unassociated rows, columns, or tables.
                - There will be a specific column labeled "AMOUNT PAID". Find amount_paid there and nowhere else.
                - The claim number will be the final string of digits in row 2, column 1 of any given claim table.
                - If a claim appears to have no codes, do not include the claim in the final output.
                - If the image appears to have no claims, return an empty "claims" array.
                """

#July 12; Created multiple claim objects per table; for united group
#August 1; working prompt
message_2_united =     """
                Analyze this EOB (Explanation of Benefits) document and extract all claim data. Each table contains a separate claim.

                For each claim, extract:
                - claim_number
                - ada_codes
                    - alphanumeric_code
                    - amount_paid
                
                TABLE IDENTIFICATION:
                - Number tables sequentially from top to bottom: table 1, table 2, table 3, etc.
                - A single image may contain multiple tables (1 to 3 tables per scan)
                - Each table will have its own claim number

                Before extracting data:
                1. Identify every separate claim table on the page.
                2. Count the tables.
                3. Extract every table independently.
                Do not merge information between tables.

                OUTPUT FORMAT - Array of Claim Objects:
                Return a JSON object with a top-level "claims" array. Each element in the array represents ONE complete claim object from ONE table. Do not add any additional keys, fields, explanations, or markdown formatting. Structure the JSON as follows:

                {
                    "claims": [
                        {
                            "claim_number": "X",
                            "ada_codes": [
                                {
                                    "alphanumeric_code": "X",
                                    "amount_paid": "X"
                                }
                            ]
                        }
                    ]
                }


                KEY REQUIREMENTS:
                - Return ALL claims found in the image, each in its own object within the "claims" array
                - If a field is blank or cannot be identified, report the field as null.
                - Be specific and extract values exactly as they appear on the document. Do not infer uncertain values from unassociated rows, columns, or tables.
                - There will be a specific column labeled "AMOUNT PAID". Find amount_paid there and nowhere else.
                - The claim number will be the final string of digits in row 2, column 1 of any given claim table.
                - If a claim appears to have no codes, do not include the claim in the final output.
                - If the image appears to have no claims, return an empty "claims" array.
                """

image_intake = """Analyze this EOB (Explanation of Benefits) document. You will be given an instruction to analyze it in future prompts. Return one word (lowercase, no punctuation): ready"""

what_provider = """
Analyze this EOB (Explanation of Benefits) document. You are tasked with determing the company which created it.
If the document contains either of these two things, you may classify it using what is found. If not, other methods of classification are as described below.

Method 1: Watermarks
Look in the top left corner. The document may contain one of two things: either a watermark that contains "UnitedHealthcare", or a logo with "PAI" written on it. PAI stands for Planned Administrators Inc. Classify the documents according to their watermark.

METHOD 2: Color Coding
Documents from UnitedHealthcare will contain little to no color. All elements will be either black, white, or gray. Documents from PAI, however, use a blue-and-gray color scheme. Elements from PAI will often be either blue or gray. Classify accordingly.

METHOD 3: Shape Coding
Documents from UnitedHealthcare use square edges on and within most elements. Documents from PAI, however, will use a rounded scheme. Elements in a PAI document will often have rounded edges, mixed with some square. Classify accordingly.

Attempt to use each method as needed.
Finding the provider is the goal; however, if each method fails to determine the correct classification, none_found may be a necessary output. 

OUTPUT STRUCTURE: Output a single phrase. All letters must be lowercase. Do not include any whitespace, punctuation or newlines, other than the underscore included in the example. The word should follow the classification of the document. It may be any of these three:

united_health
planned_admin
none_found

Do not output anything besides exactly ONE of the listed phrases.
"""

message_3_pai_not_ready_need_to_see_valid_claim_and_edit = """
Analyze this EOB (Explanation of Benefits) document and extract all claim data. Each table may contain a separate claim.

                For each claim, extract:
                - claim_number
                - ada_codes
                    - alphanumeric_code
                    - amount_paid
                
                TABLE IDENTIFICATION:
                - Number tables sequentially from top to bottom: table 1, table 2, table 3, etc.
                - A single image may contain multiple tables (1 to 3 tables per scan)
                - Each table will have its own claim number

                Before extracting data:
                1. Identify every separate claim table on the page.
                2. Count the tables.
                3. Extract every table independently.
                Do not merge information between tables.

                OUTPUT FORMAT - Array of Claim Objects:
                Return a JSON object with a top-level "claims" array. Each element in the array represents ONE complete claim object from ONE table. Do not add any additional keys, fields, explanations, or markdown formatting. Structure the JSON as follows:

                {
                    "claims": [
                        {
                            "claim_number": "X",
                            "ada_codes": [
                                {
                                    "alphanumeric_code": "X",
                                    "amount_paid": "X"
                                }
                            ]
                        }
                    ]
                }


                KEY REQUIREMENTS:
                - Return ALL claims found in the image, each in its own object within the "claims" array
                - If a field is blank or cannot be identified, report the field as null.
                - Be specific and extract values exactly as they appear on the document. Do not infer uncertain values from unassociated rows, columns, or tables.
                - There will be a specific column labeled "AMOUNT PAID". Find amount_paid there and nowhere else.
                - The claim number will be the final string of digits in row 2, column 1 of any given claim table.
                - If a claim appears to have no codes, do not include the claim in the final output.
                - If the image appears to have no claims, return an empty "claims" array.
                """