import ifcopenshell as ios
import ifcpatch

f = 'H:\BBIM\Сваи.ifc'
f2 = 'H:\BBIM\Сваи_.ifc'

output = ifcpatch.execute({
    "input": f,
    "file": ios.open(f),
    "recipe": "ConvertLengthUnit",
    "arguments": ["MILLIMETERS"],
})

ifcpatch.write(output, f)

#alist = file.by_type('IFCTEXTLITERALWITHEXTENT')
#print(alist[0].get_info())

#for a in alist:
#    a.Literal = "{{Tag}}"

#file.write(f)