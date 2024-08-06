from visto.connector.base_ontology import BaseOntology


class RefOntology(BaseOntology):

    def __init__(self, base_ontology, ref=None):
        super().__init__(base_ontology, base_ontology=base_ontology, ref=ref)
