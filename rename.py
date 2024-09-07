import argparse
import logging
from pathlib import Path

def get_directory_from_args():
    parser = argparse.ArgumentParser(description="Rename video files in a specified directory")
    parser.add_argument('directory', type=str, help='Path to the directory containing video files')
    args = parser.parse_args()
    return Path(args.directory)

def rename_files(directory):
    if not directory.exists() or not directory.is_dir():
        logging.error(f"The directory {directory} does not exist or is not a directory.")
        return

    files = list(directory.iterdir())
    video_files = [f for f in files if f.suffix.lower() in {'.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv', '.m4v', '.mpeg', '.mpg'}]

    video_files.sort()

    for index, file_path in enumerate(video_files):
        new_name = f"{index + 1:04d}{file_path.suffix}"
        new_path = directory / new_name

        if new_path.exists():
            logging.warning(f"File already exists: {new_path}. Skipping...")
            continue

        try:
            file_path.rename(new_path)
            logging.info(f"Renamed: {file_path} -> {new_path}")
        except Exception as e:
            logging.error(f"Failed to rename: {file_path} -> {new_name}. Error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    directory_path = get_directory_from_args()
    rename_files(directory_path)