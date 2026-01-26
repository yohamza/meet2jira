import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

    # JIRA CONFIG
    JIRA_BASE_URL = os.environ.get('JIRA_BASE_URL')
    JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
    JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN')
    JIRA_DEFAULT_PROJECT = os.environ.get('JIRA_DEFAULT_PROJECT', 'IWMP') # Default to IWMP
