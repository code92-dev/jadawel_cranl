# backend/src/jadawel/contrib/database/db/functions.py

- RandomUUID · class · L4-L10 — class RandomUUID(Func): # We're using this function because the `gen_random_uuid` has introduced in # version 13, and we support a lower version than that. # More information about where we found this function: # https://stackoverflow.com/questions/12505158/generating-a-uuid-in-postgres-for-insert-statement
