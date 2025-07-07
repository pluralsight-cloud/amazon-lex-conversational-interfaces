#!/usr/bin/env python3
"""
Amazon Lex v2 Session Management Script

This script demonstrates how to:
1. Track session state across multiple conversation turns
2. Manage context and session attributes
3. Handle multi-turn dialogues programmatically
4. Store and retrieve custom session data

Prerequisites:
- AWS CloudShell (which includes Python 3, boto3, and admin credentials)
- A Lex v2 bot with multi-turn conversation flow (following Part 1 of the tutorial)
"""

import boto3
import json
import time
import uuid
from botocore.exceptions import ClientError

# Configuration - Update these values for your bot
BOT_ID = 'YOUR_BOT_ID'  # Replace with your Bot ID
BOT_ALIAS_ID = 'TSTALIASID'  # Use TSTALIASID for testing or your PROD alias ID
LOCALE_ID = 'en_US'  # English US locale
REGION = 'us-east-1'  # Replace with your preferred AWS region

def create_lex_runtime_client():
    """
    Create and return a Lex v2 runtime client for conversation management
    """
    try:
        # Create the Lex v2 runtime client (lexv2-runtime service)
        client = boto3.client('lexv2-runtime', region_name=REGION)
        print(f"Successfully created Lex v2 runtime client for region: {REGION}")
        return client
    except Exception as e:
        print(f"Error creating Lex runtime client: {str(e)}")
        return None

def generate_session_id():
    """
    Generate a unique session ID for the conversation
    """
    session_id = f'session-{uuid.uuid4()}'
    print(f"Generated session ID: {session_id}")
    return session_id

