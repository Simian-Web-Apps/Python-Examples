import os
import shutil

from pypdf import PdfWriter, PdfReader
from simian.gui import Form, component, utils


if __name__ == "__main__":
    from simian.local import Uiformio

    Uiformio("pdf_processor", window_title="PDF Processor", show_refresh=True, debug=True)


def gui_init(meta_data: dict) -> dict:
    # Create the form and load the json builder into it.
    form = Form(from_file=__file__)

    return {
        "form": form,
        "navbar": {"title": "PDF Merger", "subtitle": "<small>Simian app</small>"},
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def gui_close(meta_data):
    # Remove the session folder on app close.
    shutil.rmtree(utils.getSessionFolder(meta_data), ignore_errors=True)


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


def MergeFiles(meta_data, payload):
    # 1 Based indexing in App to zero based in code!

    file_list, _ = utils.getSubmissionData(payload, "pdfSettings")

    merger = PdfWriter()

    for file in file_list:
        input_file = open(file["fullName"], "rb")

        merger.append(fileobj=input_file, pages=(file["firstPage"] - 1, file["lastPage"]))

    # input1 = open("document1.pdf", "rb")
    # input2 = open("document2.pdf", "rb")
    # input3 = open("document3.pdf", "rb")

    # # Add the first 3 pages of input1 document to output

    # # Insert the first page of input2 into the output beginning after the second page
    # merger.merge(position=2, fileobj=input2, pages=(0, 1))

    # # Append entire input3 document to the end of the output document
    # merger.append(input3)

    # Write to an output PDF document
    out_file = os.path.join(utils.getSessionFolder(meta_data), "document-output.pdf")
    output = open(out_file, "wb")
    merger.write(output)

    # Close file descriptors
    merger.close()
    output.close()

    utils.setSubmissionData(payload, "createdPdf", out_file)

    component.ResultFile.upload(
        file_paths=[out_file],
        mime_types=["application/pdf"],
        meta_data=meta_data,
        payload=payload,
        key="createdPdf",
        file_names=["document-output.pdf"],
    )
    return payload
