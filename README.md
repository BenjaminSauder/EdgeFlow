# EdgeFlow

This addon adds two operators to blender which both work on edgeloop selections.

Feel free to create issues, file requests etc. but be aware of that I might not find time to work on this as much as I'd probably need to. 

Anyhow lets start with a brief overview:

#### Set edge flow:

![Set_Flow_Demo](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Flow_Demo.jpg)

  My stab at implementing a set flow operator for blender, which is a popular tool in 3ds max and maya. This adjusts the edgeloop via a spline interpolation such that it respects the flow of the surrounding geometry.

#### Set edge linear:

![Set_Linear_Demo](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Linear_Demo.jpg)

This tool has two modes, the first makes each selected edge loop linear, the later works on edge rings and straightens them and adjusts each edge length.

### A more indepth description of these tools can be found bellow.



## Where are these located in blender?

Both can be accessed via the 'Mesh>Edges' menu, the viewport edge context menu (right-click in edge mode) or the edge menu Shortcut (Ctrl-E). The two commands should be there at the bottom. As mentioned both operate on edge selections - mostly edgeloops.


## Installation
Master is now the 2.8 version! if you need the 2.7 version go to the blender_27 branch.

* Get the latest EdgeFlow.zip release in: https://github.com/BenjaminSauder/EdgeFlow/releases
* start Blender and open the user preferences
* switch to the Add-ons tab and click the Install Add-on from file... button at the bottom
* locate the downloaded EdgeFlow.zip file and double-click it
* search for the addon "EdgeFlow"
* activate the addon by ticking the checkbox (hit the Save User Settings button at the bottom if your blender is setup that way)



## Set edge flow

This operator has three options to play with:

#### Tension: 
Controls the strengh of offset 
#### Iterations: 
How often the operation will be repeated
#### Min Angle:
Cut off angle of the smoothing. Falls back to a linearely extrapolated position if the angle is beyond threshold. 

In this example the control points for the spline smoothing are around the corner - which creates a nasty bulge. With the min angle one can force the alghorithm to find a better solution.
![MIn_Angle_Demo](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Min_Angle_Demo.jpg)


#### How it works

Back when I first got to see this in action I did quite not understand how it all worked - so I thought i might be well worth adding a quick description to better understand how the underlaying mechanics work.

![Shema](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Shema.jpg)

The tool goes over each edge from an edgeloop, and then goes over each vert for this edge. For every vert it searches the points C1-C4 which are used as 'control points' for the spline interpolation - quite similar to how every vector drawing programm works.
So its all depending on the surrounding geometry - which also means if we have multiple neighbouring edgeloops they all influence each other once we start applying this smoothing. Doing the same operation a few times helps to balance it all out and  converges quickly into something stable after a few iterations - so hence the need for such an option.


## Set edge linear

As already mentioned this is basically two tools in one. The first case is if you just select regular edge loops. After running the operator each loop should be linear from start to end point. The spacing of all the other points can either be spaced evenly, or projected from the original distances.

![Set_Linear_Demo2](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Linear_Demo2.jpg)


The second case is if the selection consits only of single edges - most common in edge rings. Once applied it straightens the edges to the next connected vert and makes sure the distance is even everywhere. This is handy for tweaking control loops for SubD Modelling. Mostly inspired by an older 3ds maxscript from Christoph Kubisch: http://luxinia.de/index.php/ArtTools/3dsmax

![Set_Linear_Demo3](https://github.com/BenjaminSauder/EdgeFlow/blob/master/docs/Set_Linear_Demo3.jpg)


## Developer Notes

I had to reimplement the edge loop selection from blender because I needed to go from a spaghetti edge selection to sorted edgeloops. While I like that I was able to reproduce blenders selection behaviour I still think I might have overlooked something on how to do it with the regular api - any hints?

I tried different spline interpolation implementations but settled with a hermite interpolation from http://paulbourke.net/miscellaneous/interpolation/ as it has this nice tension variable.
