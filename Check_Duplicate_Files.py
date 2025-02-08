import os
import sys
import hashlib

def get_file_hash(file_path, hash_algo=hashlib.md5):
    hasher = hash_algo()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def find_duplicate_files(directory):
    hash_map = {}
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            sys.stdout.write(f"Checking: {file_path}    \r")
            sys.stdout.flush()
            file_hash = get_file_hash(file_path)
            if file_hash:
                if file_hash in hash_map:
                    hash_map[file_hash].append(file_path)
                    print(f"Duplicate: {hash_map[file_hash][0]} -> {file_path}")
                else:
                    hash_map[file_hash] = [file_path]

    print("\n")
    total_duplicates = sum(len(v) - 1 for v in hash_map.values() if len(v) > 1)
    total_groups = sum(1 for v in hash_map.values() if len(v) > 1)
    print(f"Total duplicate files: {total_duplicates}, Total duplicate groups: {total_groups}")
    files_to_delete = []
    if total_duplicates > 0:
        print("Summary of duplicate files:")
        for file_hash, file_list in hash_map.items():
            if len(file_list) > 1:
                print(f"{file_hash}: {', '.join(file_list)}")
                files_to_delete.extend(file_list[1:])

        print(f"Total files to be deleted: {len(files_to_delete)}")
        confirm = input("Do you want to delete duplicate files? (y/n): ")
        if confirm.lower() == 'y':
            for file in files_to_delete:
                try:
                    os.remove(file)
                    print(f"Deleted: {file}")
                except Exception as e:
                    print(f"Error deleting {file}: {e}")
        else:
            print("Duplicate file deletion canceled.")
    else:
        print("No duplicate files found.")

if __name__ == "__main__":
    folder_path = input("Enter the directory path to check: ")
    if os.path.isdir(folder_path):
        find_duplicate_files(folder_path)
    else:
        print("Invalid directory.")