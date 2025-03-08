# EdgeFlow

This addon adds operators to blender which help when dealing with curved shaped meshes.

Feel free to create issues, file requests etc. but be aware of that I might not find time to work on this as much as I'd probably need to. 

## Installation
Master is stable - adventures are in the Dev branch.

The addon should work from blender 3.5+ and also work in the current blender release.

* Get the latest EdgeFlow.zip release in: https://github.com/BenjaminSauder/EdgeFlow/releases
* start Blender and open the user preferences
* switch to the Add-ons tab and click the 'Install...' button
* locate the downloaded EdgeFlow.zip file and double-click it to install
* search for the addon "EdgeFlow"
* activate the addon by ticking the checkbox (hit the Save User Settings button at the bottom if your blender is setup that way)

#### Where are these located in blender?

The operators can be accessed via the 3D View in the Mesh>Edge and Mesh>Vertex menu, the corresponding   
rightclick viewport context menus or the default shortcut Ctrl-E / Ctrl-V. 

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/e29dcb97-e9fa-47b2-a789-3a800a33b35a)

## Tools

### Set Flow:

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/5397adac-54c4-48c8-9999-e121c85db7d6)

My stab at implementing a set flow operator for blender, which is a popular tool in many 3d applications. This adjusts the edgeloop via a spline interpolation such that it respects the flow of the surrounding geometry.
The tool operates orthogonal to the direction of the flow of the edgeloop, indicated by the orange in the image.

**Mix:** Blend between intial vertex positions and the interpolated result.  
**Tension:** Controls the strengh of offset.  
**Iterations:** How often the operation will be repeated.  
**Min Angle:** Cut off angle of the smoothing. Falls back to a linearely extrapolated position if the angle is beyond threshold.  

In this example the control points for the spline smoothing are around the corner - which creates a nasty bulge. With the min angle one can force the alghorithm to find a better solution.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/778a2e59-435d-4338-b2ff-40fc2c444d82)


**Blend Mode:**   
- Absolute: Use a number of vertices along the edgeloop to control the blend length.  
- Factor: Blend length defined by a factor of the length from the edgeloop. 
     
**Blend Start:** Number of vertices from the start of the edgeloop | The partial length from the start of the edgeloop.  
**Blend End:** Number of vertices from the end of the edgeloop | The partial length from the end of the edgeloop.  
**Blend Curve:** Linear or Smoothstep blend of the values along the edgeloop.

Notice how the shape changes from straight to curved at the right image. This obviously only works for edgeloops which are not cyclic.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/fd584d3f-f232-4351-a251-1863c0d5a4e3)


### Set Linear:

This makes each selected edge loop a straight line between start and end point. The spacing of all the other points can either be spaced evenly, or projected from the original distances.
The tool operates in the direction of the flow of the edgeloop, indicated by the green in the image.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/f53f5544-a3ea-4afe-aea8-ddb5e792bfbc)

**Space evenly:** Place the vertices on the loop in regular distances.


### Set Curve:

This tool curves each selected edge loop onto a spline which is controled by the first and the last edge of the edgeloop.
The tool operates in the direction of the flow of the edgeloop, indicated by the green in the image.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/f7e1690d-e852-4dec-bd40-956b470f94bf)


**Mix:** Blend between intial vertex positions and the interpolated result.     
**Tension:** Controls the strengh of offset.     
**Use Rail:** Customize the interpolation by using the first and last edge of the edgeloop to control the curvature.     
**Rail Mode:** Switch rail mode between using absolute units or a factor of the length of the edge.     
**Rail Start:** Choose how long the rail is at the start.     
**Rail End:** Choose how long the rail is at the end.     

   

### Set Vertex Curve:

This tool moves vertices to a curve based on vertex selections. The picking order of the selected vertices defines the outcome of the tool. 
So it's very important to select in the correct order.

- **2 vertices are selected:** a half circle is constructed between the points.  
- **3 vertices are selected:** all inbetween points are placed onto a circle which goes through the selected points. You can think of it as start - middle - end points in the selection.
- **4 or more vertices are selected:** the tool constructs a spline and projects all points onto it.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/26a48c27-a5da-4a8a-b42f-55e700d03b1a)


**Tension:** Controls the strengh of offset   
**Use Topology Distance:** Force the path search to ignore edge lenghts, so only topological distance is used to find the inbetween vertices.   
**Flip Half Circle:** (only for 2 vertices) Flip the direction of the half circle.  
**Rotate Half Circle:** (only for 2 vertices) Rotate the half circle orthogonal to the intial orientation.     
**Space evenly:** (only for 3 or more vertices) Place the vertices in even distances.       

## How Set Flow works

Back when I first got to see this in action I did quite not understand how it all worked - so I thought it might be well worth adding a quick description to better understand how the underlaying mechanics work.

![grafik](https://github.com/BenjaminSauder/EdgeFlow/assets/13512160/c7875b5a-1f8f-407a-a05f-2f0705ac4cf3)

The tool goes over each edge from an edgeloop, and then goes over each vert for this edge. For every vert it searches the points C1-C4 which are used as 'control points' for the spline interpolation - quite similar to how every vector drawing programm works.
So its all depending on the surrounding geometry - which also means if we have multiple neighbouring edgeloops they all influence each other once we start applying this smoothing. Doing the same operation a few times helps to balance it all out and  converges quickly into something stable after a few iterations - so hence the need for such an option.

# Credits
Maintainer:
Benjamin Sauder

Additional contributions:

- IngoClemens
- ora-0

## Developer Notes

I had to reimplement the edge loop selection from blender because I needed to go from a spaghetti edge selection to sorted edgeloops. While I like that I was able to reproduce blenders selection behaviour I still think I might have overlooked something on how to do it with the regular api - any hints?

I tried different spline interpolation implementations but settled with a hermite interpolation from http://paulbourke.net/miscellaneous/interpolation/ as it has this nice tension variable.
