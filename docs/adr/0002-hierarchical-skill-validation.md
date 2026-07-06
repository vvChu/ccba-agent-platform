# 2. Hierarchical Skill Validation Parser with Keyword Exclusion

We decided to implement a Hierarchical Section Parser in `validate_skills.py` that tracks Markdown heading levels using a stack to accurately determine workflow section boundaries. Additionally, we introduced an `EXCLUSION_HEADERS` set of keywords (such as "Lưu ý", "Rules", "Tham chiếu") to temporarily disable step-validation checking under matching subheadings, preventing false positive errors on informational numbered lists.
