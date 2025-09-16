#!/usr/bin/env python3
"""
Test script for FFprobe functionality with Vimeo streams.

This script tests FFprobe analysis of Vimeo stream URLs to verify
that the stream monitoring system can properly analyze streams.
"""

import json
import subprocess
import sys
import time
from typing import Dict, Optional


def test_ffprobe_availability() -> bool:
    """Test if ffprobe is available on the system."""
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ FFprobe is available")
            print(f"Version: {result.stdout.split()[2]}")
            return True
        else:
            print("❌ FFprobe command failed")
            return False
    except FileNotFoundError:
        print("❌ FFprobe not found. Please install ffmpeg/ffprobe.")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFprobe command timed out")
        return False


def analyze_stream_with_ffprobe(url: str, timeout: int = 10) -> Optional[Dict]:
    """Analyze a stream URL using ffprobe.
    
    Args:
        url: Stream URL to analyze
        timeout: Timeout in seconds
        
    Returns:
        Stream information dictionary or None if analysis failed
    """
    try:
        print(f"🔍 Analyzing stream: {url[:50]}...")
        
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-timeout", str(timeout * 1000000),  # Convert to microseconds
            url
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                print("✅ Stream analysis successful")
                return data
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON output: {e}")
                print(f"Raw output: {result.stdout[:200]}...")
                return None
        else:
            print(f"❌ FFprobe failed with return code {result.returncode}")
            print(f"Error: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"❌ FFprobe analysis timed out after {timeout} seconds")
        return None
    except Exception as e:
        print(f"❌ Unexpected error during analysis: {e}")
        return None


def extract_stream_info(ffprobe_data: Dict) -> Dict:
    """Extract useful stream information from ffprobe output.
    
    Args:
        ffprobe_data: Raw ffprobe JSON output
        
    Returns:
        Extracted stream information
    """
    info = {
        "bitrate": 0,
        "width": 0,
        "height": 0,
        "framerate": 0,
        "audio_channels": 0,
        "audio_sample_rate": 0,
        "duration": 0,
        "format_name": "unknown"
    }
    
    try:
        # Extract format information
        if "format" in ffprobe_data:
            format_info = ffprobe_data["format"]
            info["bitrate"] = int(format_info.get("bit_rate", 0)) // 1000  # Convert to kbps
            info["duration"] = float(format_info.get("duration", 0))
            info["format_name"] = format_info.get("format_name", "unknown")
        
        # Extract stream information
        if "streams" in ffprobe_data:
            for stream in ffprobe_data["streams"]:
                codec_type = stream.get("codec_type", "")
                
                if codec_type == "video":
                    info["width"] = int(stream.get("width", 0))
                    info["height"] = int(stream.get("height", 0))
                    
                    # Parse framerate
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        if int(den) > 0:
                            info["framerate"] = float(num) / float(den)
                
                elif codec_type == "audio":
                    info["audio_channels"] = int(stream.get("channels", 0))
                    info["audio_sample_rate"] = int(stream.get("sample_rate", 0))
        
        return info
        
    except Exception as e:
        print(f"❌ Error extracting stream info: {e}")
        return info


def test_with_sample_urls():
    """Test FFprobe with various sample URLs."""
    print("\n🧪 Testing with sample URLs...")
    
    # Test with a public HLS stream (this should work)
    test_urls = [
        "https://demo.unified-streaming.com/k8s/features/stable/video/tears-of-steel/tears-of-steel.ism/.m3u8",
        "https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8"
    ]
    
    for url in test_urls:
        print(f"\n📺 Testing: {url}")
        data = analyze_stream_with_ffprobe(url, timeout=15)
        if data:
            info = extract_stream_info(data)
            print(f"   Bitrate: {info['bitrate']} kbps")
            print(f"   Resolution: {info['width']}x{info['height']}")
            print(f"   Framerate: {info['framerate']:.2f} fps")
            print(f"   Audio: {info['audio_channels']} channels @ {info['audio_sample_rate']} Hz")
            print(f"   Format: {info['format_name']}")
        else:
            print("   ❌ Analysis failed")


def main():
    """Main test function."""
    print("🎬 FFprobe Test Script for Vimeo Monitor")
    print("=" * 50)
    
    # Test FFprobe availability
    if not test_ffprobe_availability():
        sys.exit(1)
    
    # Test with sample URLs
    test_with_sample_urls()
    
    print("\n" + "=" * 50)
    print("✅ FFprobe test completed")
    print("\nNote: Vimeo stream URLs have security tokens that expire quickly.")
    print("For live monitoring, the stream monitor should analyze URLs immediately")
    print("after they are obtained from the Vimeo API.")


if __name__ == "__main__":
    main()
