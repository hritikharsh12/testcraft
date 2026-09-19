from datetime import datetime

from pydantic import BaseModel


class FunctionInfo(BaseModel):
    name: str
    line_number: int
    args: list[str]
    has_docstring: bool
    is_async: bool


class ClassInfo(BaseModel):
    name: str
    line_number: int
    methods: list[str]


class ParsedSummary(BaseModel):
    language: str
    line_count: int
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]
    warnings: list[str]  # e.g. "no docstrings found", "syntax error at line X"


class UploadResponse(BaseModel):
    submission_id: int
    filename: str
    language: str
    summary: ParsedSummary
    created_at: datetime


class GenerateResponse(BaseModel):
    submission_id: int
    generated_tests: str
    suggestions: list[str]
    model_used: str
    created_at: datetime

