from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header, Footer, Input, DataTable, Button, Static, Label
)
from textual.screen import ModalScreen
from textual import on

from storage import Storage
from models import Componente


# ---------- MODALES ----------

class FormularioComponente(ModalScreen):
    """Modal para añadir o editar un componente."""

    def __init__(self, comp: Componente | None = None):
        super().__init__()
        self.comp = comp  # None = alta, Componente = edición

    def compose(self) -> ComposeResult:
        titulo = "Editar componente" if self.comp else "Nuevo componente"
        with Vertical(id="form-modal"):
            with Vertical(id="form-box"):
                yield Label(titulo, classes="menu-title")
                yield Input(
                    placeholder="Código",
                    value=self.comp.codigo if self.comp else "",
                    id="f-codigo",
                )
                yield Input(
                    placeholder="Descripción",
                    value=self.comp.descripcion if self.comp else "",
                    id="f-descripcion",
                )
                yield Input(
                    placeholder="Cantidad",
                    value=str(self.comp.cantidad) if self.comp else "",
                    id="f-cantidad",
                )
                yield Input(
                    placeholder="Ubicación",
                    value=self.comp.ubicacion if self.comp else "",
                    id="f-ubicacion",
                )
                with Horizontal():
                    yield Button("Guardar", variant="success", id="btn-guardar")
                    yield Button("Cancelar", variant="error", id="btn-cancelar")

    @on(Button.Pressed, "#btn-guardar")
    def guardar(self):
        codigo = self.query_one("#f-codigo", Input).value.strip()
        descripcion = self.query_one("#f-descripcion", Input).value.strip()
        cantidad = self.query_one("#f-cantidad", Input).value.strip()
        ubicacion = self.query_one("#f-ubicacion", Input).value.strip()

        if not codigo or not cantidad.isdigit():
            self.app.bell()
            return

        if self.comp:
            self.dismiss(("editar", self.comp.id, codigo, descripcion, cantidad, ubicacion))
        else:
            self.dismiss(("nuevo", None, codigo, descripcion, cantidad, ubicacion))

    @on(Button.Pressed, "#btn-cancelar")
    def cancelar(self):
        self.dismiss(None)


class ConfirmarEliminar(ModalScreen):
    def __init__(self, comp: Componente):
        super().__init__()
        self.comp = comp

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Label(f"¿Eliminar '{self.comp.codigo}'?", classes="menu-title")
            with Horizontal():
                yield Button("Sí, eliminar", variant="error", id="btn-si")
                yield Button("Cancelar", variant="primary", id="btn-no")

    @on(Button.Pressed, "#btn-si")
    def si(self):
        self.dismiss(True)

    @on(Button.Pressed, "#btn-no")
    def no(self):
        self.dismiss(False)


# ---------- APP PRINCIPAL ----------

