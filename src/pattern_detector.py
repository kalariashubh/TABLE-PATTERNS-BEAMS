import json
from pdf_to_images import convert_pdf_to_images
from vision_extractor import extract_from_image


def detect_pattern(pdf_path, temp_folder):

    image_paths = convert_pdf_to_images(pdf_path, temp_folder)

    if not image_paths:
        raise Exception("No image generated for detection.")

    first_image = image_paths[0]

    classification_prompt = """
You are an expert at identifying RCC beam schedule HEADER patterns.

IMPORTANT:
You must look ONLY at the HEADER structure.
Ignore all reinforcement values.
Ignore numbers.
Ignore row content.
Focus ONLY on column names.

There are EXACTLY 8 patterns.
Return ONLY one number from 1 to 8.
No explanation.
No extra text.
Only the number.

========================================================
PATTERN 1
========================================================
Header contains:
- BEAM
- SIZE (WIDTH, DEPTH)
- TOP REINFORCEMENT (LEFT, MID SPAN, RIGHT)
- BOTTOM REINFORCEMENT (LEFT, MID SPAN, RIGHT)
- STIRRUPS 9 (LEFT, MID SPAN, RIGHT)

Simple table structure.
No Bottom (Curtail).
No Extra Over Support columns.

========================================================
PATTERN 2
========================================================
Header contains:
- BEAM MARKED
- SIZE (B x D/d)   ← MUST contain "/d"
- Bottom (Straight)
- Bottom (Curtail)
- Top (Straight)
- Ex. Top (Straight)
- Top (Extra Over Support) Left
- Top (Extra Over Support) Right
- Stirrups (Upto L/4)
- Stirrups (Rest)

CRITICAL IDENTIFIER:
SIZE column contains "/d"

If "/d" exists in size → RETURN 2

========================================================
PATTERN 3
========================================================
Header contains:
- Beam Marked
- Size (B x D)     ← MUST NOT contain "/d"
- Bottom (Straight)
- Bottom (Curtail)
- Top (Straight)
- Top (Extra Over Support - Left)
- Top (Extra Over Support - Right)
- Stirrups (Upto L/4)
- Stirrups (Rest)

CRITICAL IDENTIFIER:
SIZE column does NOT contain "/d"

If NO "/d" and above header exists → RETURN 3

========================================================
PATTERN 4
========================================================
Header contains:
- BEAM
- WIDTH
- DEPTH
- CLEAR SPAN (L)
- A
- B
- C
- D1(mm)
- G
- E
- D2(mm)
- S1

Unique identifiers:
Columns A, B, C
Columns G, E
Columns D1(mm), D2(mm)
Column S1

========================================================
PATTERN 5
========================================================
Header contains:
- BEAM
- ELEVATION
- TYPE
- SIZE - WIDTH (W)
- SIZE - DEPTH (D)
- CLEAR SPAN (L)
- TOP REINF. - A
- BOTTOM REINF. - B
- STIRRUPS

Special identifier:
Multiple beam IDs stacked vertically inside SAME beam cell.

========================================================
PATTERN 6
========================================================
Header contains:
- BEAM NO
- B
- D

BOTTOM REINFORCEMENT:
    - LEFT SUPPORT (Layer 1)
    - MID SPAN (Layer 1)
    - MID SPAN (Layer 2)
    - RIGHT SUPPORT (Layer 1)

TOP REINFORCEMENT:
    - LEFT SUPPORT (Layer 1)
    - LEFT SUPPORT (Layer 2)
    - MID SPAN (Layer 1)
    - RIGHT SUPPORT (Layer 1)
    - RIGHT SUPPORT (Layer 2)

STIRRUPS:
- NO OF LEGS
- DIA
- LEFT SUPPORT SPACING
- MID SPACING
- RIGHT SUPPORT SPACING

========================================================
PATTERN 7
========================================================
Header contains:
- BEAM NO
- B
- D
- LAYER 1
- LAYER 2
- LEFT SUPPORT
- MID SPAN
- RIGHT SUPPORT
- NO OF LEGS
- DIA

Layered support type reinforcement layout.

========================================================
PATTERN 8
========================================================
NOT A TABLE.

Strip beam detail drawing.

Contains:
- Beam segments like CB1a, CB1b, CB1c
- Size written in brackets like (300x600)
- Reinforcement written ABOVE each beam segment
- No tabular grid header

========================================================

FINAL DECISION PRIORITY:

1) If you see "/d" inside size column → RETURN 2
2) If you see "B x D" and NO "/d" → RETURN 3
3) Otherwise match full header structure carefully.

Return ONLY the number.
"""

    result = extract_from_image(first_image, classification_prompt)
    result = result.strip()

    if not result.isdigit():
        raise Exception(f"Pattern detection failed. Model returned: {result}")

    return int(result)
