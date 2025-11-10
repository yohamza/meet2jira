# MeetX (PostgreSQL Version)

This project is a Python-based application that automatically extracts action items from Google Meet transcripts stored in Google Drive. It uses the OpenAI API to analyze the transcripts and saves the meetings, transcripts, and extracted action items into a PostgreSQL database.

## Features

*   **Google Drive Integration:** Polls a specified Google Drive folder for the newest Google Doc transcript.
*   **AI-Powered Action Item Extraction:** Uses OpenAI's `gpt-4o-mini` to intelligently parse transcripts and extract action items, including descriptions and assignees.
*   **Database Storage:** Saves all data to a PostgreSQL database using SQLAlchemy.
*   **REST API:** Provides a simple Flask-based API to trigger the process and retrieve data.
*   **OAuth 2.0 Authentication:** Securely connects to the Google Drive API.
*   **Database Migrations:** Uses Flask-Migrate (Alembic) to manage database schema changes.

## How It Works

1.  **Authentication:** The first time you use the app, you run `get_token.py` to authenticate with your Google account and authorize read-only access to your Google Drive. This creates a `token.json` file.
2.  **API Call:** You send a `POST` request to the `/api/process-newest-transcript` endpoint, providing a Google Drive folder ID.
3.  **Fetch Transcript:** The application uses the Google Drive API to find the most recent Google Doc in that folder and downloads its content as plain text.
4.  **Extract Action Items:** The transcript text is sent to the OpenAI API. A carefully crafted prompt instructs the model to find and return a structured JSON list of action items.
5.  **Save to Database:** The application creates a new `Meeting` record, saves the `Transcript`, and stores each extracted `ActionItem` in the PostgreSQL database, linking them all together.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd meetx
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Google API Credentials:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project.
    *   Enable the "Google Drive API".
    *   Create OAuth 2.0 credentials for a "Desktop app".
    *   Download the credentials JSON file and save it as `credentials.json` in the project root.

5.  **Set up OpenAI API Key:**
    *   Get your API key from the [OpenAI Platform](https://platform.openai.com/).
    *   Create a `.env` file in the project root and add your key:
        ```
        OPENAI_API_KEY='your-openai-api-key'
        ```

6.  **Set up PostgreSQL Database:**
    *   Make sure you have PostgreSQL installed and running.
    *   Create a new database for this project.
    *   Add the database connection URL to your `.env` file. It should look like this:
        ```
        DATABASE_URL='postgresql://user:password@host:port/dbname'
        ```

7.  **Run Initial Authentication:**
    *   Run the `get_token.py` script once to authorize Google Drive access. This will open a browser window for you to log in.
    ```bash
    python get_token.py
    ```
    This will create a `token.json` file.

8.  **Run Database Migrations:**
    *   Apply the initial database schema:
    ```bash
    flask db upgrade
    ```

## Usage

1.  **Start the Flask server:**
    ```bash
    flask run
    ```
    The server will be running at `http://127.0.0.1:5000`.

2.  **Trigger Transcript Processing:**
    *   Use a tool like `curl` or Postman to send a POST request to the API. Replace `"YOUR_FOLDER_ID"` with the ID of the Google Drive folder where your transcripts are saved.
    ```bash
    curl -X POST -H "Content-Type: application/json" \
      -d '{"folder_id": "YOUR_FOLDER_ID"}' \
      http://127.0.0.1:5000/api/process-newest-transcript
    ```

## API Endpoints

*   `POST /api/process-newest-transcript`
    *   Triggers the process of fetching the newest transcript from a Google Drive folder, extracting action items, and saving everything to the database.
    *   **Request Body:** `{"folder_id": "your-google-drive-folder-id"}`
    *   **Success Response (201):**
        ```json
        {
          "message": "Transcript processed successfully",
          "meeting_code": "Your Document Name",
          "meeting_id": 1,
          "preview": "Transcript preview..."
        }
        ```

*   `GET /api/meetings/<int:meeting_id>`
    *   Retrieves the details for a specific meeting.
    *   **Success Response (200):**
        ```json
        {
            "meeting_id": 1,
            "meeting_code": "Your Document Name",
            "processed_at": "2025-11-09T12:00:00Z",
            "transcript_content": "Transcript preview..."
        }
        ```

*   `GET /api/meetings/<int:meeting_id>/action-items`
    *   Retrieves all the action items that were extracted from a specific meeting.
    *   **Success Response (200):**
        ```json
        {
            "meeting_id": 1,
            "meeting_code": "Your Document Name",
            "action_items": [
                {
                    "id": 1,
                    "description": "Send the Q4 report to the marketing team.",
                    "assignee": "Alice",
                    "status": "todo",
                    "created_at": "2025-11-09T12:00:00Z"
                }
            ]
        }
        ```
