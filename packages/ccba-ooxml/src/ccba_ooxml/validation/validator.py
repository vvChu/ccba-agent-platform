"""
Unified deep validation interface for Office Open XML files.
"""

from pathlib import Path

from .docx import DOCXSchemaValidator
from .pptx import PPTXSchemaValidator
from .redlining import RedliningValidator


class OOXMLValidator:
    """Unified deep validation interface for Office Open XML files.

    This class wraps individual format-specific validators and exposes
    a single, clean entry point for client code.
    """

    def __init__(self, unpacked_dir, original_file, verbose=False):
        self.unpacked_dir = Path(unpacked_dir).resolve()
        self.original_file = Path(original_file).resolve()
        self.verbose = verbose

    def validate(self) -> bool:
        """Run all applicable validators based on file extension.

        Returns:
            bool: True if all validations passed, False otherwise.
        """
        file_extension = self.original_file.suffix.lower()

        match file_extension:
            case ".docx":
                validators = [DOCXSchemaValidator, RedliningValidator]
            case ".pptx":
                validators = [PPTXSchemaValidator]
            case _:
                print(f"Error: Validation not supported for file type {file_extension}")
                return False

        success = True
        for V in validators:
            validator = V(self.unpacked_dir, self.original_file, verbose=self.verbose)
            if not validator.validate():
                success = False

        return success
