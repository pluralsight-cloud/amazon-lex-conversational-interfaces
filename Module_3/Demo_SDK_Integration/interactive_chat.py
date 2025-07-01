#!/usr/bin/env python3
"""
Interactive chat application with Lex bot
Replace BOT_ID with your actual bot ID before running
"""

import boto3
from datetime import datetime

def initialize_lex_client(region='us-east-1'):
    """Initialize Amazon Lex Runtime v2 client"""
    try:
        client = boto3.client('lexv2-runtime', region_name=region)
        print(f"Lex client initialized for region: {region}")
        return client
    except Exception as e:
        print(f"Error initializing Lex client: {str(e)}")
        return None

def recognize_text(client, bot_id, bot_alias_id, locale_id, session_id, text_input):
    """Send text input to Lex bot using RecognizeText API"""
    try:
        response = client.recognize_text(
            botId=bot_id,
            botAliasId=bot_alias_id,
            localeId=locale_id,
            sessionId=session_id,
            text=text_input
        )
        
        return response
        
    except Exception as e:
        print(f"Error in RecognizeText: {str(e)}")
        return None

def chat_with_bot():
    """Interactive conversation with the bot"""
    
    # Bot configuration - REPLACE WITH YOUR BOT DETAILS
    BOT_ID = 'YOUR_BOT_ID_HERE'  # Replace with your actual bot ID
    BOT_ALIAS_ID = 'TSTALIASID'  # Or your custom alias ID
    LOCALE_ID = 'en_US'
    SESSION_ID = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Initialize client
    client = initialize_lex_client()
    if not client:
        return
    
    print("Starting conversation with bot...")
    print(f"Bot ID: {BOT_ID}")
    print(f"Session ID: {SESSION_ID}")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Goodbye!")
            break
        
        if not user_input.strip():
            continue
        
        # Send text to bot
        response = recognize_text(
            client=client,
            bot_id=BOT_ID,
            bot_alias_id=BOT_ALIAS_ID,
            locale_id=LOCALE_ID,
            session_id=SESSION_ID,
            text_input=user_input
        )
        
        if response:
            # Extract bot's response message
            messages = response.get('messages', [])
            if messages:
                bot_message = messages[0].get('content', 'No response')
                print(f"Bot: {bot_message}")
            
            # Check if conversation is complete
            intent_state = response.get('sessionState', {}).get('intent', {}).get('state')
            if intent_state == 'Fulfilled':
                print("Intent fulfilled!")
            elif intent_state == 'Failed':
                print("Intent failed!")
        
        print()  # Add spacing

# Run the chat
if __name__ == "__main__":
    chat_with_bot()
