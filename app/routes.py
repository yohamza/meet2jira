import os
from flask import Blueprint, request, jsonify
from app import db
from app.models import Meeting, Transcript, ActionItem
from app import google_client
from app import action_extractor

main = Blueprint('main', __name__)

@main.route('/')
def home():
    """A simple route to check if the server is running."""
    return f"{os.environ.get('APP_NAME')} is running..."

@main.route('/api/meetings/<int:meeting_id>', methods=['GET'])
def get_meeting_details(meeting_id):
    """
    Gets a specific meeting and its transcript.
    """
    meeting = Meeting.query.get(meeting_id)
    
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404
        
    return jsonify({
        "meeting_id": meeting.id,
        "meeting_code": meeting.meeting_code,
        "processed_at": meeting.processed_at,
        "transcript_content": meeting.transcript.content[:200] + "..." # Show a preview
    })

@main.route('/api/meetings/<int:meeting_id>/action-items', methods=['GET'])
def get_action_items_for_meeting(meeting_id):
    """
    Gets all action items for a specific meeting ID.
    """
    # 1. Find the meeting by its ID
    meeting = Meeting.query.get(meeting_id)
    
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404
    
    # 2. Use the "magic" relationship (this is the implicit JOIN)
    # SQLAlchemy gets all ActionItem objects linked to this meeting
    action_items = meeting.action_items

    # 3. Format the data for a JSON response
    # We use a list comprehension to build a list of dictionaries
    action_items_list = [
        {
            "id": item.id,
            "description": item.description,
            "assignee": item.assignee,
            "status": item.status,
            "created_at": item.created_at
        }
        for item in action_items
    ]
    
    return jsonify({
        "meeting_id": meeting.id,
        "meeting_code": meeting.meeting_code,
        "action_items": action_items_list
    })

@main.route('/api/process-newest-transcript', methods=['POST'])
def process_newest_transcript():
    """
    API endpoint to poll a Google Drive folder, get the newest transcript,
    and save it to the database.
    
    Expects JSON body: {"folder_id": "YOUR_FOLDER_ID"}
    """
    data = request.get_json()
    if not data or 'folder_id' not in data:
        return jsonify({"error": "Missing 'folder_id' in request body"}), 400

    folder_id = data['folder_id']

    # 1. Fetch the newest transcript text from Google Drive
    print(f"Polling Drive folder {folder_id} for newest transcript...")
    doc_name, transcript_text = google_client.get_transcript_from_folder(folder_id)

    print(f"Fetched document: {doc_name}")

    if transcript_text is None:
        return jsonify({"error": f"Could not fetch any new transcript from folder {folder_id}"}), 404

    # 2. Check if we already processed this file (using the doc name)
    existing_meeting = Meeting.query.filter_by(meeting_code=doc_name).first()
    if existing_meeting:
        return jsonify({
            "message": f"This transcript '{doc_name}' has already been processed.",
            "meeting_id": existing_meeting.id
        }), 200 # 200 OK, since it's not an error

    # 3. Save the new transcript to the database
    try:
        new_meeting = Meeting(meeting_code=doc_name)
        new_transcript = Transcript(content=transcript_text, meeting=new_meeting)
        
        db.session.add(new_meeting)
        db.session.add(new_transcript)
        db.session.commit()
        
        print(f"Successfully saved transcript for '{doc_name}'.")

        action_items_list = action_extractor.extract_action_items(transcript_text)
        
        if action_items_list:
            for item in action_items_list:
                new_action_item = ActionItem(
                    description=item.get('description'),
                    assignee=item.get('assignee'),
                    meeting_id=new_meeting.id  # Link it to the meeting
                )
                db.session.add(new_action_item)
            
            # Commit the new action items to the database
            db.session.commit()
            print(f"Saved {len(action_items_list)} new action items.")


        return jsonify({
            "message": "Transcript processed successfully",
            "meeting_code": doc_name,
            "meeting_id": new_meeting.id,
            "preview": transcript_text[:100] + "..."
        }), 201 # 201 Created

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
        # If new_meeting was created before the error, try to clean it up
        if new_meeting and new_meeting.id:
            # Re-fetch and delete the partially created meeting
            db.session.delete(Meeting.query.get(new_meeting.id))
            db.session.commit()
            print(f"Cleaned up partial meeting entry {new_meeting.id}.")

        return jsonify({"error": "Failed to save transcript to database."}), 500
