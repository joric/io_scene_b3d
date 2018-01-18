# io_scene_b3d

Blender Import-Export script for Blitz 3D .b3d files

## Installation

The preferred method to install scripts is `File - User preferences - Add-ons - Install Add-on from File`.
Use archived addon (zip archive containing io_scene_b3d directory), and press 
`Save User Settings` button afterwards.

You can also copy or symlink the io_scene_b3d directory to the Blender user directory, i.e.:
`%APPDATA%\Blender Foundation\Blender\2.79\scripts\addons\io_scene_b3d`.

## Debugging

Every time you change the script it has to be reloaded with `Reload Scripts` (space bar menu or simply press `F8`).

I've also implemented a debug shortcut `Shift+Ctrl+d`, that reset scene, reloads script and then imports a test file.

## TODO

### Import

* Mind that UV mapping, normals and animation are not yet implemented. Working on it!
* Nodes with multiple meshes get converted into a single mesh (preserving brush_id).
Maybe it's better to split those nodes into separate objects.
* Nodes use original quaternion rotation and it affects user interface.
Maybe it's worth to convert it into euler.

### Export

* Exported files sometimes contain animation keys that go outside the animation.
Assimp doesn't import them so I've added an extra frame, just to be safe.
It's better to recalculate the animation using existing keys.
UPDATE: could not reproduce, reverted. Will double check later.

## License

This is all GPL 2.0. Pull requests welcome.

The import script is a heavily rewriten script from Glogow Poland Mariusz Szkaradek.
I've had to rewrite all the chunk reader stuff and all the import stuff, because Blender API
has heavily changed since then.

The export script uses portions (copied almost verbatim, just ported to Blender Import-Export format)
from supertuxcart project by Diego 'GaNDaLDF' Parisi. Since it's all GPL-licensed, he shouldn't mind.

The b3d format documentation (b3dfile_specs.txt) doesn't have a clear license (I assume Public Domain)
but it was hard to find, so I just put it here in the repository as well.

## Alternatives

* [Assimp](http://assimp.sourceforge.net/) - doesn't read .b3d animation in most cases, maybe I have acuired a very particular set of files
* [fragMOTION](http://www.fragmosoft.com/) - works fine most of the time, but it's a terrible nagware and the only suitable export is .smd

## References

* https://github.com/joric/gnome

