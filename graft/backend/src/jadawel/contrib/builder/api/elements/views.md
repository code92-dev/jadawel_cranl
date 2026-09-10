# backend/src/jadawel/contrib/builder/api/elements/views.py

- ElementsView · class · L61-L177 — class ElementsView(APIView)
- get_permissions · method · L64-L68 — def get_permissions(self)
- get · method · L100-L114 — def get(self, request, page_id)
- post · method · L161-L177 — def post(self, request, data: Dict, page_id: int)
- ElementView · class · L180-L290 — class ElementView(APIView)
- patch · method · L224-L249 — def patch(self, request, element_id: int)
- delete · method · L281-L290 — def delete(self, request, element_id: int)
- MoveElementView · class · L293-L385 — class MoveElementView(APIView)
- patch · method · L335-L385 — def patch(self, request, data: Dict, element_id: int)
- DuplicateElementView · class · L388-L434 — class DuplicateElementView(APIView)
- post · method · L419-L434 — def post(self, request, element_id: int)
