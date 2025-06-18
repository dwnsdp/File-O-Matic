from pathlib import Path
from typing import List
from dotenv import dotenv_values
import os
from openai import OpenAI

env_vars = dotenv_values(".env")
openai_key = env_vars.get("OPENAI")

client = OpenAI(
    api_key = openai_key,
)

def find_directories(dir: str = ".", max_depth: int = 4) -> List[Path]:
    current_dir = Path(dir).resolve()
    directories = []

    def _recursive_search(path: Path, current_depth: int):
        if current_depth > max_depth:
            return

        try:
            # Only iterate immediate children, don't use rglob
            for item in sorted(path.iterdir()):
                # Skip hidden directories and files
                if item.name.startswith('.'):
                    continue

                if item.is_dir():
                    directories.append(item)
                    # Only recurse if we haven't hit max depth
                    if current_depth < max_depth:
                        _recursive_search(item, current_depth + 1)
        except (PermissionError, OSError):
            print("PERMISSION or OS ERROR")
            pass

    _recursive_search(current_dir, 0)
    return directories





def ask_lmm(dirs, file):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are tasked with sorting files for the user. You must respond with the directory they should be put in and only the directory they should be put in. Do not try to put files in directories that seem like they are in use by an application. Format as a full path from the root, an example: /home/user/Documents. No quotation marks, or any other text, as the algorithm needs only the path. The is a list of available directories: " + str(dirs)},
            {"role": "user", "content": f"Where should I move this file: {file}"}
        ]
    )
    return response.choices[0].message.content


def get_file(directory_path):
    try:
        with os.scandir(directory_path) as entries:
            for entry in entries:
                if entry.is_file():
                    return entry.path

        print(f"No files found in {directory_path}")
        return None

    except FileNotFoundError:
        print(f"Directory not found: {directory_path}")
        return None
    except PermissionError:
        print(f"Permission denied accessing: {directory_path}")
        return None
    except Exception as e:
        print(f"Error accessing directory: {e}")
        return None

def move_file_rename(source_path, destination_path):
    try:
        os.rename(source_path, destination_path)
        print(f"Successfully moved {source_path} to {destination_path}")
        return True
    except FileNotFoundError:
        print(f"Source file not found: {source_path}")
        return False
    except OSError as e:
        print(f"OS Error (might be cross-filesystem): {e}")
        return False
    except Exception as e:
        print(f"Error moving file: {e}")
        return False

def main():
    directory = input("folder to sort files from: ")
    sort_location = input("sort to folders in: ")
    max_depth = int(input("how many folders deep can be found by the AI from your sort location: "))
    recursion_limit = int(input("recursion limit: "))
    dry_run = bool(input("dry run: "))

    dirs = find_directories(sort_location, max_depth=max_depth)
    directory_path = Path(directory)
    dirs = [dir for dir in dirs if not (dir == directory_path or directory_path in dir.parents)]
    for dir in dirs:
        print(dir)
    print("found " + str(len(dirs)) + " directories")

    for i in range(recursion_limit):
        file = get_file(directory)
        print("File to sort = " + str(file))
        sorted_dir = ask_lmm(dirs, file)
        print("New Dir = " + str(sorted_dir))
        filename = str(file).rsplit("/", 1)[1]
        if dry_run:
            print("moved " + str(file) + " to " + str(sorted_dir) + "/" + str(filename))
        move_file_rename(str(file), str(sorted_dir) + "/" + str(filename))
        if  len(os.listdir(directory)) == 0:
            print("Folder fully sorted!")
            exit()
    print("recursion limit reached")
main()
exit()
