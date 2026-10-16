# Contributing to QRIS Parser 🇮🇩

Thank you for your interest in contributing to **QRIS Parser**! We welcome bug reports, feature requests, documentation improvements, and pull requests from the developer and fintech community.

---

## 🛠️ Local Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/muhakmal/qris-parser.git
   cd qris-parser
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the package in editable mode with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run the test suite:**
   ```bash
   pytest
   ```

---

## 📋 Guidelines

### Code Style & Quality
- Write clear, idiomatic Python with type hints (`typing` / PEP 484).
- Adhere to PEP 8 standards. We recommend running `ruff check .` or `flake8`.
- Ensure new features include unit tests under the `tests/` directory.

### Git & Commits
- Follow [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: add CPM offline data authentication validation`
  - `fix: handle non-padded Base64 payload in CPM parser`
  - `docs: update quickstart guide in README`
  - `test: add test vector for ShopeePay dynamic QRIS`

### Pull Request Process
1. Create a feature branch from `main`: `git checkout -b feat/your-feature-name`.
2. Commit your changes and ensure all tests pass: `pytest`.
3. Push to your branch and open a Pull Request against `main`.
4. Provide a clear description of the problem solved or feature added.

---

## 📄 License
By contributing to this repository, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
