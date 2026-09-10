# backend/src/jadawel/api/exceptions.py

- api_exception_to_json_response · function · L8-L22 — def api_exception_to_json_response(exc: APIException) -> JsonResponse
- RequestBodyValidationException · class · L25-L30 — class RequestBodyValidationException(APIException)
- __init__ · method · L26-L30 — def __init__(self, detail=None, code=None)
- UnknownFieldProvided · class · L33-L36 — class UnknownFieldProvided(ValidationError)
- QueryParameterValidationException · class · L39-L44 — class QueryParameterValidationException(APIException)
- __init__ · method · L40-L44 — def __init__(self, detail=None, code=None)
- ThrottledAPIException · class · L47-L48 — class ThrottledAPIException(Throttled)
- InvalidClientSessionIdAPIException · class · L51-L58 — class InvalidClientSessionIdAPIException(APIException)
- InvalidUndoRedoActionGroupIdAPIException · class · L61-L67 — class InvalidUndoRedoActionGroupIdAPIException(APIException)
- InvalidSortDirectionException · class · L70-L73 — class InvalidSortDirectionException(Exception)
- InvalidSortAttributeException · class · L76-L79 — class InvalidSortAttributeException(Exception)
