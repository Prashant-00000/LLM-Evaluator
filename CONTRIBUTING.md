# Contributing to Guardian LLM Safety Framework

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/guardian-llm.git
   cd guardian-llm
   ```

3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests
```bash
python -m pytest tests/
```

### Running the Dashboard
```bash
streamlit run src/dashboard/streamlit_dashboard.py
```

### Running Bulk Evaluation
```bash
python -m src.engine.bulk_evaluator
```

## Code Style

- Follow PEP 8 guidelines
- Use descriptive variable names
- Add docstrings to functions and classes
- Keep functions focused and modular

## Commit Messages

Use clear, descriptive commit messages:
```
feat: Add new red-teaming attack vector
fix: Resolve faithfulness scorer bug
docs: Update API documentation
refactor: Simplify evaluation pipeline
```

## Pull Request Process

1. **Update documentation** if needed
2. **Run tests** to ensure nothing breaks
3. **Create a descriptive PR** with:
   - Clear title
   - Description of changes
   - Motivation/context
   - Testing done

4. **Request review** from maintainers

## Areas for Contribution

- **New Evaluators**: Add custom evaluation metrics
- **Attack Vectors**: Expand red-teaming suite
- **Visualizations**: Improve dashboard charts
- **Documentation**: Enhance guides and examples
- **Performance**: Optimize evaluation pipeline
- **Testing**: Add unit and integration tests

## Reporting Issues

When reporting bugs:
1. Include Python version and OS
2. Provide minimal reproducible example
3. Show error messages and logs
4. Describe expected vs actual behavior

## Questions?

Feel free to open a GitHub issue or discussion for questions about contributing.

---

Thank you for helping make Guardian safer and better! 🛡️
