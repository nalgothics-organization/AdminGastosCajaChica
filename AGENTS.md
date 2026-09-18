# Instructions for Code Formatting and Encoding

When generating, editing, or refactoring files in this repository, follow these rules strictly:

## 1. Indent Style
* Always use spaces (`space`) instead of hard tabs (`tab`).
* Never insert literal tab characters into code or configuration files.

## 2. Indent Size
* **2 spaces:** Web technologies and markup (`.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`, `.json`, `.yaml`, `.yml`).
* **4 spaces:** Systems and backend languages (`.py`, `.cs`, `.java`, `.cpp`, `.php`).

## 3. Charset
* All files must be read, written, and saved using **UTF-8** encoding.
* Do not include a Byte Order Mark (BOM).

## 4. Insert Final Newline
* Always ensure every file ends with a single trailing newline (`\n`).
* Do not leave trailing whitespace on empty lines at the end of files.

## 5. Line Endings (End of Line)
* **Always use LF (`\n`)** as the end-of-line sequence for all files in this repository.
* Do not use CRLF (`\r\n`) line breaks under any circumstances, even when working on Windows environments.

## 6. Repository Configuration Consistency
* The formatting rules defined in `.editorconfig` must be strictly respected across all files.
* Ensure Git is configured to preserve LF line endings (`git config core.autocrlf input` on Linux/macOS or `false` with explicit `.gitattributes`).

## 7. AI Agent Guidelines
* When generating or editing code, verify that generated output adheres to the space-indentation, UTF-8 charset, and LF newline requirements.
* Avoid committing auto-generated configuration files or temporary editor artifacts that violate the structure.

## 8. Business Rules: Expenses and Petty Cash
- **Immutability & Auditing:** It is strictly forbidden to perform *hard deletes* (physical deletion) in the petty cash transaction, expense, or receipt tables; always implement *soft deletes*.
- **State Protection:** If an expense record has an `Approved` or `Reconciled` status, never generate code that allows its amounts or details to be updated (UPDATE) directly.
- **Correction Flow:** Any correction to an already approved transaction must be implemented by creating a new "Reversal" or "Adjustment" record that references the original transaction's UUID, keeping the accounting history intact.
