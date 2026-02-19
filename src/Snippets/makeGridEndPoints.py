import numpy as np

def makeGridEndpoints(size, spacing):
    vertices = []
    steps = int(size/spacing)
    for x in range(steps+1):
        vertices += [x*spacing,0]                            # Top vertex for T-B line
        vertices += [x*spacing,-size]                        # Bottom vertex for T-B line
        vertices += [0, -x*spacing]                          # Left vertex for L-R line
        vertices += [size,-x*spacing]                        # Right vertex for L-R line

    "Translating vertices to their real position with numpy arrays "
    translVertices = (np.reshape(vertices,(int(len(vertices)/2),-1)) + np.array([-size/2,size/2])).flatten()
#     vLength = int(len(vertices)/2)
#     return pyglet.graphics.vertex_list(vLength,('v2f',translVertices), ('c4f',colors))
    return translVertices