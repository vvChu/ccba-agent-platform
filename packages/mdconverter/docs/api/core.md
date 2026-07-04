# Core API Reference

## Converters

::: mdconverter.core.base
    options:
      show_root_heading: true
      members:
        - ConversionResult
        - ConversionStatus
        - ConversionTool
        - BaseConverter

---

::: mdconverter.core.gemini
    options:
      show_root_heading: true
      members:
        - LLMConverter
        - GeminiConverter

---

::: mdconverter.core.pandoc
    options:
      show_root_heading: true
      members:
        - PandocConverter

---

::: mdconverter.core.llamaparse
    options:
      show_root_heading: true
      members:
        - LlamaParseConverter

---

## Cache

::: mdconverter.core.cache
    options:
      show_root_heading: true
      members:
        - ConversionCache

---

## Registry

::: mdconverter.core.registry
    options:
      show_root_heading: true
      members:
        - ConverterRegistry

---

## Logging

::: mdconverter.core.logging
    options:
      show_root_heading: true
      members:
        - configure_logging
        - get_logger
        - log_operation
        - StructuredFormatter
