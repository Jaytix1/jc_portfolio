import pdfplumber
import pandas as pd
import re
from pathlib import Path


def extract_tables_from_pdf(pdf_path):
    """
    Extract tables from a PDF manifest.
    Returns a list of DataFrames, one per table found.
    """
    tables = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Try to extract tables from this page
            page_tables = page.extract_tables()

            for table in page_tables:
                if table and len(table) > 1:  # Has header + at least one row
                    # Convert to DataFrame
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df['_page'] = page_num + 1
                    tables.append(df)

    return tables


def extract_text_from_pdf(pdf_path):
    """
    Extract raw text from PDF for analysis or fallback parsing.
    """
    text_content = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)

    return '\n\n'.join(text_content)


def parse_manifest(pdf_path):
    """
    Parse a manifest PDF and return structured data.
    Attempts table extraction first, falls back to text parsing.

    Returns dict with:
    - items: list of {sku, description, quantity, ...}
    - metadata: any header info found
    - raw_text: full text for AI analysis
    """
    result = {
        'items': [],
        'metadata': {},
        'raw_text': '',
        'parse_method': None,
        'errors': []
    }

    try:
        # Get raw text for AI analysis regardless of parsing method
        result['raw_text'] = extract_text_from_pdf(pdf_path)

        # Try table extraction first
        tables = extract_tables_from_pdf(pdf_path)

        if tables:
            result['parse_method'] = 'table'
            result['items'] = parse_table_data(tables)
        else:
            # Fall back to text parsing
            result['parse_method'] = 'text'
            result['items'] = parse_text_data(result['raw_text'])

        # Extract metadata from text
        result['metadata'] = extract_metadata(result['raw_text'])

    except Exception as e:
        result['errors'].append(str(e))

    return result


def parse_table_data(tables):
    """
    Parse structured table data into manifest items.
    Attempts to identify common column names.
    """
    items = []

    # Common column name patterns
    sku_patterns = ['sku', 'item', 'item #', 'item number', 'product code', 'upc', 'code']
    desc_patterns = ['description', 'desc', 'name', 'product', 'item description']
    qty_patterns = ['quantity', 'qty', 'units', 'count', 'amount', 'cases', 'pcs']
    case_patterns = ['case pack', 'pack', 'case qty', 'per case']

    for df in tables:
        if df.empty:
            continue

        # Normalize column names
        df.columns = [str(c).lower().strip() if c else f'col_{i}' for i, c in enumerate(df.columns)]

        # Find matching columns
        sku_col = find_column(df.columns, sku_patterns)
        desc_col = find_column(df.columns, desc_patterns)
        qty_col = find_column(df.columns, qty_patterns)
        case_col = find_column(df.columns, case_patterns)

        for _, row in df.iterrows():
            item = {
                'sku': clean_value(row.get(sku_col, '')) if sku_col else '',
                'description': clean_value(row.get(desc_col, '')) if desc_col else '',
                'quantity': parse_number(row.get(qty_col, 0)) if qty_col else 0,
                'case_pack': parse_number(row.get(case_col, None)) if case_col else None,
            }

            # Skip rows that look like headers or totals
            if item['sku'] and not is_header_row(item):
                items.append(item)

    return items


def parse_text_data(text):
    """
    Parse unstructured text into manifest items.
    Uses regex patterns to find SKU/quantity patterns.
    """
    items = []

    # Common patterns for SKU + quantity in text
    # Pattern: SKU followed by description and quantity
    patterns = [
        r'([A-Z0-9-]{4,20})\s+(.+?)\s+(\d+)\s*(?:units?|pcs?|cases?)?',
        r'(\d{6,14})\s+(.+?)\s+(\d+)',  # UPC-style numbers
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if len(match) >= 3:
                items.append({
                    'sku': match[0].strip(),
                    'description': match[1].strip()[:100],  # Limit description length
                    'quantity': parse_number(match[2]),
                    'case_pack': None
                })

    # Deduplicate by SKU
    seen = set()
    unique_items = []
    for item in items:
        if item['sku'] not in seen:
            seen.add(item['sku'])
            unique_items.append(item)

    return unique_items


def extract_metadata(text):
    """
    Extract metadata like dates, PO numbers, etc from text.
    """
    metadata = {}

    # Date patterns
    date_patterns = [
        (r'(?:date|ship date|delivery date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', 'date'),
        (r'(?:po|purchase order|order)[:\s#]*(\w+)', 'po_number'),
        (r'(?:vendor|supplier)[:\s]*(.+?)(?:\n|$)', 'vendor'),
    ]

    for pattern, key in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()

    return metadata


def find_column(columns, patterns):
    """Find a column matching any of the patterns."""
    for col in columns:
        col_lower = str(col).lower()
        for pattern in patterns:
            if pattern in col_lower:
                return col
    return None


def clean_value(value):
    """Clean a cell value."""
    if value is None:
        return ''
    return str(value).strip()


def parse_number(value):
    """Parse a number from various formats."""
    if value is None:
        return 0
    try:
        # Remove commas, spaces, and common suffixes
        cleaned = re.sub(r'[,\s]', '', str(value))
        cleaned = re.sub(r'(units?|pcs?|cases?|ea)$', '', cleaned, flags=re.IGNORECASE)
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def is_header_row(item):
    """Check if a row looks like a header or total row."""
    skip_words = ['total', 'subtotal', 'grand total', 'sku', 'item', 'description', 'quantity']
    sku_lower = item['sku'].lower()
    desc_lower = item['description'].lower()

    for word in skip_words:
        if word in sku_lower or word == desc_lower:
            return True
    return False


def get_manifest_summary(items):
    """Generate a summary of parsed manifest items."""
    if not items:
        return {
            'total_skus': 0,
            'total_units': 0,
            'top_items': []
        }

    total_skus = len(items)
    total_units = sum(item.get('quantity', 0) for item in items)

    # Sort by quantity and get top 10
    sorted_items = sorted(items, key=lambda x: x.get('quantity', 0), reverse=True)
    top_items = sorted_items[:10]

    return {
        'total_skus': total_skus,
        'total_units': total_units,
        'top_items': top_items
    }
