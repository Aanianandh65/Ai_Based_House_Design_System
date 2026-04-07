from flask import Flask, render_template, request
import json
import google.generativeai as genai
import random
import cv2
import numpy as np
import os

app = Flask(__name__)

# CONFIG
genai.configure(api_key="AIzaSyCgM3x4l1_5Sm0Rlj11i03tkbJdtWxLWfQ")
model = genai.GenerativeModel("gemini-1.5-flash")

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# AI TEXT FUNCTION
def get_ai_suggestion(bedrooms, style, sqft, plot_type):
    try:
        prompt = f"""
        You are an expert architect.

        Design a house with:
        - {bedrooms} bedrooms
        - {style} style
        - {sqft} sqft
        - {plot_type} plot

        Give:
        1. Layout Plan
        2. Key Features
        3. Design Tips

        Keep it practical and clear.
        """

        response = model.generate_content(prompt)
        return response.text

    except:
        return f"""
        Layout Plan:
        - Living room at front, bedrooms at rear

        Key Features:
        - Cross ventilation, natural lighting

        Design Tips:
        - Optimize space for {sqft} sqft
        """


# IMAGE DETECTION + DRAWING
def detect_plot_shape(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "unknown", 0, None

        original = img.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        edges = cv2.Canny(blur, 50, 150)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return "unknown", 0, None

        largest = max(contours, key=cv2.contourArea)

        approx = cv2.approxPolyDP(largest, 0.02 * cv2.arcLength(largest, True), True)

        sides = len(approx)

        #DRAW SHAPE
        cv2.drawContours(original, [approx], -1, (0, 255, 0), 3)

        # SAVE PROCESSED IMAGE
        filename = os.path.basename(image_path)
        output_path = os.path.join(UPLOAD_FOLDER, "processed_" + filename)
        cv2.imwrite(output_path, original)

        # CLASSIFY
        if sides == 4:
            return "regular", 0.8, output_path
        elif 5 <= sides <= 8:
            return "irregular", 0.6, output_path
        else:
            return "unknown", 0.3, output_path

    except Exception as e:
        print("Detection Error:", e)
        return "unknown", 0, None


# ROUTES
@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/form')
def form():
    return render_template('index.html')


# RESULT
@app.route('/result', methods=['POST'])
def result():

    # FORM DATA
    bedrooms = int(request.form.get('bedrooms'))
    style = request.form.get('style')
    length = float(request.form.get('length'))
    width = float(request.form.get('width'))
    manual_plot = request.form.get('plot_type')

    sqft = length * width

    # IMAGE UPLOAD
    file = request.files.get('plot_image')

    detected_plot = "unknown"
    confidence = 0
    detection_used = False
    processed_image = None  

    if file and file.filename != "":
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        detected_plot, confidence, processed_image = detect_plot_shape(filepath)

    # DECISION LOGIC
    if detected_plot != "unknown" and confidence >= 0.6:
        plot_type = detected_plot
        detection_used = True
    else:
        plot_type = manual_plot
        detection_used = False

# CLEAN IMAGE PATH FOR HTML 
    if processed_image:
      processed_image = processed_image.split("static/")[-1]
      processed_image = processed_image.replace("\\", "/")   
    # LOAD DESIGNS
    with open('designs.json') as f:
        designs = json.load(f)
        
    print("FINAL IMAGE PATH:", processed_image)

    matched_designs = []

    # MATCHING LOGIC
    for design in designs:
        score = 0

        if design["bedrooms"] == bedrooms:
            score += 3
        if design["style"] == style:
            score += 2
        if design["plot_type"] == plot_type:
            score += 2
        if design["sqft_min"] <= sqft <= design["sqft_max"]:
            score += 3

        score += random.randint(0, 1)

        design["score"] = score
        matched_designs.append(design)

    # SORT + RANDOM PICK
    matched_designs = sorted(matched_designs, key=lambda x: x["score"], reverse=True)
    top_designs = matched_designs[:6]
    matched_designs = random.sample(top_designs, min(3, len(top_designs)))

    #AI TEXT
    ai_text = get_ai_suggestion(bedrooms, style, sqft, plot_type)

    return render_template(
        'result.html',
        designs=matched_designs,
        sqft=sqft,
        ai_text=ai_text,
        detected_plot=detected_plot,
        confidence=confidence,
        detection_used=detection_used,
        processed_image=processed_image
    )


if __name__ == '__main__':
    app.run()