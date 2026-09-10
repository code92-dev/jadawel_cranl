# backend/src/jadawel/core/telemetry/env_overrides_parser.py

- get_sampler_overrides_from_str · function · L25-L54 — def get_sampler_overrides_from_str(overrides: str) -> Dict[str, Sampler]
- ModuleAndSamplerTuple · class · L57-L59 — class ModuleAndSamplerTuple(NamedTuple)
- _try_get_sampler_and_module_from_str · function · L62-L97 — def _try_get_sampler_and_module_from_str(override) -> Optional[ModuleAndSamplerTuple]
- _generate_sampler_from_string_args · function · L100-L130 — def _generate_sampler_from_string_args( module: str, trace_sampler: str, arg: str ) -> Optional[Sampler]
