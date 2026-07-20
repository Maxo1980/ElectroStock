from dataclasses import dataclass, asdict
import uuid


@dataclass
class Componente:
    id: str
    codigo: str
    descripcion: str
    cantidad: int
    ubicacion: str

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def nuevo(codigo, descripcion, cantidad, ubicacion):
        return Componente(
            id=str(uuid.uuid4())[:8],
            codigo=codigo,
            descripcion=descripcion,
            cantidad=int(cantidad),
            ubicacion=ubicacion,
        )
