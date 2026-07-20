import json
from pathlib import Path
from models import Componente


class Storage:
    def __init__(self, path: str = "data/stock.json"):
        self.path = Path(path)
        self._data = self._load()

    def _load(self):
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"componentes": []}, indent=2))
        return json.loads(self.path.read_text())

    def _save(self):
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False)
        )

    def listar(self):
        return [Componente(**c) for c in self._data["componentes"]]

    def agregar(self, comp: Componente):
        self._data["componentes"].append(comp.to_dict())
        self._save()

    def actualizar(self, id_: str, **campos):
        for c in self._data["componentes"]:
            if c["id"] == id_:
                c.update(campos)
        self._save()

    def eliminar(self, id_: str):
        self._data["componentes"] = [
            c for c in self._data["componentes"] if c["id"] != id_
        ]
        self._save()

    def buscar(self, texto: str):
        texto = texto.lower().strip()
        if not texto:
            return self.listar()
        return [
            Componente(**c)
            for c in self._data["componentes"]
            if texto in c["codigo"].lower()
            or texto in c["descripcion"].lower()
            or texto in c["ubicacion"].lower()
        ]

    def stock_bajo(self, umbral: int = 10):
        return [c for c in self.listar() if c.cantidad <= umbral]

    def total_unidades(self):
        return sum(c.cantidad for c in self.listar())
