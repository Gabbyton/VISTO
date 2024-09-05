from cemento.draw_io.read_diagram import ReadDiagram

INPUT_PATH = "../in/tutorial_2.drawio"

if __name__ == "__main__":
    # to read a diagram, create a ReadDiagram object and specify the path
    diagram = ReadDiagram(INPUT_PATH)
    # the relationship table parsed from the diagram is a pandas dataframe
    relationships_df = diagram.get_relationships()
    print(relationships_df)