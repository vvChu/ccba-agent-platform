# 3. Object-Oriented Plan Management with File-based Concurrency Lock

We decided to refactor `plan.py` to use domain models (`Plan` and `Phase` classes) to abstract Markdown and Frontmatter parsing. To protect against concurrency race conditions in multi-agent environments, we implemented a simple file-based lock (`.plan.lock`). To preserve custom metadata formatting and engineer comments in existing phase files, we utilized a target-line override technique for status updates instead of complete file re-serialization.
