# SpaceVoices

A powerful system that converts text scripts into multi-voice podcasts and automatically distributes them through Twitter Spaces. This project uses AI voice generation and NLP optimization to create engaging, multi-character audio content while maintaining transparency about its AI-generated nature.

## Features

- **Script to Podcast Conversion**
  - Custom script format supporting multiple characters
  - NLP-optimized dialogue flow with sentiment analysis
  - Intelligent pause timing based on context
  - Character-specific voice profiles
  - Background music integration
  - Resource monitoring and limits

- **AI Voice Generation**
  - High-quality voice synthesis using ElevenLabs
  - Unique voice profiles for each character
  - Natural-sounding conversations
  - Sentiment-aware voice modulation
  - Configurable rate limiting

- **Audio Processing**
  - Professional audio mixing
  - Background music support
  - Automatic audio cleanup and optimization
  - Dynamic pause adjustment
  - Memory usage optimization

- **Twitter Spaces Integration**
  - Multi-account character support
  - Real-time interaction and monitoring
  - Automated Space creation and management
  - Scheduled broadcasting support
  - Clear AI-generated content disclosure
  - WebSocket-based real-time updates

- **System Features**
  - Resource monitoring and management
  - API rate limiting with backoff
  - WebSocket connection health monitoring
  - Secure credential management
  - Feature flag system for gradual rollout
  - Encrypted configuration support

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

## Real-Time Monitoring

Monitor and interact with Spaces in real-time using WebSocket connections:

```python
import asyncio
import websockets
import json

async def monitor_space(space_id: str, character: str = "Host"):
    """Monitor a Space's events in real-time."""
    uri = f"ws://localhost:8000/api/v1/spaces/{space_id}/events?character={character}"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to Space {space_id}")
                
                while True:
                    event = await websocket.recv()
                    data = json.loads(event)
                    
                    if data["type"] == "ping":
                        # Respond to heartbeat
                        await websocket.send(json.dumps({"type": "pong"}))
                        continue
                    
                    print(f"Space update: {data}")
                    
        except websockets.ConnectionClosed:
            print("Connection lost. Reconnecting...")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error: {str(e)}")
            await asyncio.sleep(5)

# Usage
asyncio.run(monitor_space("your_space_id", "Alice"))
```

### Event Types

The WebSocket endpoint emits the following event types:

1. `space_update`: Space status updates
```json
{
    "type": "space_update",
    "data": {
        "space_id": "123",
        "state": "live",
        "participant_count": 10
    }
}
```

2. `ping`: Heartbeat event (every 30 seconds)
```json
{
    "type": "ping"
}
```

### Connection Management

- The connection includes automatic reconnection with exponential backoff
- Heartbeat mechanism ensures connection health
- Events are delivered in real-time with minimal latency
- Multiple clients can monitor the same Space

## Technical Details

### Resource Management
- CPU and memory usage monitoring
- Configurable resource limits
- Process count tracking
- Automatic cleanup of temporary files
- Memory optimization for large scripts

### Rate Limiting
- Sliding window rate limiting
- Configurable window size and request limits
- Per-character rate tracking
- Exponential backoff for retries
- Rate limit status monitoring

### Security
- Encrypted configuration storage
- Secure credential management
- API key rotation support
- Audit logging capabilities
- Environment-based configuration

### Feature Flags
- Gradual feature rollout
- Environment-based toggles
- Per-feature monitoring
- A/B testing support
- Real-time feature updates

### Important Notes
- **API Keys**: All credentials are stored securely and can be encrypted
- **Storage**: Temporary files are automatically cleaned up
- **Rate Limits**: Built-in protection against API rate limits
- **AI Disclosure**: Automatic AI content disclosure in Spaces
- **Resource Usage**: Configurable resource limits prevent overload
- **Account Management**: Secure multi-account credential handling
- **WebSocket Connections**: Robust error handling with reconnection
- **Monitoring**: Real-time health and performance tracking

## Development

Run tests:
```bash
poetry run pytest
```

## License

MIT License - See LICENSE file for details
