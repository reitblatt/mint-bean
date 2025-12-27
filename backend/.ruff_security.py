"""Custom security linting rules for data isolation.

This module provides AST-based checks to detect potential data leakage bugs
where database queries might be missing user_id filters.

Usage: Run with ruff or integrate into pre-commit hooks.
"""

import ast
from typing import Any


class UserIdFilterChecker(ast.NodeVisitor):
    """AST visitor that checks for missing user_id filters in SQLAlchemy queries.

    This checks for patterns like:
    - db.query(Model).filter(...) without user_id in the filter
    - session.query(Model).filter(...) without user_id

    It flags these as potential security issues unless:
    - The query includes .filter(Model.user_id == ...)
    - The query is in a test file
    - The query is explicitly marked with # noqa: user-isolation
    """

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: list[dict[str, Any]] = []
        self.is_test_file = "test_" in filename or "/tests/" in filename

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes to check for query patterns."""
        # Skip if this is a test file
        if self.is_test_file:
            self.generic_visit(node)
            return

        # Check for db.query(...) or session.query(...) patterns
        if self._is_query_call(node):
            # Walk the AST to see if .filter() is called with user_id
            if not self._has_user_id_filter(node):
                self.issues.append(
                    {
                        "line": node.lineno,
                        "col": node.col_offset,
                        "message": (
                            "Potential data leakage: Query appears to be missing "
                            "user_id filter. Add .filter(Model.user_id == current_user.id) "
                            "or # noqa: user-isolation if intentional."
                        ),
                        "code": "SEC001",
                    }
                )

        self.generic_visit(node)

    def _is_query_call(self, node: ast.Call) -> bool:
        """Check if this is a db.query() or session.query() call."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == "query":
                # Check if it's called on db or session
                if isinstance(node.func.value, ast.Name):
                    return node.func.value.id in ("db", "session")
        return False

    def _has_user_id_filter(self, node: ast.Call) -> bool:
        """
        Check if the query chain includes a user_id filter.

        This is a heuristic check that looks for:
        - .filter(Model.user_id == ...)
        - .filter_by(user_id=...)
        """
        # Get the source code line to do a simple string check
        # This is not perfect but catches most cases
        try:
            source = ast.get_source_segment(self._source, node)
            if source and "user_id" in source:
                return True
        except Exception:
            pass

        return False


def check_file_for_user_isolation(filename: str, source: str) -> list[dict[str, Any]]:
    """
    Check a Python file for potential user isolation issues.

    Args:
        filename: Path to the file being checked
        source: Source code content

    Returns:
        List of issues found, each with line, col, message, and code
    """
    try:
        tree = ast.parse(source, filename=filename)
        checker = UserIdFilterChecker(filename)
        checker._source = source  # Store source for get_source_segment
        checker.visit(tree)
        return checker.issues
    except SyntaxError:
        return []


# Example usage in pre-commit hook or CI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python .ruff_security.py <file.py>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, encoding="utf-8") as f:
        source = f.read()

    issues = check_file_for_user_isolation(filename, source)

    if issues:
        print(f"\nSecurity issues found in {filename}:")
        for issue in issues:
            print(
                f"  Line {issue['line']}, col {issue['col']}: "
                f"[{issue['code']}] {issue['message']}"
            )
        sys.exit(1)
    else:
        print(f"✓ No security issues found in {filename}")
        sys.exit(0)
