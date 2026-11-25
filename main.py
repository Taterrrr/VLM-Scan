from datetime import datetime
import os
import fitz
import ollama
import base64
import time
import prompts_list
import cv2
import json
from pathlib import Path

import prompt_fixes
import custom_errors


def pdf_to_images(pdf_path: str | Path, output_folder: str = "processing/pre_bucket", dpi: int = 180) -> list[Path]:
    """
    Render every page in a PDF as a PNG image.

    Returns a list of the created image paths.
    """
    pdf_path = Path(pdf_path)
    output_folder = Path(output_folder)

    zoom = dpi / 72  # PDFs use 72 points per inch
    matrix = fitz.Matrix(zoom, zoom)
    image_paths = []

    with fitz.open(pdf_path) as document:
        for page_number, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_folder / f"{pdf_path.stem}_page_{page_number:03d}.png"
            pixmap.save(image_path)
            image_paths.append(image_path)

    return image_paths
    
def black_out_column(image, x_start, x_end):   #deprecated
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

    allowed = {"claim_number", "ada_codes"}
    if not set(response["claims"][0]).issubset(allowed):
        raise custom_errors.KeysNameError


    


def parse_vlm_output(response):
    """Parse VLM JSON output into Python objects."""
    # The response is a ChatResponse object from ollama
    # The actual message content is in response.message.content
    json_string = response.strip()
    #print(json_string)
    return json.loads(json_string)

VLM_MODEL = "qwen3-vl:8b"
VLM_NUM_CTX = 8192


def encode_image(image_path):
    """Return the base64 string of an image file."""
    with open(image_path, "rb") as f:
        return base64.b64encode(
            f.read()
        ).decode()


def start_vlm_session(image_path, prompt, model=VLM_MODEL):
    """Build the message list for the very first pass over an image."""
    return [
        {
            "role": "user",
            "content": prompt,
            "images": [encode_image(image_path)]
        }
    ]


def ask_vlm(image_path, prompt, history=None, model=VLM_MODEL, num_ctx=VLM_NUM_CTX):
    """Ask the VLM about an image, optionally continuing an earlier conversation.

    First pass: call with image_path + prompt. The returned message history can
    be kept and handed back in on a second pass.

    Second pass: call again with history=<the returned history> and only the new
    prompt (image_path may then be None). The image and every earlier turn are
    resent byte-for-byte identical, so ollama matches its cached prompt prefix
    and answers off the existing KV cache instead of re-running the vision scan.

    Returns (parsed_json, seconds_taken, raw_text, message_history).
    """
    if not prompt:
        raise custom_errors.MissingInputError("Missing prompt for VLM input")
    elif not history and not image_path:
        raise custom_errors.MissingInputError("Missing image for VLM input")

    if history:
        # follow-up prompt: reuse the already-cached image + conversation prefix
        messages = [dict(msg) for msg in history]
        messages.append({
            "role": "user",
            "content": prompt
        })
    else:
        messages = start_vlm_session(image_path, prompt)

    try:
        ollama_start = time.perf_counter()
        response = ollama.chat(
            model=model,
            messages=messages,
            options={
            'num_ctx': num_ctx
            }
        )
        end_time = time.perf_counter()
        total_ollama_time = end_time - ollama_start

        if not response.message.content:
                raise custom_errors.NoResponseError("VLM output empty")
        #print(response.message.content)
        if history:                                                         #only parses 2nd run and beyond (1st is not JSON)
            responsedumped = parse_vlm_output(response.message.content)

             #error raising
            syntax_check(responsedumped)
        else: 
            responsedumped = response.message.content
    except Exception as err:
        # hand the conversation back even on failure, so the retry can continue
        # from the same image instead of paying for a fresh vision scan
        err.vlm_messages = messages
        raise

    # keep the reply in the history so the next prompt lines up exactly with the
    # tokens ollama has already processed
    messages.append({
        "role": "assistant",
        "content": response.message.content
    })

    return responsedumped, total_ollama_time, response.message.content, messages


def follow_up_vlm(history, prompt, model=VLM_MODEL, num_ctx=VLM_NUM_CTX, imagepath = None):
    """Send a second (or later) prompt about the image already in history."""
    if not history:
        raise custom_errors.MissingInputError("Missing history for follow-up prompt")

    return ask_vlm(imagepath, prompt, history=history, model=model, num_ctx=num_ctx)


def compare_payment(filepath: str, database: str):
    with open(filepath, "r") as f:
        claimbook = json.load(f)

    with open(database, "r") as f:
        databason = json.load(f)


    output_dir = "processing/tattletale_out"

    cnum = claimbook["claim_number"]
    discrepancies = []

    for code in claimbook["ada_codes"]:
        readcode = code["alphanumeric_code"]
        amtpaid = float(code["amount_paid"].replace("$", ""))

        if readcode in databason:
            expected = float(databason[readcode])

            if amtpaid != expected:
                discrepancy = amtpaid - expected

                result = {
                    "claim_number": cnum,
                    "ada_code": readcode,
                    "amount_paid": amtpaid,
                    "expected_amount": expected,
                    "discrepancy": discrepancy
                }

                discrepancies.append(result)
                ##print(f"DISCREPANCY FOUND: {result}")

    # Create one JSON file per claim, including its discrepancies
    output_file = f"{output_dir}/{filepath.name}"

    with open(output_file, "w") as f:
        json.dump({
            "claim_number": cnum,
            "discrepancies": (discrepancies if discrepancies else "None")
        }, f, indent=4)

    print(f"Saved {output_file} ({len(discrepancies)} discrepancies)")

