'''import fitz'''
import ollama
import base64
import time
import prompts_list
import cv2
import parse_vlm_output as pvo
import prompt_fixes

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


def ask_vlm(image_path, prompt):
    if not prompt:
        raise ValueError("Missing prompt for VLM input")
    elif not image_path:
        raise ValueError("Missing image for VLM input")
    
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

    end_time = time.perf_counter()
    total_ollama_time = end_time - ollama_start

    if len(pvo.parse_vlm_output(result)) > 3:
        raise ValueError("Too many tables")

    return response["message"]["content"], total_ollama_time



image = 'sensitive/EOB/page-34.png'

blackout = black_out_column(image, 1885, 2070)
cv2.imwrite("sensitive/EOB/blackout.png", blackout)

#quit()

retry = 0
try:
    result, time_taken = ask_vlm("sensitive/EOB/blackout.png", prompts_list.message_2_united)
except ValueError("Too many tables"):
    retry += 1
    if retry ==3:
        raise ValueError("Too many retries")
    
    print("Too many tables. retrying...")
    result, time_taken = ask_vlm("sensitive/EOB/blackout.png", (prompts_list.message_2_united + prompt_fixes.too_many_tables_united))


print(result)
print(f"Time Taken: {time_taken:.2f} seconds.")
