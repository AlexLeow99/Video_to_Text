from moviepy.editor import VideoFileClip
from pydub import AudioSegment
import tempfile
import os


def convert_to_mp4(input_file, output_file):
    # 直接使用文件路径
    video_clip = VideoFileClip(input_file)
    video_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")

def convert_to_wav(input_file, output_file):
    # 直接使用AudioClip对象
    mp4_video = VideoFileClip(input_file)
    mp4_audio = mp4_video.audio
    mp4_audio.write_audiofile(output_file)