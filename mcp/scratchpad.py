"""Module to give an LLM local notes"""

NOTES="notes.md"


def read_notes(filepath=NOTES):
    """From a markdown file denoted by filepath
        read the text contents and return as string
        if no file exists return a message saying so, otherwise return its contents
    """
    content = "placeholder"
    return

def append_to_notes(filepath=NOTES):
    """ Append to the file denoted by filepath, if the file does not exist, create it. """
    pass

def clear_notes(filepath=NOTES):
    """
    delete the notes file if it exists, return success message
    """
    pass
