# VISTO Tutorials

This document provides a step-by-step guide to the most important concepts surrounding the use of the VISTO package and the creation and visualization of "bottoms-up" ontologies. This document is not exhaustive and will be updated regularly as the package continues in its development.

This tutorial will cover the creation of basic ontologies using draw.io. For information about ontologies and the conventions used, please refer to this seminal paper on [PMDCo](https://www.sciencedirect.com/science/article/pii/S0264127523010195)

To learn more about draw.io, please refer to their [website](https://www.drawio.com/)

## Tutorial 1 - Parsing Relationships from draw.io files

The ontologies built for this package relies on the idea of relationship triples, composed of a parent, child and relationship. This is the core operating principle behind the CEMENTO package and its ability to convert draw.io XML files into relationships.

We start by learning how to extract relationship triples.

### Step 1

Download draw.io and install the software to follow along with tutorial. Alternatively, you can use the online version, but be sure to download the files to the appropriate location after each change.

Be sure to clone the [VISTO repository](https://github.com/Gabbyton/VISTO) and install prerequisites:

```{bash}
git clone git@github.com:Gabbyton/VISTO.git
cd VISTO
pip install -r requirements.txt
```

### Step 2

Open draw.io. Click on the rectangle shape and move the created rectangle on the canvas to the desired location.
> **Note**: If you cannot see the shapes panel on the left, click the more shapes button and check the general box on the left of the window that pops up before clicking Apply.

Double-click the rectangle to edit the text inside. Create, name, move, and connect two rectangles to mimic the setup as shown:
![tutorial-1a](https://github.com/Gabbyton/VISTO/blob/master/assets/images/tutorial-1a.png)

To connect rectangles, hover over the perimeter of a rectangle and click on one of the handles and drag towards a handle on another shape.

Double click on the line of the created arrow to edit its caption.
> **Note**: creating a textbox on top of the caption will not work. Please double-click the arrow and create the caption for the package to work properly.

Save the file by going to `File > Save` and choose the `in` folder inside the repository.
> **Note**: you can save the file in any location but you would have to edit the `INPUT_PATH` variables in the tutorial scripts.

### Step 3

On the VISTO package, we’ve included several code examples to get you started on using the underlying CEMENTO package. Run the `tutorial_1.py` script in the `tutorials` folder and inspect the script to see how draw.io files are converted into relationships.

## Tutorial 2: Creating simple ontologies

Creating ontologies follow from the same workflow from Tutorial 1 when drawing draw.io files. We simply add the concepts of hierarchy and templating.

### Step 1

If not already done, please clone the VISTO repository and install its dependencies along with the draw.io software.

### Step 2

Using the same tools as in Tutorial 1, attempt to copy the following image:

![tutorial-2a](https://github.com/Gabbyton/VISTO/blob/master/assets/images/tutorial-2a.png)

#### Few Things to Note

![tutorial-2b](https://github.com/Gabbyton/VISTO/blob/master/assets/images/tutorial-2b.png)

Relationships above the line are between classes of things.
Relationships below the line are between instances of classes

Connecting classes to each other use `rdfs:subClassOf`
Connecting classes to their instances use `rdf:type`

Note the capitalization and the use of prefixes:
`pmd:` means that the term or class belongs to the PMDCo ontology. This is the “convention” we follow. For more information on it, you can refer to this [visual guide](https://miro.com/app/board/uXjVPn5wGiA=/). The formal documentation of terms is found [here](https://materialdigital.github.io/core-ontology/index-en.html#).

In our case, we decided by convention to not use prefixes for instances. If creating a custom class, we at the MDS<sup>3</sup> center use `mds:` Be sure to formally declare your ontology if creating a new prefix, i.e. using aps: will require you to formally declare the APS ontology in the future. Reach out to us at MDS<sup>3</sup> for more information on how or why to do this later.

Relationships also come with their own classes. They follow the same rule with terms. Relationships, by convention, do not have instances, so always add a prefix to them.

> **Note**: The shapes you use should not matter. As long as you are using simple shapes (circles, rectangles, squares, rounded rectangles, clouds, etc.) and not compound shapes (containers, lists, tables, textboxes, etc.) the package should parse them as terms.

Note the use of the underscores after instances, i.e. `sample_`. The underscore indicates to our package that the instance is a variable, which can be renamed in the blueprint (discussed in the next tutorial). This is important because this enables using your draw.io files as templates that can be replaced with actual variable names in the blueprint.

### Step 3

Run the `tutorial_2.py` script. The terminal output of the relationship dataframe should be different. The last column `is_rank` indicates whether the relationship involves a class or two classes.

## Tutorial 3: Creating blueprints

To expedite the process, we have already included some ontologies for various components at the APS. This can be found in the `visto/ontologies` folder. These ontologies are only grouped by folder for convenience. In the package, they are all added to a big list where the package chooses and reads the diagrams.

Now that you have templates, a good question to ask is, how do I fill them up for actual components? In fact, how do I do it for multiple components of the same type? We will demonstrate how to do these actions here.

### Step 1

Start by drawing a draw.io diagram once again with the following content:


![tutorial-3a](https://github.com/Gabbyton/VISTO/blob/master/assets/images/tutorial-3a.png)

Looking closely, the names on the bubbles and boxes have some funny brackets. This is because bubbles by themselves do not mean anything to the VISTO package. We have to link each of the bubbles to an ontology that it is related to. Thus the naming pattern is:

`<New Variable Name> [<ontology file name>|<ontology variable>]`

**New Variable Name** is the actual variable name you want to assign. For example, the FS motor is an actual variable name and it is what we use.

**Ontology file name** is the file name of your source diagram without the file extensions. This tells the package that the bubble you drew is actually represented by the diagram inside that file.

**Ontology variable** is the term inside the diagram that you want your New Variable Name to replace. Based on the ideas in tutorial 2, this is the template that will be “filled-in” with your choice of variable.

Note the use of `~` in the boxes. This is because there is no native way in draw.io or its schema to indicate something is an area that contains other things, rather than just being a term. The choice of symbol is by convention. Avoid using `~` to name things that are not areas.

> **Tip**: to align the area boxes up, please click the following button on the right panel under format as shown in the image:

![tutorial-3b](https://github.com/Gabbyton/VISTO/blob/master/assets/images/tutorial-3b.png)

### Step 3

Make sure to draw the relationships between the bubbles. Notice that there are three relationships use:

| Term | Definition |
| --- | --- |
| Mds:bind | means that the child is grouped by or part of its parent. For example, a motor belongs to a motor stack. In the final diagram, the motor and all of its variables or components will be connected to the stack. |
| Mds:place | denotes that the child is “on top of” the parent physically. For example, within a stack the FSY motor is placed on top of FSX motor. |
| Mds:adopt | signifies that the parent reads from a reference template (discussed in the next tutorial) and chooses the content of the child as the variable whose character it follows. |

Save the file in a convenient location and take note of it for the next step.

### Step 4

Inside visto folder is a `config ini` file. Please modify the paths to a folder of your choice inside your environment. 

`triple_output_path` is the path of the output for saving file triples (pending feature but required)

`file_source_path` is the path of the csv file containing the metadata variable data (will migrate to motor variable linking but currently required)

`temp_path` is the path of the temp folder used by the VISTO server to open your draw.io file (required)

### Step 5

Run the VISTO package server by typing run `app.py` inside the `visto` folder. Copy-paste the URL that is output on the terminal on a browser to see the app.

### Step 6

On the VISTO app, open `File` and select `Import File`. Choose the file containing the blueprint. The first window from the top-left should now be populated with bubbles of the variables with the proper names.

Feel free to drag the window to pan and drag the bubbles to move them. Scroll the mouse up and down to zoom in and out. Click on a variable to inspect its children if it has any.

## Tutorial 4 and more information

Tutorial 4 is currently being created. A video tutorial will also be released for all tutorials in the near future.

Please feel free to contact the developer at [gop2@case.edu](mailto:gop2@case.edu) if you have questions, code reports, or require more information.
