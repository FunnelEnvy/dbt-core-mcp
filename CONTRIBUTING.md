# Contributing to dbt-core-mcp

We love your input! We want to make contributing to dbt-core-mcp as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [Github Flow](https://guides.github.com/introduction/flow/index.html)

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the existing style.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/your-org/dbt-core-mcp/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/your-org/dbt-core-mcp/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/your-username/dbt-core-mcp.git
cd dbt-core-mcp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black flake8
```

4. Create a branch:
```bash
git checkout -b feature/your-feature-name
```

5. Make your changes and test:
```bash
pytest
black src tests
flake8 src tests
```

6. Commit your changes:
```bash
git add .
git commit -m "Add your meaningful commit message"
```

7. Push to your fork:
```bash
git push origin feature/your-feature-name
```

8. Open a Pull Request

## Code Style

- We use [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
- Use [Black](https://github.com/psf/black) for code formatting
- Use type hints where applicable
- Write docstrings for all public functions and classes
- Keep line length to 100 characters

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for high test coverage
- Use pytest for testing

## Documentation

- Update README.md if needed
- Add docstrings to new functions/classes
- Update API documentation for new tools
- Include examples where helpful

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## Code of Conduct

### Our Pledge

In the interest of fostering an open and welcoming environment, we as contributors and maintainers pledge to making participation in our project and our community a harassment-free experience for everyone.

### Our Standards

Examples of behavior that contributes to creating a positive environment include:

* Using welcoming and inclusive language
* Being respectful of differing viewpoints and experiences
* Gracefully accepting constructive criticism
* Focusing on what is best for the community
* Showing empathy towards other community members

### Our Responsibilities

Project maintainers are responsible for clarifying the standards of acceptable behavior and are expected to take appropriate and fair corrective action in response to any instances of unacceptable behavior.

### Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by contacting the project team. All complaints will be reviewed and investigated and will result in a response that is deemed necessary and appropriate to the circumstances.

## Questions?

Feel free to open an issue with a question tag or reach out to the maintainers directly.