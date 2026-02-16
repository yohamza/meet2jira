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

TICKET_VALIDATION_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b", re.IGNORECASE)

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
    You are technical Project Manager. Your task is to extract Jira ticket updates from a meeting transcript.

    ### INSTRUCTIONS
    - Scan the transcript for mentions of specific Jira tickets or issue numbers.
    - If a number is mentioned in the context of a bug/task (e.g., "ticket 991", "issue 50"), attach the prefix "{default_project}-".
    - Extract the update/note for that specific ticket.
    - The team often refers to tickets by number only (e.g., "look at 991" or "ticket 400").
    - If you see a number discussed as a task/issue, assume it belongs to the project "{default_project}".
    - Example: "Fix 991" -> Ticket ID: "{default_project}-991"
    - Example: "{default_project}-102 is done" -> Ticket ID: "{default_project}-102"
    - Do NOT create tickets for monetary values or generic numbers (e.g. "$500", "500 users").
    - **DO NOT** create tickets for general action items. Only extract if a specific number/ID was spoken.
    - **DO NOT** invent sequential numbers (like 400, 401, 402) if they were not in the text.
    - If no tickets were mentioned, return an empty object: {{}}


    OUTPUT FORMAT:
    Return ONLY a valid JSON object.
    Keys = Ticket IDs (e.g., "{default_project}-991").
    Values = List of strings (notes/updates for that ticket).

    Example JSON:
    {{
      "{default_project}-123": ["John will fix the CSS bug.", "Needs to be deployed by Friday."],
      "{default_project}-50": ["Discussed the API timeout issue."]
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            temperature=0.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text}
            ]
        )
        response_text = completion.choices[0].message.content
        data = json.loads(response_text)
        validated_data = {}
        for key, value in data.items():
            # Ensure key is a string and looks like a Ticket ID
            if isinstance(key, str) and TICKET_VALIDATION_RE.fullmatch(key):
                key = key.upper()
                # Ensure value is a list of strings
                notes = value if isinstance(value, list) else [str(value)]
                validated_data[key] = notes
        
        return validated_data
    except Exception as e:
        print(f"An error occurred while calling OpenAI for Jira notes: {e}")
        return {}
