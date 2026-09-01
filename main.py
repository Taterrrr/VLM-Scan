import datetime
import os


'''import fitz'''
import ollama
import base64
import time
import prompts_list
import cv2
import json

import prompt_fixes
import custom_errors

pretend = True
'''
def pdf_to_image(pdf_path):
    doc = fitz.open(pdf_path)

    page = doc[0]

    pix = page.get_pixmap(
        dpi=300
    )

    path = "sensitive/page.png"
    pix.save(path)

    return path
'''
    
def black_out_column(image, x_start, x_end):
    """
    Black out a vertical column in an image.

    Args:
        image: OpenCV image (numpy array).
        x_start: Left x-coordinate (inclusive).
        x_end: Right x-coordinate (exclusive).

    Returns:
        Modified image.
    """
    result = cv2.imread(image)
    result[:, x_start:x_end] = 0
    return result

def syntax_check(response):

    if not isinstance(response, dict):
        raise custom_errors.NotDictError
        
    try:
        if len(response["claims"]) > 3:
            raise custom_errors.TooManyTablesError
    except KeyError:
        raise custom_errors.ClaimsNameError

    allowed = {"patient_name", "claim_number", "ada_codes"}
    if not set(response["claims"][0]).issubset(allowed):
        raise custom_errors.KeysNameError


    


def parse_vlm_output(response):
    """Parse VLM JSON output into Python objects."""
    # The response is a ChatResponse object from ollama
    # The actual message content is in response.message.content
    json_string = response.strip()
    #print(json_string)
    return json.loads(json_string)

def ask_vlm(image_path, prompt):
    if not prompt:
        raise custom_errors.MissingInputError("Missing prompt for VLM input")
    elif not image_path:
        raise custom_errors.MissingInputError("Missing image for VLM input")
    
    with open(image_path, "rb") as f:
        image = base64.b64encode(
            f.read()
        ).decode()


    ollama_start = time.perf_counter()
    response = ollama.chat(
        model="qwen3-vl:8b",
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images":[image]
            }
        ],
        options={
        'num_ctx': 8192
        }
    )

    responsedumped = parse_vlm_output(response.message.content)
    end_time = time.perf_counter()
    total_ollama_time = end_time - ollama_start

    if not response.message.content:
        raise custom_errors.NoResponseError("VLM output empty")     #error raising
    syntax_check(responsedumped)
    

    return responsedumped, total_ollama_time, response.message.content


image = 'sensitive/EOB/page-25.png'

blackout = black_out_column(image, 1885, 2070)
cv2.imwrite("sensitive/EOB/blackout.png", blackout)

#quit()

tryagain = 0                    #RUN VLM BLOCK
retry = True
fixmessage = ""
while retry:
    retry = False
    if fixmessage != "":
        print("Fixmessage triggered.")
        tryagain += 1
        if tryagain == 3:
            raise custom_errors.RetryLimitExceededError("Too many retries")
    try:
        result, time_taken, result_raw = ask_vlm("sensitive/EOB/blackout.png", (prompts_list.message_2_united + (fixmessage if fixmessage != "" else "")))
        fixmessage = ""
    except custom_errors.TooManyTablesError:
        retry = True
        fixmessage = prompt_fixes.too_many_tables_united
        print("Too many tables.")
    except custom_errors.NoResponseError:
        retry = True
    except custom_errors.KeysNameError:
        retry = True
        fixmessage = prompt_fixes.stick_to_script
        print("Claims keys mislabeled.")
    except custom_errors.ClaimsNameError:                                                 
        retry = True
        fixmessage = prompt_fixes.stick_to_script
        print("Claims dict mislabeled.")
    except custom_errors.NotDictError:
        retry = True
        fixmessage = prompt_fixes.stick_to_script
        print("Not a dict.")

                                #VLM NOW COMPLETE
    

        


print(f"VLM OUT: \n{result_raw}")
print(f"Debug stats: {'Retries: ' + str(tryagain) if tryagain else ''}" if tryagain else "")  #fill once debug variables known
print(f"Time Taken: {time_taken:.2f} seconds.")
print(f"Tables: {len(result["claims"])}")

# Append result to a new file in the vlm_out folder
#os.makedirs("vlm_out", exist_ok=True)
filename = f"claim_{result["claims"][0]["claim_number"]["value"]}.txt"
filepath = os.path.join("vlm_out", filename)
with open(filepath, "a") as f:
    f.write(result)
print(f"Result appended to: {filepath}")



