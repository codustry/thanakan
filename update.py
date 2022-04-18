from plumbum import local
from dataclasses import dataclass
import re

poetry = local['poetry']

deps = poetry('show', '--outdated').splitlines()
print(deps)

@dataclass
class Dep:
    name: str
    installed: str
    latest: str
    description: str

clean_deps = [ Dep(*re.split('\s+', raw_dep, maxsplit=3)) for raw_dep in deps ]

for dep in clean_deps:
    if dep.latest != dep.installed:
        print(f'{dep.name} {dep.installed} -> {dep.latest}')
        poetry('update', f"{dep.name}@^{dep.latest}")
