"""PDF Merger app."""

import os
import shutil

from pypdf import PdfWriter, PdfReader
from simian.gui import Form, component, utils


def gui_init(meta_data: dict) -> dict:
    # Create the form and load the json builder into it.
    Form.componentInitializer(description=extend_description(mode=meta_data["mode"]))
    form = Form(from_file=__file__)

    return {
        "form": form,
        "navbar": {"title": "PDF Merger", "subtitle": "<small>Simian demo</small>"},
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    Form.eventHandler(MergeFiles=merge_files)
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def gui_close(meta_data):
    # Remove the session folder on app close.
    shutil.rmtree(utils.getSessionFolder(meta_data), ignore_errors=True)


def extend_description(mode):
    """Extend the description based on the run mode."""

    def inner(comp):
        if mode == "deployed":
            comp.content += "<li>Warning: do not upload sensitive information.</li><li>Tip: click the 'Close' button in the top-right corner to close the app AND immediately delete the uploaded and merged files. Remaining files from your session are deleted every 24 hours.</li>"
        else:
            comp.content += "<li>Tip: selected and merged files available in the session are deleted when you close the app."

    return inner


def file_selection_change(meta_data: dict, payload: dict) -> dict:
    """Process file selection change."""
    selected_meta, _ = utils.getSubmissionData(payload, "inputPdFs")
    payload, selected_pdfs = component.File.storeUploadedFiles(meta_data, payload, "inputPdFs")

    file_list, _ = utils.getSubmissionData(payload, "pdfSettings")

    # Delete removed files
    for f in reversed(file_list):
        if f["fullName"] not in selected_pdfs:
            file_list.remove(f)

    ex_files = [f["fullName"] for f in file_list]

    for file, meta in zip(selected_pdfs, selected_meta):
        # Add new files.
        if file not in ex_files:
            pdf_reader = PdfReader(file)
            num_pages = pdf_reader.get_num_pages()
            file_list.append(
                {
                    "pdfName": meta["originalName"],
                    "firstPage": 1,
                    "lastPage": num_pages,
                    "numberPages": num_pages,
                    "fullName": file,
                }
            )
            pdf_reader.close()

    utils.setSubmissionData(payload, "pdfSettings", file_list)

    return payload


def merge_files(meta_data, payload):
    """Merge the selected files."""
    file_list, _ = utils.getSubmissionData(payload, "pdfSettings")

    merger = PdfWriter()

    for file in file_list:
        # Append the selected pages of the PDFs to the PDF writer.
        with open(file["fullName"], "rb") as input_file:
            merger.append(fileobj=input_file, pages=(file["firstPage"] - 1, file["lastPage"]))

    # Write to an output PDF document
    out_file = os.path.join(utils.getSessionFolder(meta_data), "document-output.pdf")
    with open(out_file, "wb") as output:
        merger.write(output)

    # Close file descriptors
    merger.close()

    # Put the merged PDF in the app for the user to download.
    component.ResultFile.upload(
        file_paths=[out_file],
        mime_types=["application/pdf"],
        meta_data=meta_data,
        payload=payload,
        key="createdPdf",
        file_names=["document-output.pdf"],
    )
    return payload
