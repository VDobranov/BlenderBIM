import bpy
import ifcopenshell as ios

ifc = ios.file()

path = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/welded_profile.ifc'
# ifc.write(path)
bpy.ops.bim.unload_project()
bpy.ops.bim.load_project(filepath=path)

print(f"\n{path}")