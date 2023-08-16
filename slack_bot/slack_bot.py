import os
import asyncio
import aiohttp
from pydantic import BaseModel
from fastapi import FastAPI, Request
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import toml
import datetime
import concurrent.futures
import re

import json

# Read the bot token from environment variable or config file
try:
    SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
    TEXT_GENERATION_HOST = os.environ['TEXT_GENERATION_HOST']
    PORT = os.environ['PORT']
    config = {'slack_bot_token': SLACK_BOT_TOKEN, 'text_generation_host': TEXT_GENERATION_HOST, 'port': PORT}
except:
    # Alternatively, load the bot token from a config file
    config = toml.load('../config/config.toml')
    SLACK_BOT_TOKEN = config['slack_bot_token']
    TEXT_GENERATION_HOST = config['text_generation_host']
    PORT = config['port']

SERVICE_URI = f"http://{TEXT_GENERATION_HOST}:{PORT}"

# Set up the Slack client
client = WebClient(token=SLACK_BOT_TOKEN)
SLACK_BOT_USER_ID = client.auth_test()['user_id']
print('connected to slack bot', SLACK_BOT_USER_ID)

# Set up FastAPI web server
app = FastAPI()

def get_timestamp():
    return datetime.datetime.now()

class Event(BaseModel):
    type: str
    user: str
    text: str
    client_msg_id: str | None
    team: str | None
    channel: str
    event_ts: str
    channel_type: str | None

# Define executor
executor = concurrent.futures.ThreadPoolExecutor()

def send_message(channel, text, response_id):
    try:
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            },
            {
                "type": "actions",
                "block_id": f"vote:{response_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👍",
                            "emoji": True
                        },
                        "value": "upvote",
                        "action_id": "upvote_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "👎",
                            "emoji": True
                        },
                        "value": "downvote",
                        "action_id": "downvote_button"
                    }
                ]
            }
        ]
        
        client.chat_postMessage(channel=channel, text=text, blocks=blocks)
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")


async def fetch_generated_text(session, url, payload, headers):
    print(f'{get_timestamp()} – Fetching response from LLM…')
    async with session.post(url, json=payload, headers=headers) as response:
        return await response.json()

async def generate_text(event: Event):
    input_prompt = re.sub(r'<@.*?>', '', event.get('text')).strip()  
    channel_id = event.get('channel')
    headers = {'Content-type': 'application/json'}
    payload = {'input_prompt': input_prompt}

    async with aiohttp.ClientSession() as session:
        response = await fetch_generated_text(session, f'{SERVICE_URI}/generate_text', payload, headers)
        generated_text = response['generated_text']
        response_id = response['response_id']  
        
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, send_message, channel_id, generated_text, response_id)
    print(f"{get_timestamp()} – Can't wait for response, returning immediately.")
    return '', 200

@app.post("/slack/events")
async def slack_events(request: Request):
    payload = await request.json()

    if payload.get('challenge'):
        challenge = payload.get('challenge')
        return challenge, 200, {'Content-Type': 'text/plain'}
    
    event = payload.get('event')

    if event:
        user_id = event.get('user')
        # Ignore bot's own messages
        if user_id != SLACK_BOT_USER_ID:
            channel_type = event.get('channel_type', '')
            text = event.get('text', '')
            is_instant_message = channel_type == "im"
            
            if is_instant_message or f'<@{SLACK_BOT_USER_ID}>' in text:
                print(f'{get_timestamp()} – Received {"instant message" if is_instant_message else "mention"}…')
                if event.get('type') in ('message', 'app_mention'):
                    asyncio.create_task(generate_text(event))

    return {"status": 200}

@app.post("/slack/interactive")
async def slack_interactive(request: Request):
    result = await request.form()
    payload = json.loads(result["payload"])
    block_id = payload['actions']['block_id']
    channel_id = payload['channel']['id']
    actions = payload['actions']
    # Extract the response_id from the callback_id field in the Slack payload
    response_id = int(block_id.split(":")[1])
    
    # Determine the vote based on the button clicked
    vote_value = None
    for action in actions:
        if action['value'] == 'upvote':
            vote_value = 1
        elif action['value'] == 'downvote':
            vote_value = -1

    # Now, make a request to the run_inference_api.py to update the vote
    if vote_value:
        async with aiohttp.ClientSession() as session:
            payload = {
                'vote': vote_value,
                'response_id': response_id
            }
            headers = {'Content-type': 'application/json'}
            
            await session.post(f'{SERVICE_URI}/vote', json=payload, headers=headers)
            client.chat_postMessage(channel=channel_id, text='Thanks for your vote!')

    return {"status": 200}
