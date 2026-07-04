# Exceptions API Reference

Custom exception hierarchy for mdconverter error handling.

## Exception Hierarchy

```text
MDConvertError (base)
├── ConverterNotAvailableError
├── ConversionTimeoutError
├── InvalidInputError
└── ProviderError
```

---

::: mdconverter.core.exceptions
    options:
      show_root_heading: true
      members:
        - MDConvertError
        - ConverterNotAvailableError
        - ConversionTimeoutError
        - InvalidInputError
        - ProviderError
