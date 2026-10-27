"""Domain exceptions."""
class ApplicationError(Exception):
    """Base for expected application failures."""
class ConfigurationError(ApplicationError):
    """Invalid configuration."""
class DataError(ApplicationError):
    """Base for import/export failures."""
class DataImportError(DataError):
    """Input cannot be read or parsed."""
class DataExportError(DataError):
    """Output cannot be written safely."""
class RecordValidationError(DataError):
    """A record violates the configured schema."""
    def __init__(self, message: str, *, line_number: int | None = None, field: str | None = None):
        super().__init__(message)
        self.line_number = line_number
        self.field = field
