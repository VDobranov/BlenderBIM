import ifcopenshell as ios

#f = 'H:\BBIM\Сваи_.ifc'
f = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/2023.08.10_study.ifc'

file = ios.open(f)

plist = file.by_type('IfcPile')
clist = file.by_type('IfcColumn')

def get_coords(p):
    x = ios.util.placement.get_local_placement(p.ObjectPlacement)[:,3][0] * 10000.0
    y = ios.util.placement.get_local_placement(p.ObjectPlacement)[:,3][1] * 100.0
    return x + y

plist.sort(key=get_coords)

i = 1
for p in plist:
    p.Tag = str(i)
    i = i + 1

for c in clist:
    c.Tag = "K-1"

file.write(f)

#print(get_coords(plist[10]))