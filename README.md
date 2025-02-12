# SpaceVoices

A powerful system that converts text scripts into multi-voice podcasts and automatically distributes them through Twitter Spaces. This project uses AI voice generation and NLP optimization to create engaging, multi-character audio content while maintaining transparency about its AI-generated nature.

## Features

- **Script to Podcast Conversion**
  - Custom script format supporting multiple characters
  - NLP-optimized dialogue flow with sentiment analysis
  - Intelligent pause timing based on context
  - Character-specific voice profiles
  - Background music integration

- **AI Voice Generation**
  - High-quality voice synthesis using ElevenLabs
  - Unique voice profiles for each character
  - Natural-sounding conversations
  - Sentiment-aware voice modulation

- **Audio Processing**
  - Professional audio mixing
  - Background music support
  - Automatic audio cleanup and optimization
  - Dynamic pause adjustment

- **Twitter Spaces Integration**
  - Multi-account character support
  - Real-time interaction and monitoring
  - Automated Space creation and management
  - Scheduled broadcasting support
  - Clear AI-generated content disclosure

## Setup

1. Clone the repository:
```bash
git clone https://github.com/kydlikebtc/SpaceVoices.git
cd SpaceVoices
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up environment variables:
Create a `.env` file based on `.env.example` and fill in your API keys. For multi-account support, configure each character's Twitter credentials:

```bash
# Host Account (Required)
TWITTER_ACCOUNT_1_CHARACTER=Host
TWITTER_ACCOUNT_1_API_KEY=your_api_key_here
TWITTER_ACCOUNT_1_API_SECRET=your_api_secret_here
TWITTER_ACCOUNT_1_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCOUNT_1_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# Character Accounts (Optional)
TWITTER_ACCOUNT_2_CHARACTER=Alice
TWITTER_ACCOUNT_2_API_KEY=your_api_key_here
TWITTER_ACCOUNT_2_API_SECRET=your_api_secret_here
TWITTER_ACCOUNT_2_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCOUNT_2_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

## Usage

1. Create a script:
```json
{
  "title": "My First Podcast",
  "characters": [
    {
      "name": "Host",
      "voice_profile": "voice_id_1"
    },
    {
      "name": "Guest",
      "voice_profile": "voice_id_2"
    }
  ],
  "dialogue": [
    {
      "character": "Host",
      "text": "Welcome to the show!",
      "pause_after": 1.0
    },
    {
      "character": "Guest",
      "text": "Thanks for having me!",
      "pause_after": 0.5
    }
  ]
}
```

2. Generate and publish:
```bash
# Start the server
poetry run uvicorn app.main:app --reload

# Use the API to create and publish content
curl -X POST http://localhost:8000/api/v1/scripts -d @script.json
curl -X POST http://localhost:8000/api/v1/generate/1
curl -X POST http://localhost:8000/api/v1/publish/1
```

## Real-Time Interaction

Monitor and interact with Spaces in real-time using WebSocket connections:

```python
import asyncio
import websockets
import json

async def monitor_space(space_id: str, character: str = "Host"):
    uri = f"ws://localhost:8000/api/v1/spaces/{space_id}/events?character={character}"
    async with websockets.connect(uri) as websocket:
        while True:
            event = await websocket.recv()
            data = json.loads(event)
            print(f"Space update: {data}")

# Usage
asyncio.run(monitor_space("your_space_id", "Alice"))
```

## Important Notes

- **API Keys**: All voice generation and Twitter API keys must be stored securely in environment variables
- **Storage**: Audio files are stored temporarily and automatically cleaned up after processing
- **Rate Limits**: The system implements error handling for API rate limits
- **AI Disclosure**: All Twitter Spaces automatically include clear disclosure of AI-generated content
- **Content Moderation**: Implement appropriate content filtering before publishing
- **Resource Usage**: NLP optimization features require significant CPU/memory resources
- **Account Management**: Multiple Twitter accounts need secure credential management
- **WebSocket Connections**: Implement proper error handling for real-time connections

## Development

Run tests:
```bash
poetry run pytest
```

## License

MIT License - See LICENSE file for details