class StockApp(App):
    CSS_PATH = "app.tcss"
    TITLE = "StockCLI"

    BINDINGS = [
        ("a", "add_component", "Añadir"),
        ("e", "edit_component", "Editar"),
        ("d", "delete_component", "Eliminar"),
        ("slash", "focus_search", "Buscar"),
        ("l", "stock_bajo", "Stock bajo"),
        ("q", "quit", "Salir"),
    ]

    def __init__(self):
        super().__init__()
        self.storage = Storage()
        self.filtro_stock_bajo = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield Static("CRUD", classes="menu-title")
                yield Button("[a] Añadir", id="btn-add")
                yield Button("[e] Editar", id="btn-edit")
                yield Button("[d] Eliminar", id="btn-del")

                yield Static("Filtros", classes="menu-title")
                yield Button("[l] Stock bajo", id="btn-lowstock")
                yield Button("[s] Ordenar cant.", id="btn-sort")
                yield Button("[c] Limpiar filtro", id="btn-clear")

                yield Static("Config", classes="menu-title")
                yield Button("[i] Importar", id="btn-import")
                yield Button("[x] Exportar", id="btn-export")

                yield Static("Herramientas", classes="menu-title")
                yield Button("[h] Historial", id="btn-history")
                yield Button("[g] Estadísticas", id="btn-stats")
                yield Button("[b] Backup", id="btn-backup")

            with Vertical(id="main"):
                yield Input(placeholder="🔍 Buscar código, descripción o ubicación...", id="search")
                yield DataTable(id="tabla")
                yield Static(id="statusbar")

        yield Footer()

    def on_mount(self):
        table = self.query_one("#tabla", DataTable)
        table.cursor_type = "row"
        table.add_columns("ID", "Código", "Descripción", "Cantidad", "Ubicación")
        self.refresh_table()

    # ---------- helpers ----------

    def _fila_actual(self) -> Componente | None:
        table = self.query_one("#tabla", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        id_ = table.get_row(row_key)[0]
        for c in self.storage.listar():
            if c.id == id_:
                return c
        return None

    def refresh_table(self, lista: list[Componente] | None = None):
        table = self.query_one("#tabla", DataTable)
        table.clear()

        if lista is None:
            lista = self.storage.listar()
            if self.filtro_stock_bajo:
                lista = [c for c in lista if c.cantidad <= 10]

        for c in lista:
            estilo = ""
            if c.cantidad == 0:
                estilo = "⚠ AGOTADO"
            elif c.cantidad <= 10:
                estilo = "⚠ bajo"
            table.add_row(c.id, c.codigo, c.descripcion, str(c.cantidad), c.ubicacion, key=c.id)

        self._actualizar_status()

    def _actualizar_status(self):
        total = self.storage.total_unidades()
        cantidad_items = len(self.storage.listar())
        bajos = len(self.storage.stock_bajo())
        status = self.query_one("#statusbar", Static)
        status.update(
            f"Total: {total} uds   |   {cantidad_items} componentes   |   ⚠ {bajos} con stock bajo/agotado"
        )

    # ---------- acciones CRUD ----------

    def action_add_component(self):
        self.push_screen(FormularioComponente(), self._callback_formulario)

    def action_edit_component(self):
        comp = self._fila_actual()
        if comp:
            self.push_screen(FormularioComponente(comp), self._callback_formulario)

    def action_delete_component(self):
        comp = self._fila_actual()
        if comp:
            self.push_screen(ConfirmarEliminar(comp), lambda ok: self._callback_eliminar(ok, comp))

    def _callback_formulario(self, resultado):
        if resultado is None:
            return
        modo, id_, codigo, descripcion, cantidad, ubicacion = resultado
        if modo == "nuevo":
            comp = Componente.nuevo(codigo, descripcion, cantidad, ubicacion)
            self.storage.agregar(comp)
        else:
            self.storage.actualizar(
                id_, codigo=codigo, descripcion=descripcion,
                cantidad=int(cantidad), ubicacion=ubicacion,
            )
        self.refresh_table()

    def _callback_eliminar(self, ok: bool, comp: Componente):
        if ok:
            self.storage.eliminar(comp.id)
            self.refresh_table()

    # ---------- búsqueda y filtros ----------

    def action_focus_search(self):
        self.query_one("#search", Input).focus()

    @on(Input.Changed, "#search")
    def buscar_en_vivo(self, event: Input.Changed):
        resultados = self.storage.buscar(event.value)
        self.refresh_table(resultados)

    def action_stock_bajo(self):
        self.filtro_stock_bajo = not self.filtro_stock_bajo
        self.refresh_table()

    # ---------- botones del sidebar ----------

    @on(Button.Pressed, "#btn-add")
    def _b_add(self):
        self.action_add_component()

    @on(Button.Pressed, "#btn-edit")
    def _b_edit(self):
        self.action_edit_component()

    @on(Button.Pressed, "#btn-del")
    def _b_del(self):
        self.action_delete_component()

    @on(Button.Pressed, "#btn-lowstock")
    def _b_lowstock(self):
        self.action_stock_bajo()

    @on(Button.Pressed, "#btn-clear")
    def _b_clear(self):
        self.filtro_stock_bajo = False
        self.query_one("#search", Input).value = ""
        self.refresh_table()

    @on(Button.Pressed, "#btn-sort")
    def _b_sort(self):
        lista = sorted(self.storage.listar(), key=lambda c: c.cantidad)
        self.refresh_table(lista)


if __name__ == "__main__":
    StockApp().run()
