import json
from openai import OpenAI

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