def select_prompt(vlmspeak):
    returnedprompt = None
    trueword = str(vlmspeak).strip().lower()
    #print(trueword)
    if trueword == "united_health":
        returnedprompt = prompts_list.message_2_united
    elif trueword == "planned_admin":
        returnedprompt = prompts_list.message_3_pai
    else:
        raise custom_errors.DocumentTypeError('Invalid provider given')

    return returnedprompt


def main(file: list[Path]):
    try:         
        image_list = pdf_to_images(file)
        #blackout = black_out_column(image, 1885, 2070)
        #cv2.imwrite("sensitive/EOB/blackout.png", blackout)

        #quit()

        tryagain = 0                    #RUN VLM BLOCK
        retry = True
        fixmessage = ""
        history = None                  #one conversation over the image, kept warm in the KV cache
        while retry:
            retry = False
            if fixmessage != "":
                print("Fixmessage triggered.")
                tryagain += 1
                if tryagain == 3:
                    raise custom_errors.RetryLimitExceededError("Too many retries")
                fixmessage = ""
            try:
                if history:
                    #second pass on the same image: only the fixmessage is new, the
                    #image and every earlier turn come off the KV cache
                    for run in range(len(image_list)-1):
                        result, time_taken, result_raw, history = follow_up_vlm(history, prompts_list.image_intake, imagepath = image_list[run])
                    result, time_taken, result_raw, history = follow_up_vlm(history, prompts_list.message_1_all + fixmessage)
                    retry = False
                else:
                    result, time_taken, result_raw, history = ask_vlm(image_list[0], prompts_list.image_intake)
                    retry = True
                    #selected_prompt = select_prompt(result)
            except custom_errors.TooManyTablesError as err:
                history = getattr(err, "vlm_messages", history)
                retry = True
                fixmessage = prompt_fixes.too_many_tables_united
                print("Too many tables.")
            except custom_errors.NoResponseError as err:
                history = getattr(err, "vlm_messages", history)
                retry = True
            except custom_errors.KeysNameError as err:
                history = getattr(err, "vlm_messages", history)
                retry = True
                fixmessage = prompt_fixes.stick_to_script
                print("Claims keys mislabeled.")
            except custom_errors.ClaimsNameError as err:                                                 
                history = getattr(err, "vlm_messages", history)
                retry = True
                fixmessage = prompt_fixes.stick_to_script
                print("Claims dict mislabeled.")
            except custom_errors.NotDictError as err:
                history = getattr(err, "vlm_messages", history)
                retry = True
                fixmessage = prompt_fixes.stick_to_script
                print("Not a dict.")

                                        #VLM NOW COMPLETE
            

        claims_list = []
        if result["claims"]:
            for obj in result["claims"]:
                claims_list.append(obj)
        else: 
            raise custom_errors.EmptyDocumentError("Document is empty.")  


                                        ##DEBUG SECTION
        print(f"VLM OUT: \n{result_raw}")
        print(f"Debug stats: {'Retries: ' + str(tryagain) if tryagain else ''}" if tryagain else "")  #fill once debug variables known
        print(f"Time Taken: {time_taken:.2f} seconds.")
        print(f"Tables: {len(result["claims"])}")
                                        ##DEBUG SECTION

        for obj in claims_list:
            now = datetime.now()
            filename = f"claim_{obj["claim_number"]}_{now.year}-{now.month}-{now.day}_{now.hour}-{now.minute}-{now.second}.json"
            filepath = os.path.join("processing/vlm_out", filename)
            with open(filepath, "w") as f:
                json.dump(obj, f, indent=4)

            print(f"AI result written to: {filepath}")

        vlmOutputDir = Path("processing/vlm_out")
        postComparisonDir = Path("processing/post_comparison")
        
        
        # Process files from both processing/vlm_out and movess directories
        for filepath in vlmOutputDir.iterdir():
            if filepath.is_file():
                compare_payment(filepath, "databases/codes_base_proj1.json")
                
                # Move processed file to processing/post_comparison directory
                dest_path = postComparisonDir / filepath.name
                import shutil
                shutil.move(str(filepath), str(dest_path))
                print(f"Moved {filepath} to {dest_path}")
    except custom_errors.EmptyDocumentError:
        print("No valid claims can be detected within the document.")
    #except Exception as e:
       # print("An error occurred during processing")
       # print(e)
'''
try:            
    main("sensitive/EOB/page-25.png")
except custom_errors.EmptyDocumentError:
    print("No valid claims can be detected within the document.")
'''

#Check errors in main() most are gonna get in the way now