import pandas as pd
import networkx as nx

if __name__ == "__main__":
    rels_df = pd.read_excel("/Users/gabriel/dev/aps/onto-connector/out/E-hutch.xlsx")
    ex_graph = nx.DiGraph()
    for _, row in rels_df.iterrows():
        parent, child, rel = row['parent'], row['child'], row['rel']
        ex_graph.add_edge(parent, child, rel=rel)

    placements = [(parent,child) for parent, child, data in ex_graph.edges(data=True) if data['rel'] == "mds:place"]
    chain_graphs = nx.DiGraph(placements)

    subgraphs = [
        ex_graph.subgraph(c).copy() for c in nx.weakly_connected_components(chain_graphs)
    ]
    for subgraph in subgraphs:
        print(list(nx.dfs_edges(subgraph)))
        print()

    for parent, child, in placements:
        pos_desc = set(nx.descendants_at_distance(ex_graph, "pmd:Coordinates", 2))
        parent_desc = nx.descendants(ex_graph, parent)
        child_desc = nx.descendants(ex_graph, child)

        parent_vars = pos_desc & parent_desc
        child_vars = pos_desc & child_desc