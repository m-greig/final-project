import csv


def str_to_int(s: str) -> int|str:
    """
    Returns an integer. Converts 's' into an integer if possible.
    """
    try:
        return int(s)
    except ValueError:
        return s


def str_to_float(s: str) -> float|str:

    """
    Returns a float. Converts 's' into a float if possible.
    """
    try:
        return float(s)
    except ValueError:
        return s
    

def read_csv_file(filename: str) -> list[list[str]]:
    """
    Returns a nested list representing the data in the file at
    'filename'
    """
    file_data = []
    with open(filename, 'r') as file:
        file_reader = csv.reader(file)
        for line in file_reader:
            file_data.append(line)
    return file_data