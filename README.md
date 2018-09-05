# EdgeFlow

This addon adds two operators to blender which both work on edgeloop selections.

#### Set edge flow:

![Set_Flow_Demo](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Flow_Demo.jpg)

  My stab at implementing a set flow operator for blender, which is a popular tool in 3ds max and maya. This adjusts the edgeloop    via a spline interpolation such that it respects the flow of the surrounding geometry.

#### Set edge linear:

![Set_Linear_Demo](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Linear_Demo.jpg)

  If the edgeloop length is longer than one, makes each selected edge loop linear.
If the selection is only made up of unconnected edges (think of an edge ring here) adjusts the length of each edge.


Both can be accessed via the 'Mesh>Edges' Menu or the Edge Menu Shortcut (Ctrl-E). The two commands should be there at the bottom.


### Installation
* grab the most recent .zip from the depoly folder
* start Blender and open the user preferences
* switch to the Add-ons tab and click the Install Add-on from file... button at the bottom
* locate the downloaded EdgeFlow.zip file and double-click it
* activate the addon by ticking the checkbox and hit the Save User Settings button at the bottom


## Set edge flow

This operator has three options to play with:

#### Tension: 
controls the strengh of offset 
#### Iterations: 
how often the operation will be repeated
#### Min Angle:
cut off angle of the smoothing. Falls back to a linear extrapolated position if the angle is beyond threshold. See example bellow.

![MIn_Angle_Demo](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Min_Angle_Demo.jpg)


#### How it works

Back when I first got to see this in action I did quite not understand how it all worked - so I thought i might be well worth adding a quick description to better understand how the underlaying mechanics work.

![Shema](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Shema.jpg)

The tool goes over each edge from an edgeloop, and then goes over each vert for this edge. For every vert it searches the points C1-C4 which are used as 'control points' for the spline interpolation - quite similar to how every vector drawing programm works.
So its all depending on the surrounding geometry - which also means if we have multiple neighbouring edgeloops they all influence each other once we start applying this smoothing. Doing the same operation a few times helps to balance it all out and  converges quickly into something stable after a few iterations - so hence the need for such an option.


## Set edge linear

As already mentioned this is basically two tools in one. The first case is if you just select regular edge loops

![Set_Linear_Demo2](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Linear_Demo2.jpg)


The second case is if the selection consits only of single edges - most common in edge rings. Once applied it straightens the edges to the next connected vert and makes sure the distance is even everywhere. This is handy for tweaking control loops for SubD Modelling.

![Set_Linear_Demo3](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Linear_Demo3.jpg)

