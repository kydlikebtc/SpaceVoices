import ffmpeg
import tempfile
import os
from typing import List, BinaryIO, Optional
from pathlib import Path

class AudioProcessingError(Exception):
    """Custom exception for audio processing failures."""
    pass

class AudioProcessor:
    def __init__(self):
        self.temp_dir = Path(tempfile.mkdtemp())
    
    async def merge_audio_tracks(
        self,
        voice_tracks: List[BinaryIO],
        background_music: Optional[BinaryIO] = None,
        background_volume: float = 0.2
    ) -> BinaryIO:
        """
        Merge multiple voice tracks and optional background music into a single audio file.
        
        Args:
            voice_tracks: List of voice audio file objects
            background_music: Optional background music file object
            background_volume: Volume level for background music (0.0 to 1.0)
            
        Returns:
            BinaryIO: Merged audio file object
        """
        try:
            # Save voice tracks to temporary files
            voice_paths = []
            for i, track in enumerate(voice_tracks):
                temp_path = self.temp_dir / f"voice_{i}.mp3"
                with open(temp_path, "wb") as f:
                    f.write(track.read())
                voice_paths.append(temp_path)
            
            # Create ffmpeg input streams for voice tracks
            input_streams = [ffmpeg.input(str(path)) for path in voice_paths]
            
            # Add background music if provided
            if background_music:
                bg_path = self.temp_dir / "background.mp3"
                with open(bg_path, "wb") as f:
                    f.write(background_music.read())
                bg_stream = ffmpeg.input(str(bg_path)).filter('volume', background_volume)
                input_streams.append(bg_stream)
            
            # Create output file
            output_path = self.temp_dir / "output.mp3"
            
            # Merge all streams
            merged = ffmpeg.concat(*input_streams, v=0, a=1)
            
            # Run ffmpeg
            merged.output(str(output_path), acodec='libmp3lame', ar='44100').overwrite_output().run(capture_stdout=True, capture_stderr=True)
            
            # Read the output file and return it as a file object
            output_file = tempfile.TemporaryFile()
            with open(output_path, "rb") as f:
                output_file.write(f.read())
            output_file.seek(0)
            
            return output_file
            
        except ffmpeg.Error as e:
            raise AudioProcessingError(f"FFmpeg error: {e.stderr.decode()}")
        except Exception as e:
            raise AudioProcessingError(f"Unexpected error during audio processing: {str(e)}")
        finally:
            # Cleanup temporary files
            for file in self.temp_dir.glob("*"):
                try:
                    os.remove(file)
                except:
                    pass
            try:
                os.rmdir(self.temp_dir)
            except:
                pass
