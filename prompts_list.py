#July 11; first prompt
message_1_all=      """      
                Extract: 
                - all_human_names
                - claim_number
                - procedure_blocks
                - evidence (including table number, row and column number of table, if present) of all reported data
                - confidence
                
                TABLE IDENTIFICATION:
                - Number tables sequentially from top to bottom: Table 1, Table 2, Table 3, etc.
                - A single image may contain multiple tables
                - A table may contain multiple patient names and/or multiple procedure codes

                NOTE:
                A procedure block is an object containing three key features: the ADA code of the procedure, the corresponding amount that was paid by the insurance provider, and the 3-digit EOB code for this procedure.

                General JSON Schema:

                {
                    "field_name": {
                        "value": "X",
                        "conf": "X",
                        "evidence": [
                        {
                            "table": "Table 1",  # Reference to the table containing this data
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
                            "table": "Table 1",  # Reference to the table containing this name
                            "row": "X",
                            "column": "X",
                            "page_location_relative": "X"
                        }
                        ]
                    }
                    ]
                }

                Return a VALID JSON BLOCK, followed by a hashtag on a new line. The hashtag should fall after all JSON is complete. Additional comments may come anywhere after the hashtag. Do not comment before the JSON and hashtag.

                NOTES: 
                This is an Explanation of Benefits (EOB) document from an insurance provider.   
                If any field is blank or cannot be identified, report the contents as null.
                Be specific and extract values exactly as they appear on the document.
                amt_paid will NEVER fall under a column labeled AMOUNT ALLOWED. Do not pull data from that column at all.
                Ensure amt_paid is NOT the amount the patient is responsible for. There will be a specific row or column labeled "AMOUNT PAID", "PLAN PAYMENT" or similar -- Find amt_paid there.
                Each evidence block should come directly after the value it refers to.
                
                Human Names Ranking Guidelines:
                - Look for names near "Patient:", "Name:", "Patient Name:", or similar labels
                - Names in the header/top of the document are more likely to be the patient
                - Names in billing/payment sections are less likely to be the patient
                - Consider names that appear with addresses or contact information
                - Rank by proximity to patient-related labels and document section context

                IMPORTANT:
                REVIEW YOUR OUTPUT. If any information does not match what is contained in the document, or does not follow these prompt rules, print "OUTPUT_NULL" at the very end of your response.
                """

#July 12; Created multiple claim objects per table; for united group
#August 1; working prompt
message_2_united =     """
                Analyze this EOB (Explanation of Benefits) document and extract all claim data. Each table contains a separate claim.

                For each claim, extract:
                - patient_name
                - claim_number
                - ada_codes
                    - alphanumeric_code
                    - amount_paid
                - evidence (including table number, row and column number of table, if present) of all reported data --- numbering of table rows and columns begins at one. Header rows count as row 1.

                
                TABLE IDENTIFICATION:
                - Number tables sequentially from top to bottom: table 1, table 2, table 3, etc.
                - A single image may contain multiple tables (1 to 3 tables per scan)
                - Each table will have its own claim number

                Before extracting data:
                1. Identify every separate claim table on the page.
                2. Count the tables.
                3. Then extract every table independently.
                Do not merge information between tables.

                OUTPUT FORMAT - Array of Claim Objects:
                Return a JSON object with a top-level "claims" array. Each element in the array represents ONE complete claim object from ONE table. Do not add any additional keys, fields, explanations, or markdown formatting. Structure the JSON as follows:

                {
                    "claims": [
                        {
                            "patient_name": {
                                "value": "X",
                                "evidence": {
                                    "table": "table X",
                                    "row": "X",
                                    "column": "X"
                                }
                            },
                            "claim_number": {
                                "value": "X",
                                "evidence": {
                                    "table": "table X",
                                    "row": "X",
                                    "column": "X"
                                }
                            },
                            "ada_codes": [
                                {
                                    "alphanumeric_code": {
                                        "value": "X",
                                        "evidence": {
                                            "table": "table X",
                                            "row": "X",
                                            "column": "X"
                                        }
                                    },
                                    "amount_paid":{
                                        "value": "X",
                                        "evidence": {
                                            "table": "table X",
                                            "row": "X",
                                            "column": "X"
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }


                KEY REQUIREMENTS:
                - Return ALL claims found in the image, each in its own object within the "claims" array
                - If a field is blank or cannot be identified, report the "value", "table", "column", and "row" fields as null.
                - Be specific and extract values exactly as they appear on the document. Do not infer uncertain values from unassociated rows, columns, or tables.
                - There will be a specific column labeled "AMOUNT PAID". Find amount_paid there and nowhere else. DO NOT EXTRACT FROM "PATIENT RESP".
                - The claim number will be the final string of digits in row 2, column 1 of any given claim table.

                """
