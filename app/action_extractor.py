import json
import re
from openai import OpenAI
from flask import current_app

# Initialize the OpenAI client
# It will automatically read the OPENAI_API_KEY from your .env file
try:
    client = OpenAI()
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please make sure your OPENAI_API_KEY is set in your .env file.")
    client = None

def extract_action_items(transcript_text):
    """
    Uses OpenAI's GPT model to extract action items from a transcript.
    Returns a list of dictionaries.
    """
    if not client:
        print("OpenAI client is not initialized. Cannot extract action items.")
        return []

    # This is the "prompt" - we're telling the AI what to do
    system_prompt = """
    You are an expert meeting assistant. Your task is to read a meeting
    transcript and extract all action items.
    
    For each action item, identify the following:
    - 'description': A clear, concise description of the task.
    - 'assignee': The name of the person (or people) assigned to the task.
      If no one is explicitly assigned, set this to null.
      
    Respond ONLY with a valid JSON object. The object should contain a single
    key called 'action_items', which is a list of all extracted tasks.
    
    Do not include any text before or after the JSON object.
    
    Example:
    {
      "action_items": [
        { "description": "Send the Q4 report to the marketing team.", "assignee": "Alice" },
        { "description": "Update the project timeline in Asana.", "assignee": "Bob" },
        { "description": "Research new CRM tools.", "assignee": null }
      ]
    }
    """

    print("Sending transcript to OpenAI for analysis...")

    try:
        completion = client.chat.completions.create(
            # We use gpt-4o-mini because it's fast, cheap, and smart
            model="gpt-4o-mini",
            
            # This forces the model to return valid JSON
            response_format={"type": "json_object"}, 
            
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text}
            ]
        )
        
        response_text = completion.choices[0].message.content
        
        # Parse the JSON response
        data = json.loads(response_text)
        
        print(f"Successfully extracted {len(data.get('action_items', []))} action items.")
        return data.get('action_items', [])

    except Exception as e:
        print(f"An error occurred while calling OpenAI: {e}")
        return []

TICKET_ID_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")
CONTINUATION_RE = re.compile(r"^\s*(?:[-*]|\d+[\.\)])\s+")

def _is_continuation_line(line):
    if not line:
        return False
    if CONTINUATION_RE.match(line):
        return True
    lower = line.lower()
    return lower.startswith(("action:", "action item", "actions:", "discussion:", "notes:", "decision:"))

def _normalize_note(lines):
    cleaned = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        cleaned.append(text)
    return "\n".join(cleaned)

def extract_jira_ticket_notes_regex(transcript_text):
    """
    Extracts Jira ticket IDs and nearby notes using simple heuristics.
    Returns a dict: { "PROJ-123": ["note1", "note2"] }.
    """
    lines = transcript_text.splitlines()
    notes_by_ticket = {}

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        tickets = TICKET_ID_RE.findall(line)
        if not tickets:
            continue

        collected = [line]
        j = idx + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if not next_line:
                break
            if TICKET_ID_RE.search(next_line):
                break
            if _is_continuation_line(next_line):
                collected.append(next_line)
                j += 1
                continue
            break

        note = _normalize_note(collected)
        for ticket in tickets:
            notes_by_ticket.setdefault(ticket, [])
            if note and note not in notes_by_ticket[ticket]:
                notes_by_ticket[ticket].append(note)

    return notes_by_ticket

def extract_jira_ticket_notes_ai(transcript_text):
    """
    Uses OpenAI to extract Jira ticket IDs and associated notes.
    Returns a dict: { "PROJ-123": ["note1", "note2"] }.
    """
    if not client:
        print("OpenAI client is not initialized. Cannot extract Jira notes.")
        return {}
    
    default_project = current_app.config.get('JIRA_DEFAULT_PROJECT', 'IWMP')

    system_prompt = f"""
    You are an expert Project Manager assistant. Your task is to extract Jira ticket updates from a meeting transcript.

    CRITICAL RULE FOR TICKET IDs:
    - The team often refers to tickets by number only (e.g., "look at 991" or "ticket 400").
    - If you see a number discussed as a task/issue, assume it belongs to the project "{default_project}".
    - Example: "Fix 991" -> Ticket ID: "{default_project}-991"
    - Example: "IWMP-102 is done" -> Ticket ID: "IWMP-102"
    - Do NOT create tickets for monetary values or generic numbers (e.g. "$500", "500 users").

    OUTPUT FORMAT:
    Return ONLY a valid JSON object.
    Keys = Ticket IDs (e.g., "{default_project}-991").
    Values = List of strings (notes/updates for that ticket).

    Example JSON:
    {{
      "{default_project}-123": ["John will fix the CSS bug.", "Needs to be deployed by Friday."],
      "IWMP-50": ["Discussed the API timeout issue."]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text}
            ]
        )
        response_text = completion.choices[0].message.content
        data = json.loads(response_text)
        return {
            key: value if isinstance(value, list) else [str(value)]
            for key, value in data.items()
            if isinstance(key, str) and TICKET_ID_RE.fullmatch(key)
        }
    except Exception as e:
        print(f"An error occurred while calling OpenAI for Jira notes: {e}")
        return {}

def extract_jira_ticket_notes(transcript_text):
    """
    Wrapper to choose regex or AI-based extraction.
    """
    return extract_jira_ticket_notes_ai(transcript_text)