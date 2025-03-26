import pdfplumber
import pandas as pd

# Step 1: Extract data from the regulatory PDF document
def extract_regulatory_rules(pdf_path):
    # Extract the table from the PDF
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]  # Assuming the table is on the first page
        table = page.extract_table()

    # Create a DataFrame from the table (skip the header row)
    df = pd.DataFrame(table[1:], columns=table[0])

    # Return extracted rules
    return df[['field_name', 'description', 'allowable_values']]

# Step 2: Validate the input CSV based on extracted rules
def validate_transaction_file(csv_path, rules_df):
    # Load the transaction file (CSV)
    transactions = pd.read_csv(csv_path)
    
    # Initialize a list to store flagged transactions
    flagged_transactions = []
    
    for _, rule in rules_df.iterrows():
        field_name = rule['field_name']
        allowable_values = rule['allowable_values']
        
        # Extract the relevant column in the transaction data
        if field_name in transactions.columns:
            column_data = transactions[field_name]
            
            # Validation check: Handle different types of allowable values
            if 'integer' in allowable_values:
                # Check if the value is an integer
                invalid_rows = column_data[~column_data.apply(lambda x: isinstance(x, int))]
            elif 'unique' in allowable_values:
                # Check if the value is unique
                invalid_rows = column_data[column_data.duplicated()]
            else:
                invalid_rows = []
            
            # Flag the invalid rows
            if not invalid_rows.empty:
                flagged_transactions.append({
                    'field_name': field_name,
                    'invalid_transactions': invalid_rows.tolist(),
                    'allowable_values': allowable_values
                })

    return flagged_transactions

# Step 3: Generate an Excel report of the flagged transactions
def generate_flagged_report(flagged_transactions, output_file='flagged_transactions.xlsx'):
    # Prepare data for Excel output
    flagged_data = []
    for transaction in flagged_transactions:
        for invalid in transaction['invalid_transactions']:
            flagged_data.append({
                'Field Name': transaction['field_name'],
                'Invalid Transaction': invalid,
                'Allowable Values': transaction['allowable_values']
            })

    # Convert flagged data into a DataFrame and write to Excel
    flagged_df = pd.DataFrame(flagged_data)
    flagged_df.to_excel(output_file, index=False)

# Example usage:
def main():
    pdf_path = 'regulatory_instructions.pdf'  # Path to regulatory document
    csv_path = 'input_transactions.csv'       # Path to the transaction CSV

    # Step 1: Extract regulatory rules
    rules_df = extract_regulatory_rules(pdf_path)
    print(f"Extracted Rules:\n{rules_df}")

    # Step 2: Validate the transactions
    flagged_transactions = validate_transaction_file(csv_path, rules_df)
    
    if flagged_transactions:
        print(f"Flagged Transactions: {flagged_transactions}")
        # Step 3: Generate Excel report for flagged transactions
        generate_flagged_report(flagged_transactions)
        print("Flagged transactions report saved as 'flagged_transactions.xlsx'")
    else:
        print("No flagged transactions found.")

if __name__ == "__main__":
    main()
