from collections.abc import Iterable
from odf.element import Element
from odf.opendocument import OpenDocument
from odf.style import ParagraphProperties, Style, TableColumnProperties, TextProperties


paragraph_styles = {
    "Title": (
        TextProperties(
            fontfamily="DejaVu Sans",
            fontsize="28pt",
            color="#000000",
            fontweight="bold",
        ),
        ParagraphProperties(
            marginbottom="0.05in",
        ),
    ),
    "Subtitle": (
        TextProperties(
            fontfamily="DejaVu Sans Light",
            fontsize="11pt",
            color="#666666",
            fontweight="bold",
            letterspacing="0.015in",
        ),
        ParagraphProperties(
            marginleft="0.08in",
            marginright="0.08in",
        ),
    ),
    "Urls": (
        TextProperties(
            fontfamily="DejaVu Sans",
            fontsize="10pt",
            color="#999999",
        ),
        ParagraphProperties(
            margintop="0.05in",
            marginbottom="0.05in",
        ),
    ),
    "Table header": (
        TextProperties(
            fontfamily="DejaVu Sans",
            fontsize="10pt",
            color="#4c4c4c",
        ),
        ParagraphProperties(
            padding="0.05in",
            borderbottom="0.06pt solid #000000",
            marginleft="0.05in",
            marginright="0.05in",
            margintop="0.1in",
            marginbottom="0.05in",
        ),
    ),
    "Table key": (
        TextProperties(
            fontfamily="DejaVu Sans",
            fontsize="10pt",
            color="#999999",
        ),
        ParagraphProperties(
            marginleft="0.05in",
            marginright="0.05in",
            margintop="0.05in",
            marginbottom="0.05in",
            textalign="end",
        ),
    ),
    "Table value": (
        TextProperties(
            fontfamily="DejaVu Sans",
            fontsize="10pt",
            color="#000000",
        ),
        ParagraphProperties(
            marginleft="0.05in",
            marginright="0.05in",
            margintop="0.05in",
            marginbottom="0.05in",
        ),
    ),
    "Table value bold": (
        TextProperties(
            fontfamily="DejaVu Sans",
            fontsize="10pt",
            color="#000000",
            fontweight="bold",
        ),
        ParagraphProperties(
            marginleft="0.05in",
            marginright="0.05in",
            margintop="0.05in",
            marginbottom="0.05in",
        ),
    ),
}

tablecolumn_styles = {
    "Table title": TableColumnProperties(relcolumnwidth="2000*"),
    "Table urls": TableColumnProperties(relcolumnwidth="1000*"),
    "Table column key": TableColumnProperties(relcolumnwidth="1000*"),
    "Table column value": TableColumnProperties(relcolumnwidth="4000*"),
}


def gen_styles() -> Iterable[Element]:
    for name, (font, para) in paragraph_styles.items():
        s = Style(name=name, family="paragraph")
        s.addElement(font)
        s.addElement(para)
        yield s


def gen_auto_styles() -> Iterable[Element]:
    for name, props in tablecolumn_styles.items():
        s = Style(name=name, family="table-column")
        s.addElement(props)
        yield s

    bold = Style(name="Bold", family="text")
    bold.addElement(
        TextProperties(
            fontweight="bold",
        )
    )
    yield bold


def add_styles(doc: OpenDocument) -> None:
    for s in gen_styles():
        doc.styles.addElement(s)
    for s in gen_auto_styles():
        doc.automaticstyles.addElement(s)
