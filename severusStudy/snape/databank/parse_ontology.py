import pandas as pd


# Function to split the Triple column
def split_triple(triple):
    if pd.isna(triple):
        return [None, None, None]
    # Remove parentheses
    triple = triple.strip('()')
    triple = triple.replace('(', '')

    # Split by comma and strip extra spaces
    parts = [part.strip() for part in triple.split(',')]
    if len(parts) == 3:
        return parts
    else:
        return [None, None, None]


def parse_quarto_ontology():
    # Load the CSV file with the correct delimiter and skip empty lines
    file_path = 'severusStudy/snape/content/ontologies/new_ontology.csv'
    df = pd.read_csv(file_path, delimiter=';', skip_blank_lines=True)

    # Remove rows where all columns are NaN
    df.dropna(how='all', inplace=True)

    # Remove rows where Block value starts with #
    df = df[~df['Block'].str.startswith('#', na=False)]

    # Reset the index
    df.reset_index(drop=True, inplace=True)

    # split triple into start, relation and end
    df[['Start Node', 'Relation', 'End Node']] = df['Triple'].apply(split_triple).apply(pd.Series)

    # Add a unique index as the first column
    df.insert(0, 'Index', range(1, len(df) + 1))
    df['Complexity'] = pd.to_numeric(df['Complexity'], errors='coerce').astype('Int64')
    columns_order = ['Index', 'Block', 'Start Node', 'Relation', 'End Node', 'Condition', 'Complexity']
    df = df[columns_order]

    # Save the cleaned and transformed DataFrame to a new CSV file
    output_file_path = 'severusStudy/snape/content/ontologies/new_ontology_parsed.csv'
    df.to_csv(output_file_path, index=False)
