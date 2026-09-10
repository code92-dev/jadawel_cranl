# backend/src/jadawel/core/user_files/exceptions.py

- InvalidFileStreamError · class · L6-L7 — class InvalidFileStreamError(Exception)
- FileSizeTooLargeError · class · L10-L15 — class FileSizeTooLargeError(Exception)
- __init__ · method · L13-L15 — def __init__(self, max_size_bytes, *args, **kwargs)
- ActiveContentBlockedUserFileError · class · L18-L19 — class ActiveContentBlockedUserFileError(Exception)
- FileURLCouldNotBeReached · class · L22-L26 — class FileURLCouldNotBeReached(Exception)
- InvalidFileURLError · class · L29-L30 — class InvalidFileURLError(Exception)
- InvalidUserFileNameError · class · L33-L38 — class InvalidUserFileNameError(Exception)
- __init__ · method · L36-L38 — def __init__(self, name, *args, **kwargs)
- UserFileDoesNotExist · class · L41-L49 — class UserFileDoesNotExist(ValidationError)
- __init__ · method · L44-L49 — def __init__(self, file_names_or_ids, *args, **kwargs)
- MaximumUniqueTriesError · class · L52-L56 — class MaximumUniqueTriesError(Exception)
