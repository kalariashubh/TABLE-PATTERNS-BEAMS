import os
import json
import re
from tqdm import tqdm

from config import INPUT_DIR, OUTPUT_DIR
from pdf_to_images import convert_pdf_to_images
from vision_extractor import extract_from_image


def load_prompt():
    with open(os.path.join(os.path.dirname(__file__), "prompt.txt"), "r") as f:
        return f.read()


def is_valid_beam_id(beam_id):
    if not beam_id:
        return False
    return any(c.isalpha() for c in beam_id)


# ----------------------------
# Reinforcement Normalization
# ----------------------------

def normalize_reinforcement(value):
    if not value:
        return []

    parts = re.split(r"\+", value)

    cleaned = []

    for part in parts:
        part = part.strip()

        # Replace Y and #
        part = part.replace("Y", "T")
        part = part.replace("#", "T")

        # Remove bar mark suffix
        part = re.sub(r"-A[0-9a-zA-Z]+", "", part)

        # Standardize format
        match = re.search(r"(\d+)\s*[-]?\s*T(\d+)", part)
        if match:
            qty = match.group(1)
            dia = match.group(2)
            cleaned.append(f"{qty}-T{dia}")

    return cleaned


# ----------------------------
# Stirrups Cleaning
# ----------------------------

def clean_stirrups(dia_list, spacing_list):
    clean_dia = set()
    clean_spacing = set()

    for d in dia_list:
        if not d:
            continue

        d = d.replace("Y", "T")
        d = d.replace("#", "T")
        d = d.replace("@", "")
        d = d.replace("±", "")
        d = d.strip()

        clean_dia.add(d)

    for s in spacing_list:
        if not s:
            continue

        s = s.replace("@", "")
        s = s.replace("±", "")
        s = s.replace("/", "")
        s = s.strip()

        match = re.search(r"\d+", s)
        if match:
            spacing = match.group(0) + " C/C"
            if spacing != "0 C/C":
                clean_spacing.add(spacing)

    return list(clean_dia), list(clean_spacing)


# ----------------------------
# Main Processing
# ----------------------------

def process_pdf(pdf_path):
    file_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_folder = os.path.join(OUTPUT_DIR, file_name)

    os.makedirs(output_folder, exist_ok=True)

    image_paths = convert_pdf_to_images(pdf_path, output_folder)
    prompt = load_prompt()

    all_beams = []

    for img_path in tqdm(image_paths):
        result = extract_from_image(img_path, prompt)

        try:
            parsed = json.loads(result)

            if "beams" in parsed:
                for beam in parsed["beams"]:
                    if is_valid_beam_id(beam.get("beam_id")):
                        all_beams.append(beam)

        except:
            print("⚠ JSON parse error")

    merged = {}

    for beam in all_beams:
        beam_id = beam["beam_id"]

        if beam_id not in merged:
            merged[beam_id] = beam
        else:
            merged[beam_id]["reinforcement"] += beam["reinforcement"]
            merged[beam_id]["stirrups"]["dia"] += beam["stirrups"]["dia"]
            merged[beam_id]["stirrups"]["spacing"] += beam["stirrups"]["spacing"]

    # Final normalization
    for beam in merged.values():

        # Reinforcement normalization
        normalized = []
        for r in beam["reinforcement"]:
            normalized += normalize_reinforcement(r)

        beam["reinforcement"] = sorted(list(set(normalized)))

        # Stirrups normalization
        dia, spacing = clean_stirrups(
            beam["stirrups"]["dia"],
            beam["stirrups"]["spacing"]
        )

        beam["stirrups"]["dia"] = sorted(dia)
        beam["stirrups"]["spacing"] = sorted(spacing)

    final_output = {"beams": list(merged.values())}

    output_file = os.path.join(output_folder, f"{file_name}.json")

    with open(output_file, "w") as f:
        json.dump(final_output, f, indent=2)

    print(f"✅ Saved: {output_file}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for file in os.listdir(INPUT_DIR):
        if file.lower().endswith(".pdf"):
            process_pdf(os.path.join(INPUT_DIR, file))


if __name__ == "__main__":
    main()
