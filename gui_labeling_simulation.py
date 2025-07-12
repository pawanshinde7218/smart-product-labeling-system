import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import qrcode
import easyocr
import csv
from datetime import datetime
import os

# -----------------------
# 1. Load active batch ID
# -----------------------
def get_active_batch():
    try:
        with open("active_batch.txt", "r") as f:
            return f.read().strip().upper()
    except FileNotFoundError:
        messagebox.showerror("Error", "File 'active_batch.txt' not found.")
        exit()

# -----------------------
# 2. Generate Smart Device ID
# -----------------------
def generate_device_id(model_code, batch_id):
    filename = "batch_serials.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
    else:
        data = {}

    serial = data.get(batch_id, 0) + 1
    data[batch_id] = serial

    with open(filename, "w") as f:
        json.dump(data, f)

    return f"{model_code}-{batch_id}-{serial:03d}"

# -----------------------
# 3. Generate Label with QR Code
# -----------------------
def generate_label(device_id, batch_id, date, rohs):
    img = Image.new('RGB', (600, 300), color='white')
    d = ImageDraw.Draw(img)

    d.text((10, 20), f"Device ID: {device_id}", fill='black')
    d.text((10, 70), f"Batch ID: {batch_id}", fill='black')
    d.text((10, 120), f"Date: {date}", fill='black')
    d.text((10, 170), f"RoHS: {rohs}", fill='black')

    qr_data = f"Device ID: {device_id} | Batch ID: {batch_id} | Date: {date} | RoHS: {rohs}"
    print("📦 QR Content:", qr_data)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((180, 180))

    img.paste(qr_img, (400, 60))
    img.save("label_qr.png")

# -----------------------
# 4. OCR & Verification
# -----------------------
def ocr_label():
    reader = easyocr.Reader(['en'])
    result = reader.readtext('label_qr.png')
    extracted = [line[1] for line in result]
    print("🔍 OCR Output:")
    for line in extracted:
        print(" -", line)
    return extracted

def normalize(text):
    return text.upper().replace("I", "1").replace("O", "0").replace(" ", "").replace(":", "").strip()

def verify_label(expected, extracted):
    status = "PASS"
    for key in expected:
        expected_full = normalize(f"{key}: {expected[key]}")
        match_found = False
        for line in extracted:
            if expected_full in normalize(line):
                match_found = True
                break
        if not match_found:
            print(f"❌ Mismatch in {key}")
            status = "REJECT"
    return status

# -----------------------
# 5. Log Result to CSV
# -----------------------
def log_to_csv(device_id, batch_id, date, rohs, status):
    filename = "traceability_log.csv"
    try:
        with open(filename, "a", newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now(), device_id, batch_id, date, rohs, status])
        print(f"📄 Logged: {device_id} - {status}")
    except PermissionError:
        print("⚠️ ERROR: Close 'traceability_log.csv' and rerun.")

# -----------------------
# 6. Toggle GUI Lights
# -----------------------
def set_light(label_widget, color, reset_after=5000):
    label_widget.config(bg=color)
    root.after(reset_after, lambda: label_widget.config(bg="gray"))

# -----------------------
# 7. Simulate Detection
# -----------------------
def simulate_detection():
    model_code = "T100X"
    batch_id = get_active_batch()
    date = "02-07-2025"
    rohs = "YES"

    device_id = generate_device_id(model_code, batch_id)
    generate_label(device_id, batch_id, date, rohs)

    expected = {
        "Device ID": device_id,
        "Batch ID": batch_id,
        "Date": date,
        "RoHS": rohs
    }

    extracted = ocr_label()
    status = verify_label(expected, extracted)
    log_to_csv(device_id, batch_id, date, rohs, status)

    try:
        img = Image.open("label_qr.png")
        img.show()
    except Exception as e:
        print("⚠️ Image view error:", e)

    if status == "PASS":
        set_light(printer_light, "green")
    else:
        set_light(reject_light, "red")

    messagebox.showinfo("Result", f"Label Created: {device_id}\nStatus: {status}")

# -----------------------
# 8. GUI Setup
# -----------------------
root = tk.Tk()
root.title("Smart Labeling System with Lights")
root.geometry("400x300")

title_label = tk.Label(root, text="Smart Product Labeling System", font=("Arial", 14))
title_label.pack(pady=10)

detect_button = tk.Button(
    root,
    text="🟢 Simulate Product Detection",
    font=("Arial", 12),
    bg="green",
    fg="white",
    command=simulate_detection
)
detect_button.pack(pady=10)

# 🔵 Light indicators
printer_light = tk.Label(root, text="Label Printer", bg="gray", fg="white", width=20)
printer_light.pack(pady=5)

reject_light = tk.Label(root, text="Reject Bin", bg="gray", fg="white", width=20)
reject_light.pack(pady=5)

root.mainloop()
