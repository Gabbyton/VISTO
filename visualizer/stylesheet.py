default_stylesheet = [
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "width": "200px",
            "height": "200px",
            "background-color": "#EEF0FB",
            "border-width": "2",
            "border-color": "black",
            "color": "black",
            "text-valign": "center",
            "text-halign": "center",
            "font-size": "60px",
        },
    },
    {
        "selector": "edge",
        "style": {
            "width": 10,
            "opacity": 0.9,
            "font-size": "30px",
            "line-color": "#ACC9D7",
            "target-arrow-color": "#ACC9D7",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "label": "data(label)",
            "arrow-scale": 2,
        },
    },
    {
        "selector": "node[?chosen]",
        "style": {"background-color": "#F5F749", "color": "black"},
    },
    {
        "selector": "node[?linked]",
        "style": {"border-color": "#68FF0A", "border-width": "5px"},
    },
]
