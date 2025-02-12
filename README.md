# SpaceVoices

A powerful system that converts text scripts into multi-voice podcasts and automatically distributes them through Twitter Spaces. This project uses AI voice generation to create engaging, multi-character audio content while maintaining transparency about its AI-generated nature.

## Features

- **Script to Podcast Conversion**
  - Custom script format supporting multiple characters
  - Natural dialogue flow with configurable pauses
  - Character-specific voice profiles
  - Background music integration

- **AI Voice Generation**
  - High-quality voice synthesis using ElevenLabs
  - Unique voice profiles for each character
  - Natural-sounding conversations

- **Audio Processing**
  - Professional audio mixing
  - Background music support
  - Automatic audio cleanup and optimization

- **Twitter Spaces Integration**
  - Automated Space creation and management
  - Scheduled broadcasting support
  - Clear AI-generated content disclosure
  - Multi-account character support

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
Create a `.env` file based on `.env.example` and fill in your API keys:
```
ELEVENLABS_API_KEY=your_key_here
TWITTER_API_KEY=your_key_here
TWITTER_API_SECRET=your_key_here
TWITTER_ACCESS_TOKEN=your_key_here
TWITTER_ACCESS_TOKEN_SECRET=your_key_here
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

## Important Notes

- **API Keys**: All voice generation and Twitter API keys must be stored securely in environment variables
- **Storage**: Audio files are stored temporarily and automatically cleaned up after processing
- **Rate Limits**: The system implements error handling for API rate limits
- **AI Disclosure**: All Twitter Spaces automatically include clear disclosure of AI-generated content
- **Content Moderation**: Implement appropriate content filtering before publishing

## Development

Run tests:
```bash
poetry run pytest
```

## License

MIT License - See LICENSE file for details
