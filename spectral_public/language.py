"""ISL 0.1: bounded, deterministic, non-neural public language kernel.

No eval/exec, networking, model calls, plugins, registry or binary state format.
This deliberately does not claim genuine natural-language understanding.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, NamedTuple

from .core import Interval, SpectrumError, SpectrumRecord, blend, intersection, midpoint_cosine, union

LANGUAGE_PROFILE = "isl-language/0.1"
_TOKEN_NUMBER = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?")
_TOKEN_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
_FIELDS = {"text", "context", "provenance"}
_OPERATORS = {"intersect", "union", "blend", "cosine", "filter"}


class ISLError(ValueError):
    """User-facing lexical, grammatical or semantic language error."""


class Token(NamedTuple):
    kind: str
    value: Any
    line: int
    column: int


@dataclass(frozen=True)
class AxisDecl:
    name: str
    line: int


@dataclass(frozen=True)
class RecordDecl:
    name: str
    text: str
    context: str
    provenance: str
    axes: dict[str, Interval]
    line: int


@dataclass(frozen=True)
class Call:
    operator: str
    operands: tuple[Any, ...]
    line: int


@dataclass(frozen=True)
class LetDecl:
    name: str
    call: Call
    line: int


@dataclass(frozen=True)
class PrintStmt:
    name: str
    line: int


@dataclass(frozen=True)
class Program:
    statements: tuple[AxisDecl | RecordDecl | LetDecl | PrintStmt, ...]


def tokenize(source: str) -> tuple[Token, ...]:
    if not isinstance(source, str):
        raise ISLError("source must be UTF-8 text")
    tokens: list[Token] = []
    pos = 0
    line = col = 1
    while pos < len(source):
        c = source[pos]
        if c in " \t\r\n":
            if c == "\n":
                line, col = line + 1, 1
            else:
                col += 1
            pos += 1
            continue
        if c == "#":
            end = source.find("\n", pos)
            if end < 0:
                break
            col += end - pos
            pos = end
            continue
        start_line, start_col = line, col
        if c == '"':
            end = pos + 1
            while end < len(source):
                if source[end] == "\\":
                    end += 2
                    continue
                if source[end] == '"':
                    break
                if source[end] in "\r\n":
                    raise ISLError(f"{line}:{col}: unclosed string literal")
                end += 1
            if end >= len(source):
                raise ISLError(f"{line}:{col}: unclosed string literal")
            raw = source[pos:end + 1]
            try:
                value = json.loads(raw)
                value.encode("utf-8", errors="strict")
            except (UnicodeError, ValueError) as exc:
                raise ISLError(f"{line}:{col}: invalid quoted UTF-8 string") from exc
            tokens.append(Token("STRING", value, start_line, start_col))
            col += len(raw)
            pos = end + 1
            continue
        if source.startswith(">=", pos):
            tokens.append(Token(">=", ">=", line, col))
            pos += 2
            col += 2
            continue
        number = _TOKEN_NUMBER.match(source, pos)
        if number:
            value = number.group()
            tokens.append(Token("NUMBER", value, line, col))
            pos += len(value)
            col += len(value)
            continue
        identifier = _TOKEN_IDENT.match(source, pos)
        if identifier:
            value = identifier.group()
            tokens.append(Token("ID", value, line, col))
            pos += len(value)
            col += len(value)
            continue
        if c in "{}[](),;.=":
            tokens.append(Token(c, c, line, col))
            pos += 1
            col += 1
            continue
        raise ISLError(f"{line}:{col}: unexpected character {c!r}")
    tokens.append(Token("EOF", "", line, col))
    return tuple(tokens)


class Parser:
    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.offset = 0

    @property
    def here(self) -> Token:
        return self.tokens[self.offset]

    def take(self, kind: str, value: str | None = None) -> Token:
        token = self.here
        if token.kind != kind or (value is not None and token.value != value):
            expected = f"{kind} {value}" if value else kind
            raise ISLError(f"{token.line}:{token.column}: expected {expected}; got {token.kind} {token.value!r}")
        self.offset += 1
        return token

    def word(self, name: str) -> Token:
        return self.take("ID", name)

    def number(self) -> float:
        tok = self.take("NUMBER")
        val = float(tok.value)
        if not 0 <= val <= 1:  # also rejects inf, nan by comparison
            raise ISLError(f"{tok.line}:{tok.column}: number must be within [0,1]")
        return val

    def axis_reference(self) -> tuple[str, str]:
        record = self.take("ID").value
        self.take(".")
        axis = self.take("ID").value
        return (record, axis)

    def call(self) -> Call:
        token = self.take("ID")
        op = token.value
        if op not in _OPERATORS:
            raise ISLError(f"{token.line}:{token.column}: unsupported operator {op!r}")
        self.take("(")
        if op == "cosine":
            left = self.take("ID").value
            self.take(",")
            right = self.take("ID").value
            operands: tuple[Any, ...] = (left, right)
        elif op == "filter":
            axis = self.take("ID").value
            self.take(",")
            self.word("lower")
            self.take(">=")
            operands = (axis, self.number())
        else:
            left = self.axis_reference()
            self.take(",")
            right = self.axis_reference()
            if op == "blend":
                self.take(",")
                operands = (left, right, self.number())
            else:
                operands = (left, right)
        self.take(")")
        return Call(op, operands, token.line)

    def record(self) -> RecordDecl:
        start = self.word("record")
        name = self.take("ID").value
        self.take("{")
        fields: dict[str, str] = {}
        axes: dict[str, Interval] = {}
        while self.here.kind != "}":
            if self.here.kind == "EOF":
                raise ISLError(f"{self.here.line}:{self.here.column}: unclosed record")
            key_token = self.take("ID")
            key = key_token.value
            if key in _FIELDS:
                if key in fields:
                    raise ISLError(f"{key_token.line}:{key_token.column}: duplicate field {key!r}")
                value = self.take("STRING").value
                if not value.strip():
                    raise ISLError(f"{key_token.line}:{key_token.column}: {key} must not be blank")
                fields[key] = value
            else:
                self.take("=")
                self.take("[")
                lower = self.number()
                self.take(",")
                upper = self.number()
                self.take("]")
                if key in axes:
                    raise ISLError(f"{key_token.line}:{key_token.column}: duplicate axis {key!r}")
                try:
                    axes[key] = Interval(lower, upper)
                except SpectrumError as exc:
                    raise ISLError(f"{key_token.line}:{key_token.column}: {exc}") from exc
            self.take(";")
        self.take("}")
        missing = _FIELDS - fields.keys()
        if missing:
            raise ISLError(f"{start.line}: record {name} missing metadata: {', '.join(sorted(missing))}")
        return RecordDecl(name, fields["text"], fields["context"], fields["provenance"], axes, start.line)

    def parse(self) -> Program:
        self.word("isl")
        version = self.take("NUMBER")
        if version.value != "0.1":
            raise ISLError(f"{version.line}:{version.column}: only 'isl 0.1' is supported")
        self.take(";")
        statements: list[AxisDecl | RecordDecl | LetDecl | PrintStmt] = []
        while self.here.kind != "EOF":
            keyword = self.here
            if keyword.kind != "ID":
                raise ISLError(f"{keyword.line}:{keyword.column}: statement expected")
            if keyword.value == "axis":
                self.word("axis")
                name = self.take("ID").value
                self.take(";")
                statements.append(AxisDecl(name, keyword.line))
            elif keyword.value == "record":
                statements.append(self.record())
            elif keyword.value == "let":
                self.word("let")
                name = self.take("ID").value
                self.take("=")
                call = self.call()
                self.take(";")
                statements.append(LetDecl(name, call, keyword.line))
            elif keyword.value == "print":
                self.word("print")
                name = self.take("ID").value
                self.take(";")
                statements.append(PrintStmt(name, keyword.line))
            else:
                raise ISLError(f"{keyword.line}:{keyword.column}: unknown statement {keyword.value!r}")
        return Program(tuple(statements))


def parse(source: str) -> Program:
    """Strict grammar parser. Does not execute or import Python modules from source."""
    return Parser(source).parse()


def _evaluated(call: Call, records: dict[str, SpectrumRecord], axes: set[str]) -> tuple[str, Any]:
    op = call.operator

    def axis_of(ref: tuple[str, str]) -> Interval:
        record, name = ref
        if record not in records:
            raise ISLError(f"{call.line}: unknown record {record!r}")
        if name not in records[record].axes:
            raise ISLError(f"{call.line}: unknown axis {name!r} in record {record!r}")
        return records[record].axes[name]

    try:
        if op in ("intersect", "union", "blend"):
            left, right = axis_of(call.operands[0]), axis_of(call.operands[1])
            if call.operands[0][1] != call.operands[1][1]:
                raise ISLError(f"{call.line}: interval operands must have the same axis")
            if op == "intersect":
                value = intersection(left, right)
                return ("interval-or-empty", None if value is None else value.to_json())
            if op == "union":
                return ("interval-set", [x.to_json() for x in union(left, right)])
            return ("interval", blend(left, right, call.operands[2]).to_json())
        if op == "cosine":
            left, right = call.operands
            if left not in records or right not in records:
                raise ISLError(f"{call.line}: unknown record in cosine operands")
            return ("heuristic-similarity", midpoint_cosine(records[left], records[right]))
        if op == "filter":
            axis, bound = call.operands
            if axis not in axes:
                raise ISLError(f"{call.line}: undeclared axis {axis!r}")
            return ("record-selection", [name for name, row in records.items() if row.axes[axis].lower >= bound])
    except SpectrumError as exc:
        raise ISLError(f"{call.line}: {exc}") from exc
    raise ISLError(f"{call.line}: operator not supported")


def execute(program: Program) -> dict[str, Any]:
    """Run a closed, deterministic module; no filesystem or network access."""
    axes: set[str] = set()
    records: dict[str, SpectrumRecord] = {}
    values: dict[str, tuple[str, Any]] = {}
    outputs: list[dict[str, Any]] = []
    all_names: set[str] = set()
    began_records = False
    for stmt in program.statements:
        if isinstance(stmt, AxisDecl):
            if began_records:
                raise ISLError(f"{stmt.line}: axis declarations must precede records and expressions")
            if stmt.name in axes or stmt.name in _FIELDS:
                raise ISLError(f"{stmt.line}: duplicate or reserved axis name {stmt.name!r}")
            axes.add(stmt.name)
        elif isinstance(stmt, RecordDecl):
            began_records = True
            if stmt.name in all_names or stmt.name in axes or stmt.name in _OPERATORS:
                raise ISLError(f"{stmt.line}: duplicate or reserved record name {stmt.name!r}")
            if set(stmt.axes) != axes or not axes:
                raise ISLError(f"{stmt.line}: record {stmt.name!r} must specify exactly declared axes {sorted(axes)}")
            all_names.add(stmt.name)
            records[stmt.name] = SpectrumRecord(stmt.name, stmt.text, stmt.context, stmt.provenance, stmt.axes)
        elif isinstance(stmt, LetDecl):
            began_records = True
            if stmt.name in all_names or stmt.name in axes or stmt.name in _OPERATORS:
                raise ISLError(f"{stmt.line}: duplicate or reserved binding name {stmt.name!r}")
            all_names.add(stmt.name)
            values[stmt.name] = _evaluated(stmt.call, records, axes)
        elif isinstance(stmt, PrintStmt):
            began_records = True
            if stmt.name not in values:
                raise ISLError(f"{stmt.line}: print requires a prior 'let' binding {stmt.name!r}")
            kind, value = values[stmt.name]
            outputs.append({"name": stmt.name, "type": kind, "value": value})
    return {"profile": LANGUAGE_PROFILE, "axes": sorted(axes), "records": len(records), "outputs": outputs}


def run(source: str) -> dict[str, Any]:
    return execute(parse(source))


def run_file(path: str | Path) -> dict[str, Any]:
    return run(Path(path).read_text(encoding="utf-8"))