def send_message_to_bot(client, bot_id, bot_alias_id, locale_id, session_id, message, session_attributes=None):
    """
    Send a message to the Lex bot and get the response
    
    Args:
        client: Boto3 Lex v2 runtime client
        bot_id: The ID of the bot
        bot_alias_id: The alias ID to use
        locale_id: The locale (e.g., 'en_US')
        session_id: Unique session identifier
        message: The user's message
        session_attributes: Dictionary of session attributes to maintain context
    
    Returns:
        dict: The bot's response including session state
    """
    try:
        print(f"\nSending message: '{message}'")
        
        # Prepare the request parameters
        request_params = {
            'botId': bot_id,
            'botAliasId': bot_alias_id,
            'localeId': locale_id,
            'sessionId': session_id,
            'text': message
        }
        
        # Add session attributes if provided
        if session_attributes:
            request_params['sessionState'] = {
                'sessionAttributes': session_attributes
            }
            print(f"Including session attributes: {session_attributes}")
        
        # Call the RecognizeText API
        response = client.recognize_text(**request_params)
        
        # Extract key information from the response
        bot_message = ''
        if 'messages' in response and response['messages']:
            bot_message = response['messages'][0].get('content', '')
        
        session_state = response.get('sessionState', {})
        intent = session_state.get('intent', {})
        intent_name = intent.get('name', 'Unknown')
        intent_state = intent.get('state', 'Unknown')
        
        # Get session attributes from response
        response_session_attributes = session_state.get('sessionAttributes', {})
        
        # Get slot values if available
        slots = intent.get('slots', {})
        
        print(f"Bot response: '{bot_message}'")
        print(f"Intent: {intent_name} (State: {intent_state})")
        
        if slots:
            print("Current slot values:")
            for slot_name, slot_data in slots.items():
                if slot_data and 'value' in slot_data:
                    slot_value = slot_data['value'].get('interpretedValue', 'Not set')
                    print(f"  {slot_name}: {slot_value}")
        
        if response_session_attributes:
            print(f"Session attributes: {response_session_attributes}")
        
        return {
            'bot_message': bot_message,
            'intent_name': intent_name,
            'intent_state': intent_state,
            'slots': slots,
            'session_attributes': response_session_attributes,
            'full_response': response
        }
        
    except ClientError as e:
        print(f"Error sending message to bot: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def demonstrate_session_attributes(client, bot_id, bot_alias_id, locale_id, session_id):
    """
    Demonstrate how to use session attributes to maintain context
    """
    print("\n" + "="*50)
    print("DEMONSTRATING SESSION ATTRIBUTES")
    print("="*50)
    
    # Start with custom session attributes
    custom_attributes = {
        'customerName': 'John Doe',
        'customerType': 'VIP',
        'orderCount': '3'
    }
    
    print("Setting initial session attributes:")
    for key, value in custom_attributes.items():
        print(f"  {key}: {value}")
    
    # Send first message with session attributes
    response = send_message_to_bot(
        client, bot_id, bot_alias_id, locale_id, session_id,
        'I want to order a pizza',
        session_attributes=custom_attributes
    )
    
    if not response:
        return
    
    # Continue conversation using returned session attributes
    current_attributes = response['session_attributes']
    
    # Add more context to session attributes
    current_attributes['conversationStart'] = str(int(time.time()))
    current_attributes['lastIntent'] = response['intent_name']
    
    return current_attributes

def simulate_multi_turn_conversation(client, bot_id, bot_alias_id, locale_id):
    """
    Simulate a complete multi-turn conversation with the bot
    """
    print("\n" + "="*50)
    print("SIMULATING MULTI-TURN CONVERSATION")
    print("="*50)
    
    # Generate a unique session ID for this conversation
    session_id = generate_session_id()
    
    # Conversation flow
    conversation_steps = [
        'Hello',
        'I want to order a pizza',
        'Large',
        'Pepperoni',
        'Yes, that\'s correct'
    ]
    
    session_attributes = {}
    
    for i, message in enumerate(conversation_steps, 1):
        print(f"\n--- Turn {i} ---")
        
        response = send_message_to_bot(
            client, bot_id, bot_alias_id, locale_id, session_id,
            message, session_attributes
        )
        
        if not response:
            print("Failed to get response from bot")
            break
        
        # Update session attributes for next turn
        session_attributes = response['session_attributes']
        
        # Add conversation tracking
        session_attributes[f'turn_{i}_intent'] = response['intent_name']
        session_attributes[f'turn_{i}_state'] = response['intent_state']
        
        # Small delay between turns to simulate real conversation
        time.sleep(1)
    
    print(f"\nConversation completed with session ID: {session_id}")
    return session_id

def demonstrate_context_switching(client, bot_id, bot_alias_id, locale_id):
    """
    Demonstrate context switching within the same session
    """
    print("\n" + "="*50)
    print("DEMONSTRATING CONTEXT SWITCHING")
    print("="*50)
    
    session_id = generate_session_id()
    session_attributes = {'demo': 'context_switching'}
    
    # Start an order
    print("\n--- Starting Pizza Order ---")
    response1 = send_message_to_bot(
        client, bot_id, bot_alias_id, locale_id, session_id,
        'I want to order a pizza', session_attributes
    )
    
    if response1:
        session_attributes = response1['session_attributes']
        
        # Provide size
        print("\n--- Providing Size ---")
        response2 = send_message_to_bot(
            client, bot_id, bot_alias_id, locale_id, session_id,
            'Medium', session_attributes
        )
        
        if response2:
            session_attributes = response2['session_attributes']
            
            # Cancel the order (context switch)
            print("\n--- Canceling Order (Context Switch) ---")
            response3 = send_message_to_bot(
                client, bot_id, bot_alias_id, locale_id, session_id,
                'Actually, cancel that', session_attributes
            )
            
            if response3:
                session_attributes = response3['session_attributes']
                
                # Start a new order in the same session
                print("\n--- Starting New Order in Same Session ---")
                response4 = send_message_to_bot(
                    client, bot_id, bot_alias_id, locale_id, session_id,
                    'I want to order a pizza', session_attributes
                )

def analyze_session_state(response):
    """
    Analyze and display detailed session state information
    """
    if not response:
        return
    
    print("\n" + "-"*30)
    print("SESSION STATE ANALYSIS")
    print("-"*30)
    
    full_response = response['full_response']
    session_state = full_response.get('sessionState', {})
    
    print(f"Session ID: {full_response.get('sessionId', 'Unknown')}")
    print(f"Dialog Action: {session_state.get('dialogAction', {}).get('type', 'Unknown')}")
    
    # Analyze intent state
    intent = session_state.get('intent', {})
    if intent:
        print(f"Intent Name: {intent.get('name', 'Unknown')}")
        print(f"Intent State: {intent.get('state', 'Unknown')}")
        print(f"Intent Confirmation State: {intent.get('confirmationState', 'Unknown')}")
    
    # Show active contexts if any
    active_contexts = session_state.get('activeContexts', [])
    if active_contexts:
        print("Active Contexts:")
        for context in active_contexts:
            print(f"  - {context.get('name', 'Unknown')}")

def main():
    """
    Main function that demonstrates various session management capabilities
    """
    print("Starting Amazon Lex v2 Session Management Demo")
    print("=" * 60)
    
    # Validate configuration
    if BOT_ID == 'YOUR_BOT_ID_HERE':
        print("Please update the BOT_ID variable with your actual bot ID")
        print("You can find your bot ID in the Lex console")
        return
    
    # Create Lex runtime client
    client = create_lex_runtime_client()
    if not client:
        return
    
    print(f"\nBot Configuration:")
    print(f"Bot ID: {BOT_ID}")
    print(f"Bot Alias ID: {BOT_ALIAS_ID}")
    print(f"Locale: {LOCALE_ID}")
    
    try:
        # Demonstrate session attributes
        session_attributes = demonstrate_session_attributes(
            client, BOT_ID, BOT_ALIAS_ID, LOCALE_ID, generate_session_id()
        )
        
        # Simulate a complete multi-turn conversation
        simulate_multi_turn_conversation(client, BOT_ID, BOT_ALIAS_ID, LOCALE_ID)
        
        # Demonstrate context switching
        demonstrate_context_switching(client, BOT_ID, BOT_ALIAS_ID, LOCALE_ID)
        
        print("\n" + "=" * 60)
        print("Session Management Demo Completed!")
        
    except Exception as e:
        print(f"Error during demo: {str(e)}")

if __name__ == '__main__':
    main()
