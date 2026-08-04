import cv2
import pytesseract
import numpy as np
import os


def save_intermediate(image, name, input_path):
    """
    Save an intermediate preprocessing step to sensitive/ directory.
    Uses the input filename to create a unique output name.
    """
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = f"sensitive/{base_name}_{name}.png"
    cv2.imwrite(output_path, image)
    return output_path


def preprocess_for_dark_background(image, input_path=None):
    """
    Preprocess image for black text on dark gray background.
    Uses adaptive thresholding with inverted binary to preserve text visibility.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Use adaptive thresholding for better handling of dark backgrounds
    # This preserves dark text on dark gray backgrounds
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    
    return adaptive


def find_patient_resp_stacked(image_path, output_path=None):
    """
    Find where a document says "patient resp" (stacked vertically, all caps)
    and black out a rectangle as big as the box for the words below it.
    
    Args:
        image_path: Path to the input image/PDF
        output_path: Path to save the output image (optional)
    
    Returns:
        Tuple of (output_image_path, bounding_box_coordinates)
    """
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Preprocess for dark background
    processed = preprocess_for_dark_background(image, image_path)
    
    # Save intermediate steps
    save_intermediate(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), "gray", image_path)
    save_intermediate(processed, "preprocessed", image_path)
    
    # Get OCR data with bounding boxes - use PSM 6 for uniform block of text
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(processed, config=custom_config, output_type=pytesseract.Output.DICT)
    
    n_boxes = len(data['text'])
    
    # Find "patient" and "resp" stacked vertically
    patient_boxes = []
    resp_boxes = []
    
    for i in range(n_boxes):
        text = data['text'][i].strip()
        
        # Look for "PATIENT" (all caps)
        if text.upper() == 'PATIENT':
            patient_boxes.append({
                'index': i,
                'x': data['left'][i],
                'y': data['top'][i],
                'w': data['width'][i],
                'h': data['height'][i]
            })
        
        # Look for "RESP" (all caps)
        elif text.upper() == 'RESP':
            resp_boxes.append({
                'index': i,
                'x': data['left'][i],
                'y': data['top'][i],
                'w': data['width'][i],
                'h': data['height'][i]
            })
    
    # Check if we found stacked text
    patient_resp_box = None
    for pbox in patient_boxes:
        for rbox in resp_boxes:
            # Check if resp is directly below patient (stacked vertically)
            # resp should be within one line height below patient
            resp_below_patient = pbox['y'] + pbox['h'] <= rbox['y'] <= pbox['y'] + pbox['h'] * 2
            
            # Check if they're roughly aligned horizontally
            aligned = abs((pbox['x'] + pbox['w'] // 2) - (rbox['x'] + rbox['w'] // 2)) < pbox['w'] * 0.5
            
            if resp_below_patient and aligned:
                # Combine into one box for "patient resp"
                patient_resp_box = {
                    'x': min(pbox['x'], rbox['x']),
                    'y': pbox['y'],
                    'w': max(pbox['x'] + pbox['w'], rbox['x'] + rbox['w']) - min(pbox['x'], rbox['x']),
                    'h': rbox['y'] + rbox['h'] - pbox['y']
                }
                break
        if patient_resp_box:
            break
    
    if patient_resp_box is None:
        print("Warning: Could not find 'patient resp' text in image")
        return image_path, None
    
    # Find the box below "patient resp"
    min_y_threshold = patient_resp_box['y'] + patient_resp_box['h']
    max_y_threshold = min_y_threshold + (patient_resp_box['h'] * 4)  # Look within 4 lines below
    
    candidates = []
    for i in range(n_boxes):
        box_y = data['top'][i]
        box_h = data['height'][i]
        text = data['text'][i].strip()
        
        # Check if this box is below patient resp and within reasonable range
        if min_y_threshold <= box_y <= max_y_threshold:
            # Only consider boxes with actual content
            if text and len(text) > 0:
                candidates.append({
                    'index': i,
                    'x': data['left'][i],
                    'y': data['top'][i],
                    'w': data['width'][i],
                    'h': data['height'][i],
                    'text': text
                })
    
    below_box = None
    if candidates:
        # Find the leftmost and rightmost boxes to get full width
        min_x = min(c['x'] for c in candidates)
        max_right = max(c['x'] + c['w'] for c in candidates)
        max_y = max(c['y'] + c['h'] for c in candidates)
        
        below_box = {
            'x': min_x,
            'y': patient_resp_box['y'] + patient_resp_box['h'],
            'w': max_right - min_x,
            'h': max_y - (patient_resp_box['y'] + patient_resp_box['h'])
        }
    
    if below_box is None:
        print("Warning: Could not find box below 'patient resp'")
        return image_path, None
    
    # Create a copy of the image for processing
    output_image = image.copy()
    
    # Black out the rectangle below "patient resp"
    x, y, w, h = below_box['x'], below_box['y'], below_box['w'], below_box['h']
    
    # Add padding to make sure we cover the entire box
    padding = 3
    x = max(0, x - padding)
    y = max(0, y - padding)
    w = min(output_image.shape[1] - x, w + padding * 2)
    h = min(output_image.shape[0] - y, h + padding * 2)
    
    # Draw black rectangle
    cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 0, 0), -1)
    
    # Optionally save the output image
    if output_path is None:
        # Create output path based on input
        if image_path.lower().endswith('.pdf'):
            output_path = image_path.replace('.pdf', '_processed.png')
        else:
            output_path = image_path.replace('.', '_processed.')
    
    cv2.imwrite(output_path, output_image)
    
    return output_path, below_box


if __name__ == "__main__":
    import sys
    
    image_path = "sensitive/EOB/page-35.png"
    output_path = "sensitive/EOB/blackbox.png"
    
    try:
        result_path, box = find_patient_resp_stacked(image_path, output_path)
        print(f"Output saved to: {result_path}")
        if box:
            print(f"Blacked out box coordinates: {box}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)