# io_scene_b3d

Blender Import-Export script for Blitz 3D .b3d files

## Installation

* Userspace method: click "File" - "User Preferences" - "Add-ons" - "Install Add-on from File".
The add-on zip file should contain io_scene_b3d directory, including the directory itself.
* Alternative method: copy or symlink the io_scene_b3d directory to blender user directory, e.g. to
%APPDATA%\Blender Foundation\Blender\2.79\scripts\addons\io_scene_b3d.
* Search and enable add-on in "User Preferences" - "Add-ons". Click "Save User Settings" afterwards.

## Debugging

* Userspace method: every time you make a change the script has to be reloaded using Reload Scripts command (F8).
* Alternative method: my shortcut, Shift+Ctrl+D in Object Mode. It resets scene, reloads the script and imports test file.
* Somewhat simpler method (Windows only), an autohotkey script I wrote (see the [autohotkey](https://github.com/joric/io_scene_b3d/tree/autohotkey) branch).

## TODO

### Import

* Mind that animation is not yet implemented. Working on it!
* Nodes use original quaternion rotation that affects user interface.
Maybe convert them into euler angles.
* Sometimes objects appear joined together in a single mesh (an attempt on hardware instancing, I guess).
I'm splitting objects with multiple meshes into a separate objects but I can't effectively
split large meshes into separate objects. Probably solvable with point cloud matching
(considering that objects also can overlap).

### Export

* Exported files (script by Diego 'GaNDaLDF' Parisi) sometimes contain animation keys
that go outside the animation. Assimp doesn't import them so I've added an extra frame, just to be safe.
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

* [Assimp](http://assimp.sourceforge.net/) - doesn't read .b3d animation in most cases, maybe I have acquired a very particular set of files
* [fragMOTION](http://www.fragmosoft.com/) - works fine most of the time, but it's a terrible nagware and the only suitable export is .smd

## References

* https://github.com/joric/gnome

