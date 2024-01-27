<div style="display: flex;">
  <img src="assets/icons/icon.png" alt="PDF Flow Image" width="40" height="40" style="padding-right: 10px; padding-top: 5px;">
  <h1>PDF Flow</h1>
</div>


This program was created to dynamically analyze scanned PDF files using user defined templates to grab in-document information to use for renaming the files, save to project specific directories, and e-mail files to project specific distribution lists.

## Install Process

**Note:** PDF Flow is currently only compatible with Windows due to hardcoded configuration storage settings. Updating this for use on Linux will be completed soon in a future update.

### Dependencies

Before getting started, make sure you have the following dependencies installed on your system and are available via PATH:

- [Poppler](https://pdf2image.readthedocs.io/en/latest/installation.html) - Used for transforming PDFs to images.
- [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) - The OCR engine for text extraction.


## Installation

### Option 1: Installation via .msi File (Windows)

1. Visit the [PDF Flow website](https://pdfflow.godevservices.com) to download the latest .msi installer for Windows.
2. Run the downloaded .msi file and follow the on-screen instructions to install the program.
3. Once installed, you can launch the program from the Start Menu or desktop shortcut.

### Option 2: Building from Source

If you prefer to build from source you can follow these steps:

1. Clone the GitHub repository:

    ```bash
    git clone https://github.com/bgorman87/PDF-Flow.git
    cd pdf-flow
    ```

2. Create and activate a virtual environment (recommended):

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4. **Note:** On Windows, during processing you may notice brief command windows appearing and disappearing. This is due to the way the `pdf2image` package dependency runs Poppler.

   If you prefer not to see these windows, follow these general steps:

   1. Open `pdf2image.py` in your editor of choice.
   2. Look for any lines that uses `Popen` to execute a command.
   3. Add the following flag at the end of that line: `creationflags=0x08000000`.

   * Here's an example of what the modified line could look like:
     ```python
     proc = Popen(command, env=env, stdout=PIPE, stderr=PIPE, creationflags=0x08000000)
     ```


5. Run PDF Flow:

    ```bash
    python PDF-Flow.py
    ```

## Usage

For usage information/guides please see information located here: [PDF Flow Usage](https://pdfflow.godevservices.com/usage)

## FAQ

<details>
  <summary>Will this be available for Linux</summary>
      A: Currently have updating for cross compatability on my list of things to do. Majority of this was created in Linux so not much to change. Should be available soon. 
</details>

## Contact/Bugs

For any questions/comments/bugs please reachout through e-mail at [brandon@godevservices.com](mailto:brandon@godevservices.com) or directly through github.

## Contribution

Being a new/solo developer I happily welcome any contributions to PDF Flow! Here's how you can contribute:

1. **Fork the Repository**: Click the "Fork" button at the top-right of this repository to create your own copy.

2. **Clone the Repository**: Clone your forked repository to your local machine:

    `git clone https://github.com/your-username/PDF-Flow.git`

    `cd PDF-Flow`

3. **Create a Branch**: Create a new descriptively named branch for your changes:

    `git checkout -b your-descriptive-branch-name`

4. **Make Changes**: Make your desired changes to the codebase.

5. **Commit Changes**: Commit your changes with a descriptive commit message:

    `git commit -m "Add feature XYZ"`

6. **Push to Your Fork**: Push your changes to your fork on GitHub:

    `git push origin your-descriptive-branch-name`

7. **Submit a Pull Request**: Open a pull request from your fork to this repository's `main` branch. Provide a clear and detailed description of your changes.

8. **Review and Collaborate**: Participate in the discussion and make any necessary adjustments based on feedback from maintainers.

