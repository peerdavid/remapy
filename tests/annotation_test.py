import json
from pathlib import Path

from model.render import pdf

INPUT_BASE_PATH = Path("testcases/annotation/")
OUTPUT_BASE_PATH = Path("testcases/out/")

OUTPUT_BASE_PATH.mkdir(parents=True, exist_ok=True)


def get_pages(rm_files_path):
    content_file = rm_files_path.with_suffix(".content")
    with open(content_file, "r") as f:
        content = json.load(f)
        pages = content["pages"]

    return pages


def render(id, name):
    print()
    print("Rendering " + name + ".....")
    path_original_pdf = INPUT_BASE_PATH / id / f"{id}.pdf"
    rm_files_path = INPUT_BASE_PATH / id / id
    path_highlighter = INPUT_BASE_PATH / f"{id}.highlights"
    pages = get_pages(rm_files_path)
    path_annotated_pdf = OUTPUT_BASE_PATH / f"{name}_annotated.pdf"
    path_oap_pdf = OUTPUT_BASE_PATH / f"{name}_oap.pdf"

    pdf(
        rm_files_path,
        path_highlighter,
        pages,
        path_original_pdf,
        path_annotated_pdf,
        path_oap_pdf,
    )


render("31a5899b-c3a8-49f7-b35a-8adf07c8f16c", "top_left")
render("f8384c9a-1b60-4bbc-9c41-31e5045069f5", "bottom_right")
render("2638d92e-9b68-40c2-993e-fbf96a2ff383", "left")
render("76fe614e-8c08-4e19-8ab3-d58e5d711737", "top")
render("6d02f648-7dfd-4668-b912-757d320e9d83", "landscape")
render("47afa111-4b5d-490d-9e66-5096d7357497", "landscape_bottom_right")
render("0b98f998-fb84-465b-8d0b-229c61c8f07b", "landscape_top_left")
