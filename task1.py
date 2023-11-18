from pathlib import Path
import concurrent.futures
import time
import sys
import re

TARGET_DIR = ''
SEPARATOR_SYMBOL = '_'

# Supported file extension by sorted by type
EXT_BY_TYPE = {
    'videos': ('MP4', 'AVI', 'MKV', 'MOV', 'WMV',
               'FLV', 'WEBM', 'MPEG', 'MPG', '3GP'),
    'pictures': ('JPG', 'JPEG', 'PNG', 'GIF', 'BMP',
                 'SVG', 'WEBP', 'TIF', 'TIFF', 'ICO'),
    'documents': ('DOC', 'DOCX', 'PDF', 'RTF', 'ODT',
                  'ODS', 'ODP', 'PPT', 'PPTX', 'XLS',
                  'XLSX', 'CSV', 'XML', 'HTML', 'HTM', 'TEX'),
    'music': ('MP3', 'WAV', 'WMA', 'OGG', 'FLAC', 'AAC',
              'AMR', 'M4A', 'M3U', 'MID'),
    'archives': ('ZIP', '7Z', 'TAR', 'GZ',
                 'BZ2', 'XZ', 'TGZ', 'TBZ2'),
    'notes': ('', 'MD', 'TXT'),
    'iso-img': ('ISO', 'IMG'),
}

# Transliteraton dictionary
TRANS = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd',
    'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'y',
    'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n',
    'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
    'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch',
    'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya', 'є': 'ye', 'і': 'i',
    'ї': 'ji', 'ґ': 'g',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D',
    'Е': 'E', 'Ё': 'E', 'Ж': 'Zh', 'З': 'Z', 'И': 'Y',
    'Й': 'I', 'К': 'K', 'Л': 'L', 'М': 'M', 'Н': 'N',
    'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T',
    'У': 'U', 'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch',
    'Ш': 'Sh', 'Щ': 'Shch', 'Ъ': '', 'Ы': 'Y', 'Ь': '',
    'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya', 'Є': 'Ye', 'І': 'I',
    'Ї': 'Ji', 'Ґ': 'G'
}

RUNTIME_DATA = {
    'files_found': [],
    'files_found_by_type': {},
    'extensions_found': {'known': set(), 'unknown': set()},
}


def dir_scan(target_dir: Path) -> list:
    path = Path(target_dir)
    directories = []
    for item in path.iterdir():
        if item.is_dir():
            directories.append(item)
            directories.extend(dir_scan(item))
    return directories


def file_scan(target_dir: Path) -> list:
    path = Path(target_dir)
    files = []
    for item in path.iterdir():
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            files.extend(file_scan(item))
    RUNTIME_DATA["files_found"] = files
    RUNTIME_DATA["total_files_found"] = len(files)
    return files


def normalize(name: str) -> str:
    file_name, file_ext = Path(name).stem, Path(name).suffix
    normalized_name = re.sub(r'[^\w\s.-]', '', file_name)
    normalized_name = normalized_name.translate(TRANS)
    normalized_name = re.sub(r' +', SEPARATOR_SYMBOL, normalized_name)
    normalized_name = re.sub(r'[_-]+', SEPARATOR_SYMBOL, normalized_name)
    normalized_name = normalized_name.strip(SEPARATOR_SYMBOL)
    normalized_filename = f"{normalized_name}{file_ext}"
    return normalized_filename.lower()


def rename_duplicates(path: Path) -> Path:
    name_stem = path.stem
    file_number = 1
    while path.exists():
        new_destination = path.with_stem(
            f"{name_stem}{SEPARATOR_SYMBOL}{file_number}")
        file_number += 1
        path = new_destination
    return path


def extension_sort(files: list) -> None:
    categories = list(EXT_BY_TYPE.keys())
    categories.append("other")
    extensions_found = RUNTIME_DATA["extensions_found"]
    files_found_by_type = RUNTIME_DATA["files_found_by_type"]
    for file in files:
        if file.parts[1] in categories:
            continue
        ext = file.suffix.lstrip(".").upper()
        is_found = False
        for category, extensions in EXT_BY_TYPE.items():
            if ext in extensions:
                extensions_found["known"].add(ext)
                file_list = files_found_by_type.get(category, [])
                file_list.append(file)
                files_found_by_type[category] = file_list
                is_found = True
                break
        if not is_found:
            extensions_found["unknown"].add(ext)
            category = "other"
            file_list = files_found_by_type.get(category, [])
            file_list.append(file)
            files_found_by_type[category] = file_list


def move_files(target_dir: Path) -> None:
    found_files_by_type = RUNTIME_DATA["files_found_by_type"]
    for file_type, files in found_files_by_type.items():
        destination_path = Path(target_dir).joinpath(file_type)
        if not destination_path.exists():
            destination_path.mkdir()
        for file in files:
            original_path = file
            new_file_path = destination_path.joinpath(normalize(file.name))
            try:
                new_file_path = rename_duplicates(new_file_path)
                file.rename(new_file_path)
            except Exception as e:
                print(f'[-] Error: Failed to move "{new_file_path}": {e}')


def purge_empty(source_target_dir: Path) -> None:
    target_dir_list = dir_scan(source_target_dir)
    target_dir_list.reverse()
    for target_dir in target_dir_list:
        if target_dir.exists() and target_dir.is_dir() and not any(target_dir.glob("*")):
            try:
                target_dir.rmdir()
            except Exception as e:
                print(
                    f'[-] Error: Failed to remove directory "{target_dir}". {e}')


def main():
    try:
        if len(sys.argv) == 2:
            TARGET_DIR = Path(sys.argv[1])
            if not TARGET_DIR.exists():
                print(f'[-] Error. TARGET_DIR does not exist: "{TARGET_DIR}"')
                exit(1)
        else:
            print("""[-] Error. Invalid input\n
            USAGE:
            \tsort.py TARGET_DIR/\n
            EXAMPLE:
            \tsort.py /home/user1/Desktop/Unsorted\n
            """)
            exit(1)
    except Exception as e:
        print(f'[-] Error: {e}')

    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(file_scan, [TARGET_DIR]))
        list(executor.map(dir_scan, [TARGET_DIR]))
        extension_sort(RUNTIME_DATA["files_found"])
        list(executor.map(move_files, [TARGET_DIR]))
        purge_empty(TARGET_DIR)

    finish = time.perf_counter()
    print(f'Finished in {round(finish-start, 2)} second(s)')


if __name__ == "__main__":
    main()
