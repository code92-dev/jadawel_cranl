# backend/src/advocate/addrvalidator.py

- canonicalize_hostname · function · L17-L23 — def canonicalize_hostname(hostname)
- determine_local_addresses · function · L26-L43 — def determine_local_addresses()
- add_local_address_arg · function · L46-L63 — def add_local_address_arg(func)
- wrapper · function · L55-L61 — def wrapper(self, *args, **kwargs)
- AddrValidator · class · L66-L269 — class AddrValidator
- __init__ · method · L73-L103 — def __init__( self, ip_blacklist=None, ip_whitelist=None, port_whitelist=None, port_blacklist=None, hostname_blacklist=None, allow_ipv6=False, allow_teredo=False, allow_6to4=False, allow_dns64=False, # Must be explicitly set to "False" if you don't want to try # detecting local interface addresses with netifaces. autodetect_local_addresses=True, )
- is_ip_allowed · method · L106-L188 — def is_ip_allowed(self, addr_ip, _local_addresses=None)
- _hostname_matches_pattern · method · L190-L210 — def _hostname_matches_pattern(self, hostname, pattern): # If they specified a string, just assume they only want basic globbing. # This stops people from not realizing they're dealing in REs and # not escaping their periods unless they specifically pass in an RE. # This has the added benefit of letting us sanely handle globbed # IDNs by default.
- is_hostname_allowed · method · L212-L227 — def is_hostname_allowed(self, hostname): # Sometimes (like with "external" services that your IP has privileged # access to) you might not always know the IP range to blacklist access # to, or the `A` record might change without you noticing. # For e.x.: `foocorp.external.org`. # # Another option is doing something like: # # for addrinfo in socket.getaddrinfo("foocorp.external.org", 80): # global_validator.ip_blacklist.add(ip_address(addrinfo[4][0])) # # but that's not always a good idea if they're behind a third-party lb.
- is_addrinfo_allowed · method · L230-L269 — def is_addrinfo_allowed(self, addrinfo, _local_addresses=None)
