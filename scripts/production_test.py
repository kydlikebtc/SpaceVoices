import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.services.twitter_browser_service import TwitterBrowserService
from app.services.voice_generator import ElevenLabsGenerator
from app.services.feature_flags import FeatureFlags

async def test_browser_login():
    """Test browser login with provided credentials."""
    # Start with just one account for testing
    account_prefix = "TWITTER_BROWSER_1"
    account_name = "Host Account"
    
    print(f"\nTesting {account_name}...")
    service = None
    try:
        # Set up service with retry
        for attempt in range(3):
            try:
                service = TwitterBrowserService()
                await service.setup_browser()
                break
            except Exception as e:
                print(f"Setup attempt {attempt + 1} failed: {str(e)}")
                if service:
                    service.cleanup()
                if attempt < 2:
                    await asyncio.sleep(5)
                else:
                    raise
        
        username = os.getenv(f"{account_prefix}_USERNAME")
        password = os.getenv(f"{account_prefix}_PASSWORD")
        
        if not username or not password:
            print(f"Missing credentials for {account_name}")
            return
            
        print(f"Attempting login for {username}...")
        
        # Try login with timeout
        try:
            async with asyncio.timeout(30):  # 30 second timeout
                success = await service.login(username, password)
        except asyncio.TimeoutError:
            print("Login attempt timed out")
            return
        
        if success:
            print(f"Login successful for {account_name}")
            # Test Space creation
            print("\nTesting Space creation...")
            try:
                async with asyncio.timeout(30):
                    space_id = await service.create_space(f"Test Space from {account_name}")
                if space_id:
                    print(f"Space created successfully with ID: {space_id}")
                    # End the space
                    print("\nEnding test Space...")
                    try:
                        async with asyncio.timeout(30):
                            if await service.end_space(space_id):
                                print("Space ended successfully")
                            else:
                                print("Failed to end Space")
                    except asyncio.TimeoutError:
                        print("Space end attempt timed out")
                else:
                    print("Failed to create Space")
            except asyncio.TimeoutError:
                print("Space creation attempt timed out")
        else:
            print(f"Login failed for {account_name}")
    except Exception as e:
        print(f"Browser automation error for {account_name}: {str(e)}")
    finally:
        if service:
            service.cleanup()

async def test_voice_generation():
    """Test voice generation with ElevenLabs."""
    print("\nTesting voice generation...")
    generator = ElevenLabsGenerator()
    try:
        audio = await generator.generate_voice(
            "Hello, this is a test message for SpaceVoices.",
            "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice ID
        )
        print("Voice generation successful")
        audio.close()  # Close the temporary file
    except Exception as e:
        print(f"Voice generation error: {str(e)}")

async def main():
    """Run all production tests."""
    print("Starting production tests...")
    
    # Enable browser automation
    flags = FeatureFlags()
    print(f"\nFeature flags status:")
    print(f"Browser automation: {flags.is_enabled('use_browser_automation')}")
    print(f"Browser auto retry: {flags.is_enabled('browser_auto_retry')}")
    
    # Run tests
    await test_browser_login()
    await test_voice_generation()

if __name__ == "__main__":
    asyncio.run(main())
