import spacy
from spacy.symbols import nsubj, VERB
from rich.table import Table
from rich.tree import Tree
import rich


def main():
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(
        "The program sits here until either SIGINT or SIGTERM arrives, at which point shutdown_event.set() triggers and this await returns."
    )
    table = Table("Text", "Root", "Dep", "Head", title="Noun Chunks")
    # Finding a verb with a subject from below — good
    for chunk in doc.noun_chunks:
        table.add_row(
            chunk.text, chunk.root.text, chunk.root.dep_, chunk.root.head.text
        )
    rich.print(table)

    tree = Tree("Noun Chunks")
    for chunk in doc.noun_chunks:
        tree.add(
            f"{chunk.text} (Root: {chunk.root.text}, Dep: {chunk.root.dep_}, Head: {chunk.root.head.text})"
        )
    rich.print(tree)
