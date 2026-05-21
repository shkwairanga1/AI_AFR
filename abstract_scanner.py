#!/usr/bin/env python3
"""
Abstract Scanner — Auto-fills Neurological_Condition, Data_Type_Used, Sample_Size_N
Reads nigeria_neuro_ai.csv, scans Title + Abstract, saves updated CSV.
"""

import csv
import re

INPUT_FILE  = "nigeria_neuro_ai.csv"
OUTPUT_FILE = "nigeria_neuro_ai.csv"

# ── NEUROLOGICAL CONDITIONS ───────────────────────────────────────────────────
NEURO_CONDITIONS = {
    "Epilepsy":               ["epilep", "seizure"],
    "Stroke":                 ["stroke", "cerebrovascular", "ischaemic", "ischemic infarct"],
    "Dementia":               ["dementia", "alzheimer", "cognitive decline", "cognitive impairment"],
    "Parkinson's Disease":    ["parkinson"],
    "Multiple Sclerosis":     ["multiple sclerosis", " ms "],
    "Brain Tumour":           ["glioma", "glioblastoma", "brain tumor", "brain tumour", "meningioma"],
    "Traumatic Brain Injury": ["traumatic brain", " tbi "],
    "Spinal Cord Injury":     ["spinal cord injury", " sci "],
    "Neuropathy":             ["neuropath", "peripheral nerve"],
    "Psychiatric/Mental":     ["schizophrenia", "depression", "anxiety", "bipolar", "psychiatric", "mental health"],
    "HIV Neurology":          ["hiv", "neuroaids", "aids dementia"],
    "Malaria Neurology":      ["cerebral malaria", "neuromalaria"],
    "Headache/Migraine":      ["migraine", "headache"],
    "Sleep Disorders":        ["sleep", "insomnia", "narcolepsy"],
    "Autism/Neurodevelopment":["autism", "asd", "neurodevelopment", "adhd"],
    "Pain":                   ["neuropathic pain", "chronic pain"],
    "EEG/Brain Signals":      ["eeg", "electroencephalog", "brain signal", "brainwave"],
    "General Neuroscience":   ["neuroscience", "neural", "neuron", "brain imaging"],
}

# ── DATA TYPES ────────────────────────────────────────────────────────────────
DATA_TYPES = {
    "MRI":              ["mri", "magnetic resonance imaging", "fmri", "functional mri", "dti", "diffusion tensor"],
    "CT Scan":          ["ct scan", "computed tomography", " ct "],
    "EEG":              ["eeg", "electroencephalog"],
    "EMG":              ["emg", "electromyog"],
    "Clinical Records": ["electronic health record", "ehr", "clinical record", "medical record", "patient record", "hospital record"],
    "Genomics/Genetics":["genomic", "genetic", "dna", "rna", "snp", "genome"],
    "Text/NLP":         ["text mining", "natural language", "nlp", "clinical notes", "pubmed"],
    "Neuroimaging":     ["neuroimaging", "brain image", "brain scan"],
    "Wearable/Sensor":  ["wearable", "accelerometer", "sensor", "iot"],
    "Blood/Biomarker":  ["biomarker", "blood sample", "serum", "plasma", "csf"],
    "Survey/Questionnaire": ["questionnaire", "survey", "interview", "scale"],
    "Video/Image":      ["video", "fundus", "retinal", "optical"],
}

# ── SAMPLE SIZE ───────────────────────────────────────────────────────────────
SAMPLE_PATTERNS = [
    r'\b([nN]\s*=\s*(\d[\d,]*))',
    r'\b(\d[\d,]*)\s+patients?\b',
    r'\b(\d[\d,]*)\s+participants?\b',
    r'\b(\d[\d,]*)\s+subjects?\b',
    r'\b(\d[\d,]*)\s+individuals?\b',
    r'\b(\d[\d,]*)\s+cases?\b',
    r'\btotal\s+of\s+(\d[\d,]*)\b',
    r'\bsample\s+of\s+(\d[\d,]*)\b',
    r'\benrolled\s+(\d[\d,]*)\b',
    r'\bincluded\s+(\d[\d,]*)\b',
    r'\bcomprised?\s+(\d[\d,]*)\b',
    r'\brecruited\s+(\d[\d,]*)\b',
]

def scan_conditions(text):
    text_lower = text.lower()
    found = []
    for condition, keywords in NEURO_CONDITIONS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(condition)
    return "; ".join(found) if found else "Unspecified"

def scan_data_types(text):
    text_lower = text.lower()
    found = []
    for dtype, keywords in DATA_TYPES.items():
        if any(kw in text_lower for kw in keywords):
            found.append(dtype)
    return "; ".join(found) if found else "Unspecified"

def scan_sample_size(text):
    text = text.replace(",", "")
    for pattern in SAMPLE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            nums = re.findall(r'\d+', match.group())
            if nums:
                n = int(nums[-1])
                if 2 <= n <= 1000000:
                    return str(n)
    return ""

def main():
    print("[1/3] Reading CSV...")
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"    Loaded {len(rows)} records.")

    print("[2/3] Scanning abstracts...")
    filled_condition, filled_dtype, filled_n = 0, 0, 0

    for row in rows:
        text = (row.get("Title", "") + " " + row.get("Abstract", ""))

        # Only fill if empty
        if not row.get("Neurological_Condition", "").strip():
            row["Neurological_Condition"] = scan_conditions(text)
            filled_condition += 1

        if not row.get("Data_Type_Used", "").strip():
            row["Data_Type_Used"] = scan_data_types(text)
            filled_dtype += 1

        if not row.get("Sample_Size_N", "").strip():
            result = scan_sample_size(text)
            row["Sample_Size_N"] = result
            if result:
                filled_n += 1

    print(f"    Neurological_Condition filled : {filled_condition}")
    print(f"    Data_Type_Used filled         : {filled_dtype}")
    print(f"    Sample_Size_N filled          : {filled_n}/{len(rows)}")

    print("[3/3] Saving CSV...")
    fieldnames = list(rows[0].keys())
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! CSV updated → {OUTPUT_FILE}")

    # ── Summary ───────────────────────────────────────────────────────────────
    from collections import Counter
    cond_counts = Counter()
    for row in rows:
        for c in row.get("Neurological_Condition","").split("; "):
            if c: cond_counts[c] += 1

    print("\n  Top 10 neurological conditions detected:")
    for cond, count in cond_counts.most_common(10):
        print(f"    {count:>3}x  {cond}")

    dtype_counts = Counter()
    for row in rows:
        for d in row.get("Data_Type_Used","").split("; "):
            if d: dtype_counts[d] += 1

    print("\n  Data types detected:")
    for dtype, count in dtype_counts.most_common():
        print(f"    {count:>3}x  {dtype}")

if __name__ == "__main__":
    main()
