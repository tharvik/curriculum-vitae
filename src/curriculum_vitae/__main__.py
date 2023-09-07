from argparse import ArgumentParser
import asyncio
from asyncio.subprocess import Process, create_subprocess_exec
from collections.abc import Awaitable, Callable
from io import BytesIO
from os import PathLike
from odf.opendocument import OpenDocument
from pathlib import Path
from subprocess import DEVNULL, PIPE, CalledProcessError
import sys
from tempfile import TemporaryDirectory
import tomlkit
from typing import Literal, TypeVar

from curriculum_vitae import generate

# from typeshed
StrOrBytesPath = PathLike | bytes | str

T = TypeVar("T")

Backend = Literal["libreoffice", "pandoc"]


class UnableToAutoDetectBackend(Exception):
    def __init__(self) -> None:
        super().__init__("unable to auto detect backend")


async def with_proc(
    act: Callable[[Process], Awaitable[T]],
    *args: StrOrBytesPath,
    stdin: int | None = DEVNULL,
    stdout: int | None = DEVNULL,
) -> T:
    p = await create_subprocess_exec(*args, stdin=stdin, stdout=stdout)
    ret = await act(p)
    assert p.returncode is not None

    if p.returncode != 0:
        raise CalledProcessError(p.returncode, args)

    return ret


async def read_stdout(*args: StrOrBytesPath) -> bytes:
    async def f(p: Process) -> bytes:
        return (await p.communicate())[0]

    return await with_proc(f, *args, stdout=PIPE)


async def run(*args: StrOrBytesPath) -> None:
    await with_proc(lambda p: p.wait(), *args)


# return true when empty
async def rm_if_empty_pdf(page: Path) -> bool:
    content = await read_stdout(
        "pdftotext",
        str(page),
        "-",
    )

    if len(content) < 3:  # quite empty
        await asyncio.get_running_loop().run_in_executor(None, page.unlink)
        return True

    return False


async def pdf_convert_libreoffice(doc: OpenDocument) -> None:
    with TemporaryDirectory() as tmpdir:
        odt_path = Path(tmpdir) / "cv_dirty.odt"
        out_path = Path(tmpdir) / "cv.pdf"
        pdf_path = odt_path.with_suffix(".pdf")

        doc.write(odt_path)

        await run(
            "libreoffice",
            "--convert-to",
            "pdf",
            "--outdir",
            pdf_path.parent,
            odt_path,
        )
        await run(
            "pdfseparate",
            pdf_path,
            pdf_path.with_stem("separated-%d"),
        )
        pages = list(pdf_path.parent.glob("separated-*.pdf"))

        to_unite = [
            page
            for page, removed in zip(
                pages, await asyncio.gather(*map(rm_if_empty_pdf, pages))
            )
            if not removed
        ]

        if len(to_unite) > 0:
            await run("pdfunite", *to_unite, out_path)
        else:
            # whole empty pdf, copy base one
            pdf_path.rename(out_path)

        with out_path.open("rb") as f:
            while len(f.peek()) > 0:
                sys.stdout.buffer.write(f.read1())


async def pdf_convert_pandoc(doc: OpenDocument) -> None:
    buffer = BytesIO()
    doc.write(buffer)

    async def send_buffer(p: Process) -> bytes:
        return (await p.communicate(buffer.getvalue()))[0]

    await with_proc(
        send_buffer,
        "pandoc",
        "--from=odt",
        "--to=pdf",
        stdin=PIPE,
        stdout=None,
    )


async def pdf_convert(backend: Backend | None, doc: OpenDocument) -> None:
    from shutil import which

    if backend is None:
        if which("libreoffice") is not None:
            backend = "libreoffice"
        elif which("pandoc") is not None:
            backend = "pandoc"
        else:
            raise UnableToAutoDetectBackend()

    if backend == "libreoffice":
        await pdf_convert_libreoffice(doc)
    elif backend == "pandoc":
        await pdf_convert_pandoc(doc)


def main() -> None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="fmt", required=True)
    subparsers.add_parser("odt")
    subparsers.add_parser("pdf").add_argument(
        "-b",
        "--backend",
        choices=["pandoc", "libreoffice"],
        help="which odt to pdf convertor to use",
    )
    args = parser.parse_args()

    config = tomlkit.load(sys.stdin)
    doc = generate(config)

    if args.fmt == "odt":
        doc.write(sys.stdout.buffer)
    else:
        asyncio.run(pdf_convert(args.backend, doc))
