# MCP Runtime Dependency Policy

Tento dokument definuje jednotnou politiku verzování runtime dependencies pro MCP služby.

## Zdroj pravdy

- **Každá služba používá pouze `mcp-servers/<service>/requirements.txt` jako source of truth pro runtime balíky.**
- Legacy soubory ve tvaru `*-mcp-requirements.txt` byly odstraněny a nesmí se znovu zavádět.

## Baseline verze pro kritické runtime balíky

Všechny FastAPI-based MCP služby musí mít tyto kompatibilní rozsahy:

- `fastapi>=0.121.0,<0.122.0`
- `uvicorn>=0.24.0,<0.25.0` nebo `uvicorn[standard]>=0.24.0,<0.25.0`
- `pydantic>=2.5.0,<3.0.0`
- `starlette>=0.49.1,<0.50.0`
- `prometheus-fastapi-instrumentator>=6.1.0,<6.2.0`

## Pravidla pro pinning

- Runtime dependencies nesmí být nepinované (např. samotné `fastapi` bez verzového omezení).
- Preferovaný formát je kompatibilní rozsah `>=x.y.z,<x.(y+1).0`.
- Výjimky jsou možné jen pokud je zdokumentovaný důvod v README dané služby.

## CI enforcement

CI obsahuje kontrolu (`scripts/check_mcp_runtime_dependencies.py`), která:

1. validuje přítomnost baseline kritických balíků ve FastAPI službách,
2. kontroluje, že kritické balíky používají bounded range (`>=` + `<`),
3. failne build při porušení pravidel.
