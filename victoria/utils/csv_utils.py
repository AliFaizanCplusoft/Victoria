"""
CSV Conversion Utilities
Utility functions for converting between different data formats
"""

import pandas as pd
import logging
from io import StringIO

logger = logging.getLogger(__name__)

def convert_raw_text_to_csv_format(raw_text: str) -> pd.DataFrame:
    """
    Convert raw text with ### formatted questions to CSV format
    
    Args:
        raw_text: Raw text content with ### formatted questions
        
    Returns:
        DataFrame with questions as columns and answers as rows
    """
    import re
    
    logger.info("Converting raw text format to CSV...")
    
    # Split into blocks by ### headers
    lines = raw_text.split('\n')
    
    current_question = None
    answer_lines = []
    question_answer_pairs = []
    
    for line in lines:
        line = line.strip()
        
        # Check if line is a question (starts with ###)
        if line.startswith('###'):
            # Save previous question-answer pair
            if current_question:
                full_answer = '\n'.join(answer_lines).strip()
                if full_answer:
                    question_answer_pairs.append((current_question, full_answer))
            
            # Extract question text (remove ### and any trailing punctuation)
            current_question = re.sub(r'^###\s*', '', line)
            current_question = re.sub(r'\s*$', '', current_question)
            answer_lines = []
        elif current_question and line:
            # This is an answer line
            answer_lines.append(line)
    
    # Don't forget the last question
    if current_question and answer_lines:
        full_answer = '\n'.join(answer_lines).strip()
        if full_answer:
            question_answer_pairs.append((current_question, full_answer))
    
    logger.info(f"Extracted {len(question_answer_pairs)} question-answer pairs")
    
    # Create a dictionary with questions as keys
    data_dict = {}
    for question, answer in question_answer_pairs:
        data_dict[question] = answer
    
    # Create DataFrame with one row
    df = pd.DataFrame([data_dict])
    
    return df

def convert_csv_to_pipeline_format(csv_content: str) -> pd.DataFrame:
    """
    Convert the Zapier CSV format to the format expected by the pipeline
    
    Args:
        csv_content: Raw CSV content from Zapier
        
    Returns:
        DataFrame in the format expected by the pipeline
    """
    # Create a mapping from text responses to numeric values
    response_mapping = {
        "Always (91-100%)": 5,
        "Often (66-90%)": 4,
        "Sometimes (36-65%)": 3,
        "Seldom (11-35%)": 2,
        "Never (0-10%)": 1
    }
    
    # Read the CSV content
    from io import StringIO
    
    logger.info(f"Attempting to parse CSV content, length: {len(csv_content)}")
    logger.info(f"First 500 chars of CSV: {csv_content[:500]}")
    
    # Check if it's raw text format (starts with ###)
    is_raw_text_format = csv_content.strip().startswith('### ')
    
    if is_raw_text_format:
        logger.info("Detected raw text format, converting to CSV...")
        df = convert_raw_text_to_csv_format(csv_content)
    else:
        logger.info("Detected CSV format, parsing directly...")
        df = pd.read_csv(StringIO(csv_content))
    
    logger.info(f"Successfully parsed CSV with {len(df.columns)} columns and {len(df)} rows")
    
    # Use the first data row (pandas already handles headers correctly)
    logger.info(f"Using row 0 from CSV (first data row after parsing)")
    
    # Debug: Log some column names and values to understand the structure
    logger.info(f"Sample column names (first 20): {list(df.columns[:20])}")
    
    # Try to find a column with actual data
    row = df.iloc[0]
    for i, col in enumerate(df.columns[:20]):
        if col in row:
            val = row[col]
            if pd.notna(val) and str(val).strip():
                logger.info(f"Sample column '{col}' value: {str(val)[:100]}")
                break
    
    # Also check Email, First name, Last name
    email_cols = ['Email', 'email', 'Thanks in advance for confirming your email address.']
    first_name_cols = ['First name', 'first_name', 'First Name']
    last_name_cols = ['Last name', 'last_name', 'Last Name']
    
    for col in email_cols:
        if col in df.columns:
            logger.info(f"Column '{col}': {row.get(col, 'N/A')}")
            break
    
    for col in first_name_cols:
        if col in df.columns:
            logger.info(f"Column '{col}': {row.get(col, 'N/A')}")
            break
    
    for col in last_name_cols:
        if col in df.columns:
            logger.info(f"Column '{col}': {row.get(col, 'N/A')}")
            break
    
    logger.info(f"Column '#': {row.get('#', 'N/A')}")
    
    # Map the entire row to a dictionary - keep all data as-is
    processed_data = {}
    
    # Convert the row to dict and keep all values as strings for pipeline processing
    for col in df.columns:
        if col in row:
            value = row[col]
            # Keep all values as strings - let the pipeline handle the mapping
            if pd.notna(value) and str(value).strip():
                processed_data[col] = str(value).strip()
            else:
                processed_data[col] = ""
        else:
            processed_data[col] = ""
    
    logger.info(f"Created processed data with {len(processed_data)} fields from CSV")
    logger.info(f"All values kept as strings for pipeline processing")
    
    # Debug: Show which open-ended questions have data
    open_ended_questions = [
        "What is drawing you toward entrepreneurship at this moment in your life?",
        "What does \"entrepreneurship\" mean to you personally?",
        "What's a time when you took initiative or built something from scratch?",
        "What fears or uncertainties do you have about starting something of your own?",
        "What kind of work energizes you most—and why?",
        "When you imagine your future, what role (if any) does building something yourself play?",
        "What questions are you hoping this experience will help you answer?",
        "What would success look like for you in this phase of exploration?"
    ]
    
    logger.info("Checking which open-ended questions have answers in CSV:")
    found_count = 0
    for q in open_ended_questions:
        if q in processed_data:
            val = str(processed_data[q]).strip()
            if val and val != '' and val.lower() != 'nan':
                logger.info(f"  ✓ '{q[:50]}...' has data")
                found_count += 1
            else:
                logger.info(f"  ✗ '{q[:50]}...' is EMPTY in CSV")
        else:
            logger.info(f"  ✗ '{q[:50]}...' MISSING from CSV columns")
    logger.info(f"Total open-ended questions with data: {found_count}/{len(open_ended_questions)}")
    
    # Create DataFrame from the processed data
    df_processed = pd.DataFrame([processed_data])
    
    return df_processed
