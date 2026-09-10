# backend/src/jadawel/contrib/builder/ws/domain/signals.py

- domain_created · function · L18-L28 — def domain_created(sender, domain: Domain, user: AbstractUser, **kwargs)
- domain_updated · function · L32-L45 — def domain_updated(sender, domain: Domain, user: AbstractUser, **kwargs)
- domain_deleted · function · L49-L65 — def domain_deleted( sender, builder: Builder, domain_id: int, user: AbstractUser, **kwargs )
- domain_reordered · function · L69-L86 — def domain_reordered( sender, builder: Builder, order: List[int], user: AbstractUser, **kwargs ): # Hashing all values here to not expose real ids of domains a user might not have # access to
