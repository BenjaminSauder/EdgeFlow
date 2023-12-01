# EdgeFlow

This addon adds operators to blender which help when dealing with curved shaped meshes.

Feel free to create issues, file requests etc. but be aware of that I might not find time to work on this as much as I'd probably need to. 

## Installation
Master is for blender 4.0 - adventures are in the Dev branch.

* Get the latest EdgeFlow.zip release in: https://github.com/BenjaminSauder/EdgeFlow/releases
* start Blender and open the user preferences
* switch to the Add-ons tab and click the Install Add-on from file... button at the bottom
* locate the downloaded EdgeFlow.zip file and double-click it
* search for the addon "EdgeFlow"
* activate the addon by ticking the checkbox (hit the Save User Settings button at the bottom if your blender is setup that way)

## Where are these located in blender?

Both can be accessed via the 'Mesh>Edge' and 'Mesh>Vertex' menu, or the corresponding viewport context menus (right-click in edge/vertex mode) or the Shortcut (Ctrl-E / Ctrl-V). 

## Tools

### Set Flow:

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/5397adac-54c4-48c8-9999-e121c85db7d6)

My stab at implementing a set flow operator for blender, which is a popular tool in 3ds max and maya. This adjusts the edgeloop via a spline interpolation such that it respects the flow of the surrounding geometry.
The tool operates orthogonal to the direction of the flow of the edgeloop, indicated by the orange in the image.

##### Mix:
Blend between intial vertex positions and the interpolated result
##### Tension: 
Controls the strengh of offset 
##### Iterations: 
How often the operation will be repeated
##### Min Angle:
Cut off angle of the smoothing. Falls back to a linearely extrapolated position if the angle is beyond threshold. 

In this example the control points for the spline smoothing are around the corner - which creates a nasty bulge. With the min angle one can force the alghorithm to find a better solution.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/a291b7ee-724a-4117-a62b-8c082e5896aa)

##### Blend Mode:
Absolute: Use a number of vertices along the edgeloop control the blend
Factor: Blend length defined by a factor of the edgeloop length 
##### Blend Start:
of vertices from the start of the edgeloop | The partial length from the start of the edgeloop
##### Blend End:
Number of vertices from the end of the edgeloop | The partial length from the end of the edgeloop
##### Blend Curve:
Linear or Smoothstep blend

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/124271b7-c0cf-4772-9b05-f980cd380b45)


### Set Linear:

This makes each selected edge loop a straight line between start and end point. The spacing of all the other points can either be spaced evenly, or projected from the original distances.
The tool operates in the direction of the flow of the edgeloop, indicated by the green in the image.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/f53f5544-a3ea-4afe-aea8-ddb5e792bfbc)

##### Space evenly:
Place the vertices on the loop in regular distances.

### Set Curve:

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/f7e1690d-e852-4dec-bd40-956b470f94bf)

This tool curves each selected edge loop onto a spline which is controled by the first and the last edge of the edgeloop.
The tool operates in the direction of the flow of the edgeloop, indicated by the green in the image.

##### Mix:
Blend between intial vertex positions and the interpolated result
##### Tension: 
Controls the strengh of offset 


### Set Vertex Curve:

This tool works creates a curve based on vertex selections. 
If two vertices are selected, a half circle is constructed between the points
If three vertices are selected, all inbetween points are placed onto a circle which goes through the selected points. Selection order is important, you can think of it as start - middle - end points
If more than three vertices are selected, the tool constructs a spline and projects all points onto it



## How Set Flow works

Back when I first got to see this in action I did quite not understand how it all worked - so I thought i might be well worth adding a quick description to better understand how the underlaying mechanics work.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/c7875b5a-1f8f-407a-a05f-2f0705ac4cf3)


The tool goes over each edge from an edgeloop, and then goes over each vert for this edge. For every vert it searches the points C1-C4 which are used as 'control points' for the spline interpolation - quite similar to how every vector drawing programm works.
So its all depending on the surrounding geometry - which also means if we have multiple neighbouring edgeloops they all influence each other once we start applying this smoothing. Doing the same operation a few times helps to balance it all out and  converges quickly into something stable after a few iterations - so hence the need for such an option.



## Developer Notes

I had to reimplement the edge loop selection from blender because I needed to go from a spaghetti edge selection to sorted edgeloops. While I like that I was able to reproduce blenders selection behaviour I still think I might have overlooked something on how to do it with the regular api - any hints?

I tried different spline interpolation implementations but settled with a hermite interpolation from http://paulbourke.net/miscellaneous/interpolation/ as it has this nice tension variable.
