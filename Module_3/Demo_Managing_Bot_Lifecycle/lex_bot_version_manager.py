#!/usr/bin/env python3
"""
Amazon Lex v2 Bot Version and Alias Management Script

This script demonstrates how to:
1. Create a new bot version using CreateBotVersion
2. Update the PROD alias to point to the new version using UpdateBotAlias

Prerequisites:
- AWS CloudShell (which includes Python 3, boto3, and admin credentials)
- A Lex v2 bot already created in the console (following Part 1 of the tutorial)
"""

import boto3
import time
from botocore.exceptions import ClientError

# Configuration - Update these values for your bot
BOT_ID = "YOUR_BOT_ID"  # Replace with your actual bot ID from the console
BOT_NAME = "SimpleBot"  # The name of your bot
REGION = "us-east-1"  # Replace with your preferred AWS region
ALIAS_NAME = "DEMO"  # The alias we created in the console

def create_lex_client():
    """
    Create and return a Lex v2 client
    """
    try:
        # Create the Lex v2 client (lexv2-models service)
        client = boto3.client('lexv2-models', region_name=REGION)
        print(f"Successfully created Lex v2 client for region: {REGION}")
        return client
    except Exception as e:
        print(f"Error creating Lex client: {str(e)}")
        return None

def get_alias_id(client, bot_id, alias_name):
    """
    Get the actual alias ID for the given alias name
    """
    try:
        response = client.list_bot_aliases(botId=bot_id)
        for alias in response['botAliasSummaries']:
            if alias['botAliasName'] == alias_name:
                return alias['botAliasId']
        return None
    except ClientError as e:
        print(f"Error getting alias ID: {e.response['Error']['Message']}")
        return None

def create_bot_version(client, bot_id, description="New version created via SDK"):
    """
    Create a new version of the bot using CreateBotVersion API
    
    Args:
        client: Boto3 Lex v2 client
        bot_id: The ID of the bot
        description: Description for the new version
    
    Returns:
        str: The new version number if successful, None if failed
    """
    try:
        print(f"Creating new version for bot: {bot_id}")
        
        # Call the CreateBotVersion API
        response = client.create_bot_version(
            botId=bot_id,
            description=description,
            # botVersionLocaleSpecification is optional but recommended
            botVersionLocaleSpecification={
                'en_US': {  # English US locale
                    'sourceBotVersion': 'DRAFT'  # Create version from DRAFT
                }
            }
        )
        
        # Extract the new version number from the response
        new_version = response['botVersion']
        bot_status = response['botStatus']
        
        print(f"Bot version creation initiated: {new_version}")
        print(f"Status: {bot_status}")
        
        # Wait for the version to be available
        print("Waiting for version to be ready...")
        wait_for_bot_version_available(client, bot_id, new_version)
        
        return new_version
        
    except ClientError as e:
        print(f"Error creating bot version: {e.response['Error']['Message']}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

def wait_for_bot_version_available(client, bot_id, version, max_wait_time=300):
    """
    Wait for the bot version to become available
    
    Args:
        client: Boto3 Lex v2 client
        bot_id: The ID of the bot
        version: The version to wait for
        max_wait_time: Maximum time to wait in seconds
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = client.describe_bot_version(
                botId=bot_id,
                botVersion=version
            )
            
            status = response['botStatus']
            print(f"Version {version} status: {status}")
            
            if status == 'Available':
                print(f"Version {version} is now available!")
                return True
            elif status == 'Failed':
                print(f"Version {version} creation failed!")
                return False
            
            # Wait before checking again
            time.sleep(15)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                print(f"Version {version} still being created...")
                time.sleep(15)
                continue
            else:
                print(f"Error checking version status: {e.response['Error']['Message']}")
                return False
        except Exception as e:
            print(f"Unexpected error checking version: {str(e)}")
            return False
    
    print(f"Timeout waiting for version {version} to become available")
    return False

def update_bot_alias(client, bot_id, alias_name, new_version):
    """
    Update the bot alias to point to a new version using UpdateBotAlias API
    
    Args:
        client: Boto3 Lex v2 client
        bot_id: The ID of the bot
        alias_name: The name of the alias to update
        new_version: The version number to point the alias to
    
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # First, get the actual alias ID
        alias_id = get_alias_id(client, bot_id, alias_name)
        if not alias_id:
            print(f"Could not find alias '{alias_name}'")
            return False
        
        print(f"Updating alias '{alias_name}' (ID: {alias_id}) to point to version {new_version}")
        
        # Call the UpdateBotAlias API with correct parameters
        response = client.update_bot_alias(
            botAliasId=alias_id,
            botAliasName=alias_name,
            botId=bot_id,
            description=f"Updated to version {new_version} via SDK",
            # Specify which version this alias should point to
            botVersion=new_version,
            botAliasLocaleSettings={
                'en_US': {
                    'enabled': True
                }
            }
        )
        
        # Extract information from the response
        alias_status = response['botAliasStatus']
        updated_version = response['botVersion']
        
        print(f"Alias update initiated successfully!")
        print(f"Alias status: {alias_status}")
        print(f"Alias now points to version: {updated_version}")
        
        return True
        
    except ClientError as e:
        print(f"Error updating bot alias: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

def get_bot_info(client, bot_id):
    """
    Get basic information about the bot
    """
    try:
        response = client.describe_bot(botId=bot_id)
        print(f"Bot Name: {response['botName']}")
        print(f"Bot Description: {response.get('description', 'No description')}")
        print(f"Bot ID: {response['botId']}")
        print(f"Bot Status: {response['botStatus']}")
        return True
    except ClientError as e:
        print(f"Error getting bot info: {e.response['Error']['Message']}")
        print("Make sure to update the BOT_ID variable with your actual bot ID")
        return False

def main():
    """
    Main function that orchestrates the bot version and alias management
    """
    print("Starting Amazon Lex v2 Bot Version Management")
    print("=" * 60)
    
    # Validate configuration
    if BOT_ID == "YOUR_BOT_ID_HERE":
        print("Please update the BOT_ID variable with your actual bot ID")
        print("You can find your bot ID in the Lex console URL or bot details")
        return
    
    # Create Lex client
    client = create_lex_client()
    if not client:
        return
    
    # Get bot information
    print("\nBot Information:")
    print("-" * 30)
    if not get_bot_info(client, BOT_ID):
        return
    
    # Create a new bot version
    print(f"\nCreating New Bot Version:")
    print("-" * 30)
    new_version = create_bot_version(
        client, 
        BOT_ID, 
        f"Version created on {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    if not new_version:
        print("Failed to create new version. Exiting.")
        return
    
    # Update the PROD alias to point to the new version
    print(f"\nUpdating Alias:")
    print("-" * 30)
    success = update_bot_alias(client, BOT_ID, ALIAS_NAME, new_version)
    
    if success:
        print(f"\nSuccess! Your '{ALIAS_NAME}' alias now points to version {new_version}")
        print("You can now test your bot using the updated alias")
    else:
        print(f"\nFailed to update alias '{ALIAS_NAME}'")
    
    print("\n" + "=" * 60)
    print("Script completed!")

if __name__ == "__main__":
    main()
