import ifcopenshell as ios

#f = 'H:\BBIM\Сваи.ifc'
f = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/2023.08.10_study.ifc'

file = ios.open(f)

alist = file.by_type('IFCTEXTLITERALWITHEXTENT')
print(alist[0].get_info())

for a in alist:
    a.Literal = "{{Tag}}"

file.write(f)