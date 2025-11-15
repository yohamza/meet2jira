from app import db

class Meeting(db.Model):
    """
    Represents a meeting, identified by its unique code.
    In our test version, the 'meeting_code' will be the Google Doc's filename.
    """
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # The Google Doc name, e.g., "Team Sync (2025-11-09)"
    meeting_code = db.Column(db.String(255), unique=True, nullable=False) 
    
    processed_at = db.Column(db.DateTime, server_default=db.func.now())

    # This creates a one-to-one relationship with the Transcript
    # The 'back_populates' links it to the 'meeting' attribute in the Transcript model
    transcript = db.relationship(
        'Transcript', 
        back_populates='meeting', 
        uselist=False, 
        cascade="all, delete-orphan"
    )

    action_items = db.relationship(
        'ActionItem',
        back_populates='meeting',
        lazy='dynamic', # Helps with performance
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Meeting {self.meeting_code}>"

class Transcript(db.Model):
    """
    Stores the full text content of a meeting transcript.
    """
    __tablename__ = 'transcripts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # db.Text is used for long, unlimited-length text
    content = db.Column(db.Text, nullable=False) 
    
    # This is the foreign key that links this table to the 'meetings' table
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False, unique=True)
    
    # This links it back to the Meeting object
    meeting = db.relationship('Meeting', back_populates='transcript')

    def __repr__(self):
        return f"<Transcript for Meeting {self.meeting_id}>"
    

class ActionItem(db.Model):
    """
    Stores a single extracted action item.
    """
    __tablename__ = 'action_items'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # The text of the action, e.g., "Send the report to marketing"
    description = db.Column(db.Text, nullable=False)
    
    # The person assigned, if the AI can find it
    assignee = db.Column(db.String(255), nullable=True) 
    
    # A simple status
    status = db.Column(db.String(50), nullable=False, default='todo')
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Foreign key to link back to the meeting
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    
    # The relationship link
    meeting = db.relationship('Meeting', back_populates='action_items')

    def __repr__(self):
        return f"<ActionItem {self.id}: {self.description[:30]}>"
