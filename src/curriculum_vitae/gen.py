__all__ = ["gen"]

from collections.abc import Iterable, Mapping, Sequence
from itertools import zip_longest
from math import ceil
from odf.opendocument import Element, OpenDocument, OpenDocumentText
from odf.table import Table, TableColumn, TableRow, TableCell
from odf.text import A, P, Span
from tomlkit import TOMLDocument
from typing import Any, TypeGuard, TypeVar

from .styles import add_styles

T = TypeVar("T", str, Sequence[str], Mapping[str, str])
Block = tuple[str, T]
TextBlock = Block[str]
ListBlock = Block[Sequence[str]]
DictBlock = Block[Mapping[str, str]]


def is_seq_of_str(o: Any) -> TypeGuard[Sequence[str]]:
    return isinstance(o, Sequence) and all(isinstance(e, str) for e in o)


def is_mapping_of_str_to_str(o: Any) -> TypeGuard[Mapping[str, str]]:
    return isinstance(o, Mapping) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in o.items()
    )


class UnexpectedBlockType(Exception):
    def __init__(self, name: str, unexpected: type) -> None:
        super().__init__(f"unexpected shape of block {name}, got type {unexpected}")


def get_blocks(config: TOMLDocument) -> Iterable[Block[Any]]:
    for block_name, v in config.unwrap().items():
        if isinstance(v, str):
            yield block_name, v
        elif isinstance(v, dict):
            if len(v) == 1 and "_" in v and is_seq_of_str(v["_"]):
                yield block_name, v["_"]
            elif is_mapping_of_str_to_str(v):
                yield block_name, v
            else:
                raise UnexpectedBlockType(block_name, type(v))
        else:
            raise UnexpectedBlockType(block_name, type(v))


def get_header(doc: OpenDocument, config: TOMLDocument) -> Element:
    title = config.pop("title", None)
    subtitle = config.pop("subtitle").upper() if "subtitle" in config else None
    urls = config.pop("urls", {})

    table = Table()

    table.addElement(
        TableColumn(
            stylename=doc.getStyleByName("Table title"),
        )
    )
    table.addElement(
        TableColumn(
            stylename=doc.getStyleByName("Table urls"),
        )
    )

    tr = TableRow()
    table.addElement(tr)
    tc = TableCell(
        valuetype="string",
        numberrowsspanned=len(urls),
    )
    tr.addElement(tc)
    tc.addElement(
        P(
            stylename=doc.getStyleByName("Title"),
            text=title,
        )
    )
    tc.addElement(
        P(
            stylename=doc.getStyleByName("Subtitle"),
            text=subtitle,
        )
    )

    for text, url in urls.items():
        tr = TableRow() if tr is None else tr
        table.addElement(tr)

        tc = TableCell(valuetype="string")
        tr.addElement(tc)

        p = P(stylename=doc.getStyleByName("Urls"))
        tc.addElement(p)
        p.addElement(
            A(
                text=text,
                href=url,
            )
        )

        tr = None

    return table


def get_dict_section(doc: OpenDocument, block: DictBlock) -> Element:
    title, values = block

    table = Table()

    for style in "key", "value":
        stylename = "Table column " + style
        table.addElement(
            TableColumn(
                stylename=doc.getStyleByName(stylename),
            )
        )

    tr = TableRow()
    table.addElement(tr)
    tc = TableCell(
        valuetype="string",
        numbercolumnsspanned=2,
    )
    tc.addElement(
        P(
            stylename=doc.getStyleByName("Table header"),
            text="+ " + title.upper(),
        )
    )
    tr.addElement(tc)

    for key, value in values.items():
        tr = get_normal_row(doc, key, value)
        table.addElement(tr)

    return table


def get_paragraph(doc: OpenDocument, style: Element, value: str) -> Element:
    p = P(stylename=style)

    bold = False
    for v in value.split("_"):
        part = Span(
            stylename=doc.getStyleByName("Bold") if bold else None,
            text=v,
        )

        p.addElement(part)

        bold = not bold

    return p


def get_normal_row(doc: OpenDocument, title: str, value: str) -> Element:
    tr = TableRow()
    tc_key = TableCell(valuetype="string")
    tc_val = TableCell(valuetype="string")

    tc_key.addElement(
        P(
            stylename=doc.getStyleByName("Table key"),
            text=title,
        )
    )
    for line in value.split("\n"):
        p = get_paragraph(doc, doc.getStyleByName("Table value"), line)
        tc_val.addElement(p)

    tr.addElement(tc_key)
    tr.addElement(tc_val)

    return tr


def get_list_cell(doc: OpenDocument, line: str | None) -> Element:
    tc = TableCell(
        valuetype="string",
    )

    if line is not None:
        tc.addElement(
            P(
                stylename=doc.getStyleByName("Table value"),
                text=line,
            )
        )

    return tc


def get_list_section(doc: OpenDocument, block: ListBlock) -> Element:
    title, values = block

    table = Table()

    for _ in range(2):
        table.addElement(
            TableColumn(
                stylename=doc.getStyleByName("Table value"),
            )
        )

    tr = TableRow()
    table.addElement(tr)

    tc = TableCell(valuetype="string", numbercolumnsspanned=2)
    tc.addElement(
        P(
            stylename=doc.getStyleByName("Table header"),
            text="+ " + title.upper(),
        )
    )
    tr.addElement(tc)

    middle = ceil(len(values) / 2)

    for line in zip_longest(values[:middle], values[middle:]):
        tr = TableRow()
        table.addElement(tr)

        for e in line:
            cell = get_list_cell(doc, e)
            tr.addElement(cell)

    return table


def get_text_section(doc: OpenDocument, block: TextBlock) -> Element:
    title, line = block

    table = Table()

    tr = TableRow()
    table.addElement(tr)
    tc = TableCell(
        valuetype="string",
    )
    tc.addElement(
        P(
            stylename=doc.getStyleByName("Table header"),
            text="+ " + title.upper(),
        )
    )
    tr.addElement(tc)

    tr = TableRow()
    table.addElement(tr)
    tr.addElement(get_list_cell(doc, line))

    return table


def gen(config: TOMLDocument) -> OpenDocument:
    doc = OpenDocumentText()
    add_styles(doc)

    doc.text.addElement(get_header(doc, config))

    for block in get_blocks(config):
        table = None
        if isinstance(block[1], str):
            table = get_text_section(doc, block)
        elif isinstance(block[1], Sequence):
            table = get_list_section(doc, block)
        elif isinstance(block[1], Mapping):
            table = get_dict_section(doc, block)

        doc.text.addElement(table)

    return doc
