# backend/src/jadawel/contrib/database/management/commands/draw_field_graph.py

- Command · class · L13-L71 — class Command(BaseCommand)
- add_arguments · method · L19-L40 — def add_arguments(self, parser)
- handle · method · L42-L71 — def handle(self, *args, **options)
- draw_field_graph · function · L74-L138 — def draw_field_graph( database: Database, output_dir: str, gv_files_only: bool, draw_m2m_boxes: bool )
- field_node · function · L141-L142 — def field_node(field)
- via_node_name_func · function · L145-L156 — def via_node_name_func(via_dep)
