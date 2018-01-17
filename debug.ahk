; Blender add-ons debugging Autohotkey script
; see https://github.com/joric/io_scene_b3d

^+d:: ; Ctrl+Shift+d
Process, Exist, blender.exe
IF errorlevel=0
{
	Run "C:\Program Files\Blender Foundation\Blender\blender.exe"
	Sleep, 3000
	Send {Esc} ; close splash
}

WinActivate, Blender
Sleep 200
Send +{F4} ; switch to console
Clipboard=import imp,sys; imp.reload(sys.modules['io_scene_b3d'])
Send ^v{Enter}
Clipboard=bpy.ops.object.select_all(); bpy.ops.object.delete()
Send ^v{Enter}
Clipboard=bpy.ops.import_scene.blitz3d_b3d(filepath='test.b3d')
Send ^v{Enter}
Send +{F5} ; switch to 3d view
Send {Home} ; show all
Return

^+f:: ; Ctrl+Shift+f, do something fun, e.g. clear scene:
Send a{Del}{Enter}
Return

