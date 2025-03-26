# importing required modules 
from PyPDF2 import PdfReader 
from openai import AzureOpenAI
from flask import Flask, request, jsonify
import requests
import pdfplumber
import io
import re
import csv
import pandas as pd

csv_path = r"C:\Users\sachi\Downloads\hackathon\input_data.csv"


# Sample DataFrame with extracted rules from PDF
pdf_rules = pd.DataFrame([
    {"Field Name": "Customer ID", "MDRM": "CLCOM047", 
     "Allowable Values": "Must not contain a carriage return, line feed, comma or any unprintable character."},

    {"Field Name": "Internal ID", "MDRM": "CLCOM300", 
     "Allowable Values": "Must not contain a carriage return, line feed, comma or any unprintable character."},

    {"Field Name": "Original Internal ID", "MDRM": "CLCOG064", 
     "Allowable Values": "Must not contain a carriage return, line feed, comma or any unprintable character."},

    {"Field Name": "Obligor Name", "MDRM": "CLCO9017", 
     "Allowable Values": "Must not contain a carriage return, line feed, comma or any unprintable character."},

    {"Field Name": "City", "MDRM": "CLCO9130", 
     "Allowable Values": "Free text (A-Z only)."},

    {"Field Name": "Country", "MDRM": "CLCO9031", 
     "Allowable Values": "Use the 2-letter Country Code (ISO 3166-1 alpha-2)."},

    {"Field Name": "Zip Code", "MDRM": "CLCO9220", 
     "Allowable Values": "US: 5-digit ZIP; International: country-specific postal code."}
])

def convert_to_rule(allowable_values):
    """Convert Allowable Values text into Python validation expressions."""
    
    # No carriage return, line feed, comma, or unprintable characters
    if "Must not contain a carriage return, line feed, comma or any unprintable character" in allowable_values:
        return "not bool(re.search(r'[\\r\\n,\\x00-\\x1F]', value))"
    
    # City name: A-Z only
    elif "Free text (A-Z only)" in allowable_values:
        return "re.match(r'^[A-Za-z\\s]+$', value) is not None"
    
    # Country Code: 2-letter ISO 3166-1 alpha-2
    elif "Use the 2-letter Country Code" in allowable_values:
        return "value in VALID_COUNTRY_CODES"
    
    # ZIP Code validation
    elif "5-digit ZIP" in allowable_values:
        return "re.match(r'^\\d{5}$', value) is not None"
    
    # Default: No restriction
    return "True"

# Apply function to generate validation rules
pdf_rules["Validation Rule"] = pdf_rules["Allowable Values"].apply(convert_to_rule)

# Display updated DataFrame
print(pdf_rules)

#read input CSV file 

def read_input_from_csv(csv_path):
    input_data = []
    with open(csv_path, mode='r') as file:
        reader = csv.DictReader(file) 
        for row in reader:
            input_data.append({
                "Customer ID": row["Customer ID"],
                "Internal ID": row["Internal ID"],
                "Original Internal ID": row["Original Internal ID"],
                "Obligor Name": row["Obligor Name"],
                "City": row["City"],
                "Country": row["Country"],
                "Zip Code": row["Zip Code"]
            })
    return pd.DataFrame(input_data, columns=["Customer ID", "Internal ID", "Original Internal ID", "Obligor Name", "City", "Country", "Zip Code"])

# Function to validate CSV row data against the ruls in the PDF
def validate_row(row, rules_df):
    errors = []
    
    for _, rule in rules_df.iterrows():
        field = rule["Field Name"]
        mdrm = rule["MDRM"]
        Allowable_Values = rule["Allowable Values"]
        validation_rule = rule["Validation Rule"]

        value = str(row.get(field, ""))  # Get field value from row

        try:
            # Evaluate the rule dynamically
            if not eval(validation_rule):
                errors.append({
                    "Row Number": row.name + 1,  # Row index (1-based)
                    "Field Name": field,
                    "MDRM": mdrm,
                    "Allowable Values": Allowable_Values,
                    "Invalid Value": value
                })
        except Exception as e:
            errors.append({
                "Row Number": row.name + 1,
                "Field Name": field,
                "MDRM": mdrm,
                "Allowable Values": Allowable_Values,
                "Invalid Value": value
            })

    return errors
	
import pandas as pd
validation_errors = []
for idx, row in csv_data.iterrows():
    validation_errors.extend(validate_row(row, pdf_rules))
	
# Convert validation errors into a DataFrame
validation_results = pd.DataFrame(validation_errors)

# Save validation errors to output CSV
output_csv_path = r"C:\Users\sachi\Downloads\hackathon\validation_result.csv"
validation_results.to_csv(output_csv_path, index=False)