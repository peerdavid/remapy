import os

from model.render import notebook

INPUT_BASE_PATH = "./testcases/notebook/"
OUTPUT_BASE_PATH = "./testcases/out/"

if not os.path.exists(OUTPUT_BASE_PATH):
    os.makedirs(OUTPUT_BASE_PATH)


def render(id, name, is_landscape):
    print()
    print("Rendering " + name + ".....")
    notebook(INPUT_BASE_PATH + id + "/", id,
             OUTPUT_BASE_PATH + name + "_annotated.pdf", is_landscape)


render("0ee49335-1f4f-42a2-a1c8-d46e3a158962", "landscape_notebook", True)
render("f7f2364e-9942-4076-ae91-768fd18999d5", "portrait_notebook", False)
