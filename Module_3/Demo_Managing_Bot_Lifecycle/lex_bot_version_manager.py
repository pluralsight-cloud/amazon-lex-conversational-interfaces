#!/usr/bin/env python3
'''
This script creates a new bot version and updates an alias to point to it.
'''

import boto3
import time
from botocore.exceptions import ClientError

# Configuration - Update these values for your bot
BOT_ID = 'YOUR_BOT_ID'
REGION = 'us-east-1'
ALIAS_NAME = 'DEMO'

# Create a boto3 client
def create_lex_client():
    '''Create Lex v2 client'''
    return boto3.client('lexv2-models', region_name=REGION)

# Defining a function that finds out the Alias ID
def get_alias_id(client, bot_id, alias_name):
    '''Get alias ID from alias name'''
    try:
        response = client.list_bot_aliases(botId=bot_id)
        for alias in response['botAliasSummaries']:
            if alias['botAliasName'] == alias_name:
                return alias['botAliasId']
        return None
    except ClientError:
        return None

# Defining a function that calls CreateBotVersion 
def create_bot_version(client, bot_id):
    '''Create new bot version'''
    try:
        response = client.create_bot_version(
            botId=bot_id,
            description='Demo version',
            botVersionLocaleSpecification={
                'en_US': {
                    'sourceBotVersion': 'DRAFT'
                }
            }
        )
        
        new_version = response['botVersion']
        print(f'Creating version {new_version}...')
        
        # Wait for version to be ready
        while True:
            try:
                status_response = client.describe_bot_version(
                    botId=bot_id,
                    botVersion=new_version
                )
                if status_response['botStatus'] == 'Available':
                    print(f'Version {new_version} ready')
                    return new_version
                elif status_response['botStatus'] == 'Failed':
                    print('Version creation failed')
                    return None
                time.sleep(10)
            except ClientError:
                time.sleep(10)
                continue
                
    except ClientError as e:
        print(f'Error creating version: {e.response["Error"]["Message"]}')
        return None

# This function  calls UpdateBotAlias, provides the bot alias and the new version to attach
def update_bot_alias(client, bot_id, alias_name, new_version):
    '''Update alias to point to new version'''
    try:
        alias_id = get_alias_id(client, bot_id, alias_name)
        if not alias_id:
            print(f'Alias {alias_name} not found')
            return False
        
        client.update_bot_alias(
            botAliasId=alias_id,
            botAliasName=alias_name,
            botId=bot_id,
            description=f'Updated to version {new_version}',
            botVersion=new_version,
            botAliasLocaleSettings={
                'en_US': {
                    'enabled': True
                }
            }
        )
        
        print(f'Alias {alias_name} updated to version {new_version}')
        return True
        
    except ClientError as e:
        print(f'Error updating alias: {e.response["Error"]["Message"]}')
        return False

def main():
    '''Main function'''
    print('Lex Bot Version Manager Demo')
    print('-' * 30)
    
    # Create client
    client = create_lex_client()
    
    # Get bot info
    try:
        bot_info = client.describe_bot(botId=BOT_ID)
        print(f'Bot: {bot_info["botName"]} ({BOT_ID})')
    except ClientError:
        print('Error: Check your BOT_ID configuration')
        return
    
    # Create new version
    new_version = create_bot_version(client, BOT_ID)
    if not new_version:
        print('Failed to create version')
        return
    
    # Update alias
    if update_bot_alias(client, BOT_ID, ALIAS_NAME, new_version):
        print(f'Success! {ALIAS_NAME} alias now points to version {new_version}')
    else:
        print('Failed to update alias')

if __name__ == '__main__':
    main()
