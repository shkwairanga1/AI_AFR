#!/usr/bin/env python3
"""
PubMed Extractor — Nigeria Neuroscience + AI
Email: sk987@sussex.ac.uk
Repo:  https://github.com/shkwairanga1/AI_AFR
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import csv
import json
import time
import sys
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

SEARCH_TERM = (
    "((Neuroscience OR brain OR nervous system OR neurological "
    "OR spinal cord OR neuro) AND "
    "(Artificial Intelligence OR Machine Learning OR Deep Learning "
    "OR Neural Network) AND Nigeria)"
)
MAX_RESULTS = 500
OUTPUT_FILE = "nigeria_neuro_ai.csv"
BATCH_SIZE  = 100
BASE_URL    = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EMAIL       = "sk987@sussex.ac.uk"

def search_pubmed(term, retmax=500):
    print(f"[1/3] Searching PubMed for up to {retmax} records...")
    params = urllib.parse.urlencode({
        "db": "pubmed", "term": term, "retmax": retmax,
        "retmode": "json", "tool": "nigeria_neuro_ai_extractor", "email": EMAIL
    })
    with urllib.request.urlopen(BASE_URL + "esearch.fcgi?" + params) as r:
        data = json.load(r)
    ids   = data["esearchresult"]["idlist"]
    total = data["esearchresult"]["count"]
    print(f"    Found {total} total. Retrieving {len(ids)}.")
    return ids

def fetch_records(pmids, batch_size=100):
    print(f"[2/3] Fetching full records in batches of {batch_size}...")
    all_articles = []
    for i in range(0, len(pmids), batch_size):
        batch  = pmids[i:i+batch_size]
        params = urllib.parse.urlencode({
            "db": "pubmed", "id": ",".join(batch),
            "rettype": "xml", "retmode": "xml",
            "tool": "nigeria_neuro_ai_extractor", "email": EMAIL
        })
        print(f"    Batch {i//batch_size+1}: records {i+1}–{min(i+batch_size,len(pmids))}")
        with urllib.request.urlopen(BASE_URL + "efetch.fcgi?" + params) as r:
            root = ET.fromstring(r.read())
        all_articles.extend(root.findall(".//PubmedArticle"))
        time.sleep(0.4)
    print(f"    Total articles retrieved: {len(all_articles)}")
    return all_articles

def get_text(element, path, default=""):
    node = element.find(path)
    return (node.text or "").strip() if node is not None else default

def parse_article(article):
    medline = article.find("MedlineCitation")
    art     = medline.find("Article") if medline is not None else None
    if art is None:
        return None

    pmid  = get_text(medline, "PMID")
    title = get_text(art, "ArticleTitle")

    abstract_parts = []
    abstract_node  = art.find("Abstract")
    if abstract_node is not None:
        for ab in abstract_node.findall("AbstractText"):
            label = ab.get("Label", "")
            text  = (ab.text or "").strip()
            if label:
                abstract_parts.append(f"{label}: {text}")
            elif text:
                abstract_parts.append(text)
    abstract = " | ".join(abstract_parts)

    pub_date = art.find(".//PubDate")
    year = ""
    if pub_date is not None:
        year = get_text(pub_date, "Year") or get_text(pub_date, "MedlineDate")[:4]

    journal      = get_text(art, "Journal/Title")
    journal_abbr = get_text(art, "Journal/ISOAbbreviation")
    pub_types    = [pt.text.strip() for pt in art.findall("PublicationTypeList/PublicationType") if pt.text]
    article_type = "; ".join(pub_types)

    authors, affiliations = [], []
    for author in art.findall("AuthorList/Author"):
        last  = get_text(author, "LastName")
        first = get_text(author, "ForeName")
        if last:
            authors.append(f"{last} {first}".strip())
        for aff in author.findall("AffiliationInfo/Affiliation"):
            if aff.text and aff.text.strip() not in affiliations:
                affiliations.append(aff.text.strip())

    mesh_terms = [
        mh.find("DescriptorName").text.strip()
        for mh in (medline.findall("MeshHeadingList/MeshHeading") or [])
        if mh.find("DescriptorName") is not None
    ]

    doi, pmcid = "", ""
    id_list = article.find("PubmedData/ArticleIdList")
    if id_list is not None:
        for aid in id_list.findall("ArticleId"):
            if aid.get("IdType") == "doi":
                doi = (aid.text or "").strip()
            elif aid.get("IdType") == "pmc":
                pmcid = (aid.text or "").strip()

    grants = []
    for grant in medline.findall(".//GrantList/Grant"):
        entry = " | ".join(filter(None, [get_text(grant,"GrantID"), get_text(grant,"Agency"), get_text(grant,"Country")]))
        if entry:
            grants.append(entry)

    keywords = [kw.text.strip() for kw in medline.findall(".//KeywordList/Keyword") if kw.text]

    ai_keywords = ["CNN","LSTM","RNN","SVM","Random Forest","XGBoost","Transformer",
                   "BERT","deep learning","machine learning","neural network",
                   "convolutional","reinforcement learning","federated learning",
                   "natural language processing","NLP","decision tree","logistic regression",
                   "k-nearest","naive bayes","GAN","autoencoder","ResNet","VGG","YOLO"]
    found_ai = [kw for kw in ai_keywords if kw.lower() in (title + " " + abstract).lower()]

    return {
        "PMID":                      pmid,
        "Title":                     title,
        "Abstract":                  abstract,
        "Year":                      year,
        "Journal":                   journal,
        "Journal_Abbrev":            journal_abbr,
        "Article_Type":              article_type,
        "Authors":                   "; ".join(authors),
        "Affiliations":              " || ".join(affiliations),
        "MeSH_Terms":                "; ".join(mesh_terms),
        "Keywords":                  "; ".join(keywords),
        "DOI":                       doi,
        "PMCID":                     pmcid,
        "Funding":                   "; ".join(grants),
        "AI_Technique_AutoDetected": "; ".join(found_ai),
        "African_Country":           "",
        "African_Region":            "",
        "Lead_Author_African_YN":    "",
        "International_Collab":      "",
        "Study_Population_Location": "",
        "Neurological_Condition":    "",
        "Neuro_Subdiscipline":       "",
        "Study_Setting":             "",
        "Data_Type_Used":            "",
        "Sample_Size_N":             "",
        "AI_Category":               "",
        "AI_Task_Type":              "",
        "Model_Performance_Metric":  "",
        "Open_Source_Code_YN":       "",
        "Pretrained_Model_YN":       "",
        "AI_Maturity_Level_1to5":    "",
        "Research_Stage":            "",
        "External_Validation_YN":    "",
        "Locally_Developed_AI_YN":   "",
        "Compute_Infrastructure":    "",
        "Dataset_Origin":            "",
        "African_Led_Funding_YN":    "",
        "Ethics_Approval_YN":        "",
        "Data_Privacy_Governance":   "",
        "Barriers_Reported":         "",
        "Opportunities_Stated":      "",
        "Clinical_Applicability":    "",
        "Reviewer_Notes":            "",
    }

def write_csv(records, filename):
    if not records:
        print("No records to write.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    print(f"[3/3] Saved {len(records)} records → {filename}")

if __name__ == "__main__":
    pmids    = search_pubmed(SEARCH_TERM, MAX_RESULTS)
    if not pmids:
        print("No results found.")
        sys.exit(1)
    articles = fetch_records(pmids, BATCH_SIZE)
    records  = [r for a in articles if (r := parse_article(a)) is not None]
    write_csv(records, OUTPUT_FILE)
    print(f"\nDone! Open 'nigeria_neuro_ai.csv' in Excel or Google Sheets.")
